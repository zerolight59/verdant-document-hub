from typing import Any

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .common import Base, CreatedAtMixin


class Employee(CreatedAtMixin, Base):
    """Verdant-owned employee identity and authorization record.

    ``profile_data`` is reserved for company-specific employee attributes during
    the MySQL-to-PostgreSQL migration. Core authorization fields remain normal
    columns so they can be indexed and validated.
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    job_title: Mapped[str] = mapped_column(String(120), default="Employee")
    department: Mapped[str | None] = mapped_column(String(120), index=True)
    profile_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
