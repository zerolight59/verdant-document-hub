from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models import AccessLevel

from .common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = None
    lifecycle_template_id: int | None = None


class ProjectOut(ORMModel):
    id: int
    name: str
    description: str | None
    owner_id: int
    lifecycle_template_id: int | None
    created_at: datetime


class MemberCreate(BaseModel):
    employee_id: int
    access_level: AccessLevel = AccessLevel.VIEW


class StageCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    position: int = Field(ge=1)


class RequirementCreate(BaseModel):
    stage_id: int
    document_type_name: str = Field(min_length=1, max_length=180)
    title: str = Field(min_length=1, max_length=220)
    description: str | None = None
    responsible_employee_id: int | None = None
    reviewer_employee_id: int | None = None
    due_date: date | None = None


class RequirementAssign(BaseModel):
    responsible_employee_id: int | None = None
    reviewer_employee_id: int | None = None


class DocumentPermissionIn(BaseModel):
    employee_id: int
    access_level: AccessLevel
