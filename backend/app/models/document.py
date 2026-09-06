from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .common import Base, CreatedAtMixin
from .enums import AccessLevel, RequirementStatus, ReviewDecision, enum_type


class DocumentType(CreatedAtMixin, Base):
    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("project_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class DocumentTypeDependency(Base):
    __tablename__ = "document_type_dependencies"
    __table_args__ = (
        UniqueConstraint("document_type_id", "depends_on_document_type_id"),
        CheckConstraint(
            "document_type_id <> depends_on_document_type_id",
            name="no_self_dependency",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id", ondelete="CASCADE"), index=True
    )
    depends_on_document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id", ondelete="CASCADE"), index=True
    )


class DocumentRequirement(CreatedAtMixin, Base):
    __tablename__ = "document_requirements"
    __table_args__ = (
        UniqueConstraint("project_id", "title"),
        CheckConstraint(
            "responsible_employee_id IS NULL OR reviewer_employee_id IS NULL "
            "OR responsible_employee_id <> reviewer_employee_id",
            name="different_responsible_reviewer",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    stage_id: Mapped[int] = mapped_column(
        ForeignKey("project_stages.id", ondelete="RESTRICT"), index=True
    )
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id", ondelete="RESTRICT"), index=True
    )
    title: Mapped[str] = mapped_column(String(220), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    responsible_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True
    )
    reviewer_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[RequirementStatus] = mapped_column(
        enum_type(RequirementStatus, "requirement_status"),
        default=RequirementStatus.MISSING,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentPermission(CreatedAtMixin, Base):
    __tablename__ = "document_permissions"
    __table_args__ = (UniqueConstraint("requirement_id", "employee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("document_requirements.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    access_level: Mapped[AccessLevel] = mapped_column(
        enum_type(AccessLevel, "document_access_level")
    )
    granted_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class Document(CreatedAtMixin, Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("document_requirements.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class DocumentVersion(CreatedAtMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (UniqueConstraint("document_id", "version_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str] = mapped_column(String(180))
    file_size: Mapped[int] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    change_summary: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentReview(CreatedAtMixin, Base):
    __tablename__ = "document_reviews"
    __table_args__ = (UniqueConstraint("document_version_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    document_version_id: Mapped[int] = mapped_column(
        ForeignKey("document_versions.id", ondelete="CASCADE"), index=True
    )
    reviewer_employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="RESTRICT"), index=True
    )
    decision: Mapped[ReviewDecision] = mapped_column(
        enum_type(ReviewDecision, "review_decision"),
        default=ReviewDecision.UNDER_REVIEW,
    )
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


Index("ix_document_requirements_search", DocumentRequirement.title, DocumentRequirement.status)
