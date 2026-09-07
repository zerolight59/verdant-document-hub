from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import Any
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class AccessLevel(str, Enum): VIEW="VIEW"; EDIT="EDIT"; REVIEW="REVIEW"; MANAGE="MANAGE"
class RequirementStatus(str, Enum): MISSING="MISSING"; DRAFT="DRAFT"; SUBMITTED="SUBMITTED"; UNDER_REVIEW="UNDER_REVIEW"; CHANGES_REQUESTED="CHANGES_REQUESTED"; APPROVED="APPROVED"; ARCHIVED="ARCHIVED"
class ReviewDecision(str, Enum): UNDER_REVIEW="UNDER_REVIEW"; CHANGES_REQUESTED="CHANGES_REQUESTED"; APPROVED="APPROVED"

def enum_type(enum: type[Enum], name: str): return SAEnum(enum, name=name, native_enum=False, length=32)

class Employee(Base):
    __tablename__="employees"
    id:Mapped[int]=mapped_column(primary_key=True)
    employee_code:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(160)); email:Mapped[str]=mapped_column(String(255),unique=True,index=True)
    password_hash:Mapped[str]=mapped_column(String(255)); job_title:Mapped[str]=mapped_column(String(120),default="Employee")
    is_admin:Mapped[bool]=mapped_column(Boolean,default=False); is_active:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class LifecycleTemplate(Base):
    __tablename__="lifecycle_templates"
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(160),unique=True); description:Mapped[str|None]=mapped_column(Text)

class LifecycleTemplateStage(Base):
    __tablename__="lifecycle_template_stages"; __table_args__=(UniqueConstraint("template_id","position"),UniqueConstraint("template_id","name"))
    id:Mapped[int]=mapped_column(primary_key=True); template_id:Mapped[int]=mapped_column(ForeignKey("lifecycle_templates.id",ondelete="CASCADE"),index=True)
    name:Mapped[str]=mapped_column(String(120)); position:Mapped[int]=mapped_column(Integer)

class Project(Base):
    __tablename__="projects"
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(180),unique=True,index=True); description:Mapped[str|None]=mapped_column(Text)
    owner_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT"),index=True); lifecycle_template_id:Mapped[int|None]=mapped_column(ForeignKey("lifecycle_templates.id",ondelete="SET NULL"))
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ProjectMember(Base):
    __tablename__="project_members"; __table_args__=(UniqueConstraint("project_id","employee_id"),)
    id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True)
    employee_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="CASCADE"),index=True); access_level:Mapped[AccessLevel]=mapped_column(enum_type(AccessLevel,"member_access_level"),default=AccessLevel.VIEW)
    added_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class ProjectStage(Base):
    __tablename__="project_stages"; __table_args__=(UniqueConstraint("project_id","position"),UniqueConstraint("project_id","name"))
    id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True)
    template_stage_id:Mapped[int|None]=mapped_column(ForeignKey("lifecycle_template_stages.id",ondelete="SET NULL")); name:Mapped[str]=mapped_column(String(120)); position:Mapped[int]=mapped_column(Integer)

class DocumentType(Base):
    __tablename__="document_types"; __table_args__=(UniqueConstraint("project_id","name"),)
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(180),index=True); project_id:Mapped[int|None]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True)
    created_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class DocumentTypeDependency(Base):
    __tablename__="document_type_dependencies"; __table_args__=(UniqueConstraint("document_type_id","depends_on_document_type_id"),CheckConstraint("document_type_id <> depends_on_document_type_id",name="no_self_dependency"))
    id:Mapped[int]=mapped_column(primary_key=True); document_type_id:Mapped[int]=mapped_column(ForeignKey("document_types.id",ondelete="CASCADE"),index=True); depends_on_document_type_id:Mapped[int]=mapped_column(ForeignKey("document_types.id",ondelete="CASCADE"),index=True)

class DocumentRequirement(Base):
    __tablename__="document_requirements"; __table_args__=(UniqueConstraint("project_id","title"),CheckConstraint("responsible_employee_id IS NULL OR reviewer_employee_id IS NULL OR responsible_employee_id <> reviewer_employee_id",name="different_responsible_reviewer"))
    id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True); stage_id:Mapped[int]=mapped_column(ForeignKey("project_stages.id",ondelete="RESTRICT"),index=True); document_type_id:Mapped[int]=mapped_column(ForeignKey("document_types.id",ondelete="RESTRICT"),index=True)
    title:Mapped[str]=mapped_column(String(220),index=True); description:Mapped[str|None]=mapped_column(Text); responsible_employee_id:Mapped[int|None]=mapped_column(ForeignKey("employees.id",ondelete="SET NULL"),index=True); reviewer_employee_id:Mapped[int|None]=mapped_column(ForeignKey("employees.id",ondelete="SET NULL"),index=True)
    status:Mapped[RequirementStatus]=mapped_column(enum_type(RequirementStatus,"requirement_status"),default=RequirementStatus.MISSING,index=True); due_date:Mapped[date|None]=mapped_column(Date); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class DocumentPermission(Base):
    __tablename__="document_permissions"; __table_args__=(UniqueConstraint("requirement_id","employee_id"),)
    id:Mapped[int]=mapped_column(primary_key=True); requirement_id:Mapped[int]=mapped_column(ForeignKey("document_requirements.id",ondelete="CASCADE"),index=True); employee_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="CASCADE"),index=True); access_level:Mapped[AccessLevel]=mapped_column(enum_type(AccessLevel,"document_access_level")); granted_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class Document(Base):
    __tablename__="documents"
    id:Mapped[int]=mapped_column(primary_key=True); requirement_id:Mapped[int]=mapped_column(ForeignKey("document_requirements.id",ondelete="CASCADE"),unique=True,index=True); name:Mapped[str]=mapped_column(String(255),index=True); description:Mapped[str|None]=mapped_column(Text); created_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class DocumentVersion(Base):
    __tablename__="document_versions"; __table_args__=(UniqueConstraint("document_id","version_number"),)
    id:Mapped[int]=mapped_column(primary_key=True); document_id:Mapped[int]=mapped_column(ForeignKey("documents.id",ondelete="CASCADE"),index=True); version_number:Mapped[int]=mapped_column(Integer); file_name:Mapped[str]=mapped_column(String(255)); file_path:Mapped[str]=mapped_column(String(1024)); mime_type:Mapped[str]=mapped_column(String(180)); file_size:Mapped[int]=mapped_column(Integer); checksum_sha256:Mapped[str]=mapped_column(String(64),index=True); change_summary:Mapped[str|None]=mapped_column(Text); created_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); submitted_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class DocumentReview(Base):
    __tablename__="document_reviews"; __table_args__=(UniqueConstraint("document_version_id"),)
    id:Mapped[int]=mapped_column(primary_key=True); document_version_id:Mapped[int]=mapped_column(ForeignKey("document_versions.id",ondelete="CASCADE"),index=True); reviewer_employee_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT"),index=True); decision:Mapped[ReviewDecision]=mapped_column(enum_type(ReviewDecision,"review_decision"),default=ReviewDecision.UNDER_REVIEW); comment:Mapped[str|None]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); decided_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ResearchCategory(Base):
    __tablename__="research_categories"; __table_args__=(UniqueConstraint("parent_id","name"),)
    id:Mapped[int]=mapped_column(primary_key=True); name:Mapped[str]=mapped_column(String(180),index=True); parent_id:Mapped[int|None]=mapped_column(ForeignKey("research_categories.id",ondelete="CASCADE"),index=True); created_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class ResearchDocument(Base):
    __tablename__="research_documents"
    id:Mapped[int]=mapped_column(primary_key=True); category_id:Mapped[int]=mapped_column(ForeignKey("research_categories.id",ondelete="RESTRICT"),index=True); name:Mapped[str]=mapped_column(String(255),index=True); description:Mapped[str|None]=mapped_column(Text); uploaded_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now()); archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ResearchDocumentVersion(Base):
    __tablename__="research_document_versions"; __table_args__=(UniqueConstraint("research_document_id","version_number"),)
    id:Mapped[int]=mapped_column(primary_key=True); research_document_id:Mapped[int]=mapped_column(ForeignKey("research_documents.id",ondelete="CASCADE"),index=True); version_number:Mapped[int]=mapped_column(Integer); file_name:Mapped[str]=mapped_column(String(255)); file_path:Mapped[str]=mapped_column(String(1024)); mime_type:Mapped[str]=mapped_column(String(180)); file_size:Mapped[int]=mapped_column(Integer); checksum_sha256:Mapped[str]=mapped_column(String(64),index=True); uploaded_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class ResearchEndorsement(Base):
    __tablename__="research_endorsements"; __table_args__=(UniqueConstraint("research_document_id","employee_id"),)
    id:Mapped[int]=mapped_column(primary_key=True); research_document_id:Mapped[int]=mapped_column(ForeignKey("research_documents.id",ondelete="CASCADE"),index=True); employee_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="CASCADE"),index=True); label:Mapped[str]=mapped_column(String(100),default="Endorsed"); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class ProjectResearchLink(Base):
    __tablename__="project_research_links"; __table_args__=(UniqueConstraint("project_id","research_document_id"),)
    id:Mapped[int]=mapped_column(primary_key=True); project_id:Mapped[int]=mapped_column(ForeignKey("projects.id",ondelete="CASCADE"),index=True); research_document_id:Mapped[int]=mapped_column(ForeignKey("research_documents.id",ondelete="CASCADE"),index=True); linked_by_id:Mapped[int]=mapped_column(ForeignKey("employees.id",ondelete="RESTRICT")); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())

class AuditLog(Base):
    __tablename__="audit_logs"
    id:Mapped[int]=mapped_column(primary_key=True); actor_employee_id:Mapped[int|None]=mapped_column(ForeignKey("employees.id",ondelete="SET NULL"),index=True); action:Mapped[str]=mapped_column(String(100),index=True); entity_type:Mapped[str]=mapped_column(String(80),index=True); entity_id:Mapped[int|None]=mapped_column(Integer,index=True); details:Mapped[dict[str,Any]|None]=mapped_column(JSON); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),index=True)

Index("ix_document_requirements_search","title","status")
Index("ix_research_documents_search","name","category_id")
