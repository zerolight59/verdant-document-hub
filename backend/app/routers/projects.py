from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..db import get_db
from ..models import AccessLevel, Document, DocumentPermission, DocumentRequirement, DocumentReview, DocumentType, DocumentVersion, Employee, LifecycleTemplate, LifecycleTemplateStage, Project, ProjectMember, ProjectStage
from ..permissions import require_project_access, require_project_owner, require_requirement_access
from ..schemas import DocumentPermissionIn, MemberCreate, ProjectCreate, ProjectOut, RequirementAssign, RequirementCreate, StageCreate
from ..security import get_current_employee

router = APIRouter(prefix="/projects", tags=["projects"])


def validate_assignees(db: Session, project_id: int, employee_ids: list[int | None]) -> None:
    project = db.get(Project, project_id)
    for employee_id in {item for item in employee_ids if item is not None}:
        if employee_id == project.owner_id:
            continue
        membership = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.employee_id == employee_id))
        if not membership:
            raise HTTPException(status_code=400, detail="Responsible employees and reviewers must be project members")

def employee_json(employee: Employee | None):
    if not employee:
        return None
    return {"id": employee.id, "employee_code": employee.employee_code, "name": employee.name, "job_title": employee.job_title}


@router.get("", response_model=list[ProjectOut])
def list_projects(employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    member_projects = select(ProjectMember.project_id).where(ProjectMember.employee_id == employee.id)
    query = select(Project).where(Project.archived_at.is_(None))
    if not employee.is_admin:
        query = query.where((Project.owner_id == employee.id) | (Project.id.in_(member_projects)))
    return db.scalars(query.order_by(Project.created_at.desc())).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    if db.scalar(select(Project).where(Project.name == payload.name)):
        raise HTTPException(status_code=409, detail="A project with this name already exists")
    template = db.get(LifecycleTemplate, payload.lifecycle_template_id) if payload.lifecycle_template_id else None
    if payload.lifecycle_template_id and not template:
        raise HTTPException(status_code=404, detail="Lifecycle template not found")
    project = Project(name=payload.name, description=payload.description, owner_id=employee.id, lifecycle_template_id=payload.lifecycle_template_id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, employee_id=employee.id, access_level=AccessLevel.MANAGE, added_by_id=employee.id))
    if template:
        for item in db.scalars(select(LifecycleTemplateStage).where(LifecycleTemplateStage.template_id == template.id).order_by(LifecycleTemplateStage.position)).all():
            db.add(ProjectStage(project_id=project.id, template_stage_id=item.id, name=item.name, position=item.position))
    write_audit(db, employee.id, "PROJECT_CREATED", "project", project.id, {"name": project.name})
    db.commit()
    db.refresh(project)
    return project


@router.get("/templates")
def list_templates(_: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    templates = db.scalars(select(LifecycleTemplate).order_by(LifecycleTemplate.name)).all()
    return [{"id": item.id, "name": item.name, "description": item.description, "stages": [{"id": stage.id, "name": stage.name, "position": stage.position} for stage in db.scalars(select(LifecycleTemplateStage).where(LifecycleTemplateStage.template_id == item.id).order_by(LifecycleTemplateStage.position)).all()]} for item in templates]


@router.get("/{project_id}/dashboard")
def project_dashboard(project_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    project = require_project_access(db, project_id, employee)
    stages = db.scalars(select(ProjectStage).where(ProjectStage.project_id == project_id).order_by(ProjectStage.position)).all()
    members = db.execute(select(ProjectMember, Employee).join(Employee, Employee.id == ProjectMember.employee_id).where(ProjectMember.project_id == project_id).order_by(Employee.name)).all()
    requirements = db.scalars(select(DocumentRequirement).where(DocumentRequirement.project_id == project_id, DocumentRequirement.archived_at.is_(None)).order_by(DocumentRequirement.created_at)).all()
    rows = []
    for requirement in requirements:
        document = db.scalar(select(Document).where(Document.requirement_id == requirement.id))
        version = db.scalar(select(DocumentVersion).where(DocumentVersion.document_id == document.id).order_by(DocumentVersion.version_number.desc())) if document else None
        review = db.scalar(select(DocumentReview).where(DocumentReview.document_version_id == version.id)) if version else None
        rows.append({"id": requirement.id, "title": requirement.title, "description": requirement.description, "stage_id": requirement.stage_id, "document_type_id": requirement.document_type_id, "document_type": db.get(DocumentType, requirement.document_type_id).name, "status": requirement.status.value, "due_date": requirement.due_date, "responsible": employee_json(db.get(Employee, requirement.responsible_employee_id)) if requirement.responsible_employee_id else None, "reviewer": employee_json(db.get(Employee, requirement.reviewer_employee_id)) if requirement.reviewer_employee_id else None, "document_id": document.id if document else None, "current_version": None if not version else {"id": version.id, "version_number": version.version_number, "file_name": version.file_name, "mime_type": version.mime_type, "file_size": version.file_size, "change_summary": version.change_summary, "created_at": version.created_at, "submitted_at": version.submitted_at, "view_url": f"/api/documents/files/project/{version.id}", "review": None if not review else {"id": review.id, "decision": review.decision.value, "comment": review.comment, "decided_at": review.decided_at}}})
    return {"project": {"id": project.id, "name": project.name, "description": project.description, "owner": employee_json(db.get(Employee, project.owner_id)), "created_at": project.created_at}, "stages": [{"id": s.id, "name": s.name, "position": s.position} for s in stages], "members": [{"id": m.id, "employee": employee_json(e), "access_level": m.access_level.value} for m, e in members], "requirements": rows, "progress": {"total": len(requirements), "approved": sum(r.status.value == "APPROVED" for r in requirements)}}


@router.post("/{project_id}/members", status_code=status.HTTP_201_CREATED)
def add_member(project_id: int, payload: MemberCreate, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    require_project_owner(db, project_id, employee)
    target = db.get(Employee, payload.employee_id)
    if not target or not target.is_active:
        raise HTTPException(status_code=404, detail="Employee not found")
    member = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.employee_id == payload.employee_id))
    if member:
        member.access_level = payload.access_level
    else:
        db.add(ProjectMember(project_id=project_id, employee_id=payload.employee_id, access_level=payload.access_level, added_by_id=employee.id))
    write_audit(db, employee.id, "PROJECT_MEMBER_SET", "project", project_id, {"employee_id": payload.employee_id, "access_level": payload.access_level.value})
    db.commit()
    return {"message": "Project member saved"}


@router.post("/{project_id}/stages", status_code=status.HTTP_201_CREATED)
def add_stage(project_id: int, payload: StageCreate, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    require_project_owner(db, project_id, employee)
    stage = ProjectStage(project_id=project_id, name=payload.name, position=payload.position)
    db.add(stage)
    write_audit(db, employee.id, "PROJECT_STAGE_CREATED", "project", project_id, {"name": payload.name, "position": payload.position})
    db.commit()
    db.refresh(stage)
    return {"id": stage.id, "name": stage.name, "position": stage.position}


@router.post("/{project_id}/requirements", status_code=status.HTTP_201_CREATED)
def add_requirement(project_id: int, payload: RequirementCreate, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    require_project_owner(db, project_id, employee)
    stage = db.get(ProjectStage, payload.stage_id)
    if not stage or stage.project_id != project_id:
        raise HTTPException(status_code=400, detail="Stage does not belong to this project")
    validate_assignees(db, project_id, [payload.responsible_employee_id, payload.reviewer_employee_id])
    if payload.responsible_employee_id and payload.responsible_employee_id == payload.reviewer_employee_id:
        raise HTTPException(status_code=400, detail="Responsible employee and reviewer must be different")
    document_type = db.scalar(select(DocumentType).where(DocumentType.project_id == project_id, DocumentType.name == payload.document_type_name))
    if not document_type:
        document_type = DocumentType(project_id=project_id, name=payload.document_type_name, created_by_id=employee.id)
        db.add(document_type)
        db.flush()
    requirement = DocumentRequirement(project_id=project_id, stage_id=payload.stage_id, document_type_id=document_type.id, title=payload.title, description=payload.description, responsible_employee_id=payload.responsible_employee_id, reviewer_employee_id=payload.reviewer_employee_id, due_date=payload.due_date)
    db.add(requirement)
    db.flush()
    write_audit(db, employee.id, "DOCUMENT_REQUIREMENT_CREATED", "document_requirement", requirement.id, {"project_id": project_id, "title": requirement.title})
    db.commit()
    return {"id": requirement.id, "title": requirement.title, "status": requirement.status.value}


@router.patch("/requirements/{requirement_id}/assign")
def assign_requirement(requirement_id: int, payload: RequirementAssign, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    requirement = require_requirement_access(db, requirement_id, employee)
    require_project_owner(db, requirement.project_id, employee)
    validate_assignees(db, requirement.project_id, [payload.responsible_employee_id, payload.reviewer_employee_id])
    if payload.responsible_employee_id and payload.responsible_employee_id == payload.reviewer_employee_id:
        raise HTTPException(status_code=400, detail="Responsible employee and reviewer must be different")
    requirement.responsible_employee_id = payload.responsible_employee_id
    requirement.reviewer_employee_id = payload.reviewer_employee_id
    write_audit(db, employee.id, "DOCUMENT_ASSIGNMENT_CHANGED", "document_requirement", requirement.id, payload.model_dump())
    db.commit()
    return {"message": "Document responsibility and reviewer saved"}


@router.put("/requirements/{requirement_id}/permissions")
def set_document_permission(requirement_id: int, payload: DocumentPermissionIn, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    requirement = require_requirement_access(db, requirement_id, employee)
    require_project_owner(db, requirement.project_id, employee)
    permission = db.scalar(select(DocumentPermission).where(DocumentPermission.requirement_id == requirement_id, DocumentPermission.employee_id == payload.employee_id))
    if permission:
        permission.access_level = payload.access_level
    else:
        db.add(DocumentPermission(requirement_id=requirement_id, employee_id=payload.employee_id, access_level=payload.access_level, granted_by_id=employee.id))
    write_audit(db, employee.id, "DOCUMENT_PERMISSION_SET", "document_requirement", requirement.id, {"employee_id": payload.employee_id, "access_level": payload.access_level.value})
    db.commit()
    return {"message": "Document permission saved"}



