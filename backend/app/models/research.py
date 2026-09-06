from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .common import Base, CreatedAtMixin


class ResearchCategory(CreatedAtMixin, Base):
    __tablename__ = "research_categories"
    __table_args__ = (UniqueConstraint("parent_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("research_categories.id", ondelete="CASCADE"), index=True
    )
    created_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class ResearchDocument(CreatedAtMixin, Base):
    __tablename__ = "research_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("research_categories.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ResearchDocumentVersion(CreatedAtMixin, Base):
    __tablename__ = "research_document_versions"
    __table_args__ = (UniqueConstraint("research_document_id", "version_number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    research_document_id: Mapped[int] = mapped_column(
        ForeignKey("research_documents.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(1024))
    mime_type: Mapped[str] = mapped_column(String(180))
    file_size: Mapped[int] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64), index=True)
    uploaded_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


class ResearchEndorsement(CreatedAtMixin, Base):
    __tablename__ = "research_endorsements"
    __table_args__ = (UniqueConstraint("research_document_id", "employee_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    research_document_id: Mapped[int] = mapped_column(
        ForeignKey("research_documents.id", ondelete="CASCADE"), index=True
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(100), default="Endorsed")


class ProjectResearchLink(CreatedAtMixin, Base):
    __tablename__ = "project_research_links"
    __table_args__ = (UniqueConstraint("project_id", "research_document_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    research_document_id: Mapped[int] = mapped_column(
        ForeignKey("research_documents.id", ondelete="CASCADE"), index=True
    )
    linked_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id", ondelete="RESTRICT"))


Index("ix_research_documents_search", ResearchDocument.name, ResearchDocument.category_id)
