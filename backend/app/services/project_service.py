from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employee, Project, ProjectMember


def validate_assignees(db: Session, project_id: int, employee_ids: list[int | None]) -> None:
    """Require responsible employees and reviewers to belong to the project."""

    project = db.get(Project, project_id)
    for employee_id in {item for item in employee_ids if item is not None}:
        target = db.get(Employee, employee_id)
        if not target or not target.is_active:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee_id == project.owner_id:
            continue
        membership = db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.employee_id == employee_id,
            )
        )
        if not membership:
            raise HTTPException(
                status_code=400,
                detail="Responsible employees and reviewers must be project members",
            )


def employee_json(employee: Employee | None) -> dict[str, Any] | None:
    if not employee:
        return None
    return {
        "id": employee.id,
        "employee_code": employee.employee_code,
        "name": employee.name,
        "job_title": employee.job_title,
    }
