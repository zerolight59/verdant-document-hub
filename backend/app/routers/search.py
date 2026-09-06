from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_employee
from app.models import (
    AuditLog,
    DocumentRequirement,
    DocumentType,
    Employee,
    Project,
    ProjectMember,
    ResearchCategory,
    ResearchDocument,
)
from app.services.permission_service import require_project_access

router = APIRouter(tags=["search and audit"])


@router.get("/search")
def search(
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(min_length=1, max_length=200),
) -> list[dict]:
    pattern = f"%{q.strip()}%"
    project_ids = select(ProjectMember.project_id).where(ProjectMember.employee_id == employee.id)
    project_query = (
        select(DocumentRequirement, Project, DocumentType)
        .join(Project, Project.id == DocumentRequirement.project_id)
        .join(DocumentType, DocumentType.id == DocumentRequirement.document_type_id)
        .where(
            DocumentRequirement.archived_at.is_(None),
            or_(
                DocumentRequirement.title.ilike(pattern),
                DocumentRequirement.description.ilike(pattern),
                DocumentType.name.ilike(pattern),
            ),
        )
    )
    if not employee.is_admin:
        project_query = project_query.where(
            (Project.owner_id == employee.id) | (Project.id.in_(project_ids))
        )

    project_results = [
        {
            "kind": "project_document",
            "id": requirement.id,
            "title": requirement.title,
            "context": project.name,
            "status": requirement.status.value,
            "project_id": project.id,
        }
        for requirement, project, _ in db.execute(project_query.limit(50)).all()
    ]

    research_query = (
        select(ResearchDocument, ResearchCategory)
        .join(ResearchCategory, ResearchCategory.id == ResearchDocument.category_id)
        .where(
            ResearchDocument.archived_at.is_(None),
            or_(
                ResearchDocument.name.ilike(pattern),
                ResearchDocument.description.ilike(pattern),
                ResearchCategory.name.ilike(pattern),
            ),
        )
        .limit(50)
    )
    research_results = [
        {
            "kind": "research_document",
            "id": document.id,
            "title": document.name,
            "context": category.name,
            "status": None,
        }
        for document, category in db.execute(research_query).all()
    ]
    return project_results + research_results


@router.get("/audit")
def audit_log(
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    project_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    if project_id is not None:
        require_project_access(db, project_id, employee)
    elif not employee.is_admin:
        return []

    query = (
        select(AuditLog, Employee)
        .outerjoin(Employee, Employee.id == AuditLog.actor_employee_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    if project_id is not None:
        query = query.where(AuditLog.project_id == project_id)

    return [
        {
            "id": item.id,
            "actor": actor.name if actor else "System",
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "project_id": item.project_id,
            "details": item.details,
            "created_at": item.created_at,
        }
        for item, actor in db.execute(query).all()
    ]
