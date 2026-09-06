from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .common import Base, CreatedAtMixin
from .enums import AccessLevel, enum_type


class LifecycleTemplate(Base):
    __tablename__ = "lifecycle_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[str | None] = mapped_column(Text)


class LifecycleTemplateStage(Base):
    __tablename__ = "lifecycle_template_stages"
    __table_args__ = (
        UniqueConstraint("template_id", "position"),
        UniqueConstraint("template_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("lifecycle_templates.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer)


class Project(CreatedAtMixin, Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    lifecycle_template_id: Mapped[int | None] = mapped_column(
        ForeignKey("lifecycle_templates.id", ondelete="SET NULL")
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProjectMember(CreatedAtMixin, Base):
    __tablename__ = "project_members"
    __table_args__ = (UniqueConstraint("project_id", "employee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    access_level: Mapped[AccessLevel] = mapped_column(
        enum_type(AccessLevel, "member_access_level"), default=AccessLevel.VIEW
    )
    added_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class ProjectStage(Base):
    __tablename__ = "project_stages"
    __table_args__ = (
        UniqueConstraint("project_id", "position"),
        UniqueConstraint("project_id", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    template_stage_id: Mapped[int | None] = mapped_column(
        ForeignKey("lifecycle_template_stages.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[int] = mapped_column(Integer)
