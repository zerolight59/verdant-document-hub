from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AccessLevel, DocumentPermission, DocumentRequirement, Employee, Project, ProjectMember


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project or project.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def require_project_access(db: Session, project_id: int, employee: Employee) -> Project:
    project = get_project_or_404(db, project_id)
    if project.owner_id == employee.id or employee.is_admin:
        return project
    member = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.employee_id == employee.id))
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this project")
    return project


def require_project_owner(db: Session, project_id: int, employee: Employee) -> Project:
    project = get_project_or_404(db, project_id)
    if project.owner_id != employee.id and not employee.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the project owner can do this")
    return project


def require_requirement_access(db: Session, requirement_id: int, employee: Employee, allowed: set[AccessLevel] | None = None) -> DocumentRequirement:
    requirement = db.get(DocumentRequirement, requirement_id)
    if not requirement or requirement.archived_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document requirement not found")
    project = get_project_or_404(db, requirement.project_id)
    if project.owner_id == employee.id or employee.is_admin:
        return requirement
    member = db.scalar(select(ProjectMember).where(ProjectMember.project_id == project.id, ProjectMember.employee_id == employee.id))
    permission = db.scalar(select(DocumentPermission).where(DocumentPermission.requirement_id == requirement_id, DocumentPermission.employee_id == employee.id))
    if allowed is None:
        if member or permission:
            return requirement
    else:
        if employee.id == requirement.responsible_employee_id and AccessLevel.EDIT in allowed:
            return requirement
        if employee.id == requirement.reviewer_employee_id and AccessLevel.REVIEW in allowed:
            return requirement
        if member and member.access_level in allowed:
            return requirement
        if permission and permission.access_level in allowed:
            return requirement
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have the required document permission")
