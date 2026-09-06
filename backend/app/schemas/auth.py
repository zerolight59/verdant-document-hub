from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .common import ORMModel


class LoginRequest(BaseModel):
    employee_code: str = Field(
        min_length=1,
        max_length=100,
        description="Employee code or username",
    )
    password: str = Field(min_length=1, max_length=255)


class EmployeeOut(ORMModel):
    id: int
    employee_code: str
    username: str | None
    name: str
    email: str
    job_title: str
    department: str | None
    profile_data: dict[str, Any]
    is_admin: bool
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee: EmployeeOut
