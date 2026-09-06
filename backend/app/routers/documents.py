from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_employee
from app.models import (
    AccessLevel,
    Document,
    DocumentRequirement,
    DocumentReview,
    DocumentVersion,
    Employee,
    RequirementStatus,
    ReviewDecision,
)
from app.schemas import ReviewDecisionIn
from app.services.audit_service import write_audit
from app.services.permission_service import (
    require_project_owner,
    require_requirement_access,
)
from app.services.storage_service import remove_stored_upload, store_upload

router = APIRouter(prefix="/documents", tags=["project documents"])


def latest_version(db: Session, document_id: int) -> DocumentVersion | None:
    return db.scalar(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    )


@router.post(
    "/requirements/{requirement_id}/versions",
    status_code=status.HTTP_201_CREATED,
)
async def upload_version(
    requirement_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    change_summary: str | None = Form(None),
) -> dict:
    requirement = require_requirement_access(
        db,
        requirement_id,
        employee,
        {AccessLevel.EDIT, AccessLevel.MANAGE},
    )
    stored = await store_upload(
        file,
        "projects",
        str(requirement.project_id),
        str(requirement.id),
    )

    try:
        document = db.scalar(select(Document).where(Document.requirement_id == requirement.id))
        if not document:
            document = Document(
                requirement_id=requirement.id,
                name=requirement.title,
                description=requirement.description,
                created_by_id=employee.id,
            )
            db.add(document)
            db.flush()

        next_number = (
            db.scalar(
                select(func.max(DocumentVersion.version_number)).where(
                    DocumentVersion.document_id == document.id
                )
            )
            or 0
        ) + 1
        version = DocumentVersion(
            document_id=document.id,
            version_number=next_number,
            file_name=stored.original_name,
            file_path=str(stored.path),
            mime_type=stored.mime_type,
            file_size=stored.size,
            checksum_sha256=stored.checksum_sha256,
            change_summary=change_summary,
            created_by_id=employee.id,
        )
        db.add(version)
        requirement.status = RequirementStatus.DRAFT
        db.flush()
        write_audit(
            db,
            employee.id,
            "DOCUMENT_VERSION_UPLOADED",
            "document_version",
            version.id,
            {
                "requirement_id": requirement.id,
                "version": next_number,
                "file_name": version.file_name,
                "checksum_sha256": version.checksum_sha256,
            },
            project_id=requirement.project_id,
        )
        db.commit()
        db.refresh(version)
    except Exception:
        db.rollback()
        remove_stored_upload(stored)
        raise

    return {
        "id": version.id,
        "version_number": version.version_number,
        "file_name": version.file_name,
        "status": requirement.status.value,
    }


@router.post("/versions/{version_id}/submit")
def submit_version(
    version_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    version = db.get(DocumentVersion, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found",
        )
    document = db.get(Document, version.document_id)
    requirement = require_requirement_access(
        db,
        document.requirement_id,
        employee,
        {AccessLevel.EDIT, AccessLevel.MANAGE},
    )
    if not requirement.reviewer_employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assign a reviewer before submitting",
        )
    if latest_version(db, document.id).id != version.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the newest version can be submitted",
        )
    if requirement.status not in {
        RequirementStatus.DRAFT,
        RequirementStatus.CHANGES_REQUESTED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document is not ready for submission",
        )

    version.submitted_at = datetime.now(UTC)
    requirement.status = RequirementStatus.SUBMITTED
    review = db.scalar(
        select(DocumentReview).where(DocumentReview.document_version_id == version.id)
    )
    if not review:
        db.add(
            DocumentReview(
                document_version_id=version.id,
                reviewer_employee_id=requirement.reviewer_employee_id,
                decision=ReviewDecision.UNDER_REVIEW,
            )
        )
    write_audit(
        db,
        employee.id,
        "DOCUMENT_VERSION_SUBMITTED",
        "document_version",
        version.id,
        {"requirement_id": requirement.id},
        project_id=requirement.project_id,
    )
    db.commit()
    return {
        "message": "Version submitted to the assigned reviewer",
        "status": requirement.status.value,
    }


@router.post("/reviews/{review_id}/start")
def start_review(
    review_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    review = db.get(DocumentReview, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review.reviewer_employee_id != employee.id and not employee.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned reviewer can start this review",
        )

    version = db.get(DocumentVersion, review.document_version_id)
    document = db.get(Document, version.document_id)
    requirement = db.get(DocumentRequirement, document.requirement_id)
    if requirement.status not in {
        RequirementStatus.SUBMITTED,
        RequirementStatus.UNDER_REVIEW,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document is not waiting for review",
        )

    requirement.status = RequirementStatus.UNDER_REVIEW
    write_audit(
        db,
        employee.id,
        "DOCUMENT_REVIEW_STARTED",
        "document_review",
        review.id,
        {"requirement_id": requirement.id},
        project_id=requirement.project_id,
    )
    db.commit()
    return {"message": "Review started", "status": requirement.status.value}


@router.post("/reviews/{review_id}/decision")
def decide_review(
    review_id: int,
    payload: ReviewDecisionIn,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    if payload.decision == ReviewDecision.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose Approved or Changes requested",
        )
    review = db.get(DocumentReview, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    if review.reviewer_employee_id != employee.id and not employee.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned reviewer can decide this review",
        )

    version = db.get(DocumentVersion, review.document_version_id)
    document = db.get(Document, version.document_id)
    requirement = db.get(DocumentRequirement, document.requirement_id)
    if requirement.status != RequirementStatus.UNDER_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Start the review before recording a decision",
        )

    review.decision = payload.decision
    review.comment = payload.comment
    review.decided_at = datetime.now(UTC)
    requirement.status = (
        RequirementStatus.APPROVED
        if payload.decision == ReviewDecision.APPROVED
        else RequirementStatus.CHANGES_REQUESTED
    )
    write_audit(
        db,
        employee.id,
        "DOCUMENT_REVIEW_DECIDED",
        "document_review",
        review.id,
        {
            "decision": payload.decision.value,
            "comment": payload.comment,
            "requirement_id": requirement.id,
        },
        project_id=requirement.project_id,
    )
    db.commit()
    return {
        "message": "Review decision saved",
        "status": requirement.status.value,
    }


@router.get("/{document_id}/versions")
def version_history(
    document_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    require_requirement_access(db, document.requirement_id, employee)
    versions = db.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(DocumentVersion.version_number.desc())
    ).all()
    return [
        {
            "id": item.id,
            "version_number": item.version_number,
            "file_name": item.file_name,
            "mime_type": item.mime_type,
            "file_size": item.file_size,
            "checksum_sha256": item.checksum_sha256,
            "change_summary": item.change_summary,
            "created_at": item.created_at,
            "submitted_at": item.submitted_at,
            "view_url": f"/api/documents/files/project/{item.id}",
        }
        for item in versions
    ]


@router.get("/files/project/{version_id}")
def view_project_file(
    version_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    version = db.get(DocumentVersion, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document version not found",
        )
    document = db.get(Document, version.document_id)
    require_requirement_access(db, document.requirement_id, employee)
    path = Path(version.file_path)
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored file is missing",
        )
    return FileResponse(
        path,
        media_type=version.mime_type,
        filename=version.file_name,
        content_disposition_type="inline",
    )


@router.delete("/requirements/{requirement_id}")
def archive_requirement(
    requirement_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    requirement = require_requirement_access(db, requirement_id, employee)
    require_project_owner(db, requirement.project_id, employee)
    requirement.archived_at = datetime.now(UTC)
    requirement.status = RequirementStatus.ARCHIVED
    write_audit(
        db,
        employee.id,
        "DOCUMENT_REQUIREMENT_ARCHIVED",
        "document_requirement",
        requirement.id,
        None,
        project_id=requirement.project_id,
    )
    db.commit()
    return {"message": "Document requirement archived and remains recoverable"}
