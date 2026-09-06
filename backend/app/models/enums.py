from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class AccessLevel(StrEnum):
    VIEW = "VIEW"
    EDIT = "EDIT"
    REVIEW = "REVIEW"
    MANAGE = "MANAGE"


class RequirementStatus(StrEnum):
    MISSING = "MISSING"
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"


class ReviewDecision(StrEnum):
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"


def enum_type(enum: type[StrEnum], name: str) -> SAEnum:
    # Stored as strings rather than PostgreSQL enum types so future values can be
    # introduced with ordinary Alembic column migrations.
    return SAEnum(enum, name=name, native_enum=False, length=32)
