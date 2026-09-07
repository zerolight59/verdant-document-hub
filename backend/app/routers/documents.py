from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..config import settings
from ..db import get_db
from ..models import AccessLevel, Document, DocumentRequirement, DocumentReview, DocumentVersion, Employee, RequirementStatus, ReviewDecision
from ..permissions import require_project_owner, require_requirement_access
from ..schemas import ReviewDecisionIn
from ..security import get_current_employee

router = APIRouter(prefix="/documents", tags=["project documents"])


def latest_version(db: Session, document_id: int) -> DocumentVersion | None:
    return db.scalar(select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc()))


@router.post("/requirements/{requirement_id}/versions", status_code=status.HTTP_201_CREATED)
async def upload_version(
    requirement_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
    change_summary: str | None = Form(None),
):
    requirement = require_requirement_access(db, requirement_id, employee, {AccessLevel.EDIT, AccessLevel.MANAGE})
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    safe_suffix = Path(file.filename or "document.bin").suffix[:16]
    folder = settings.storage_root / "projects" / str(requirement.project_id) / str(requirement.id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid4().hex}{safe_suffix}"
    stored_path.write_bytes(content)
    document = db.scalar(select(Document).where(Document.requirement_id == requirement.id))
    if not document:
        document = Document(requirement_id=requirement.id, name=requirement.title, description=requirement.description, created_by_id=employee.id)
        db.add(document)
        db.flush()
    next_number = (db.scalar(select(func.max(DocumentVersion.version_number)).where(DocumentVersion.document_id == document.id)) or 0) + 1
    version = DocumentVersion(document_id=document.id, version_number=next_number, file_name=file.filename or stored_path.name, file_path=str(stored_path), mime_type=file.content_type or "application/octet-stream", file_size=len(content), checksum_sha256=sha256(content).hexdigest(), change_summary=change_summary, created_by_id=employee.id)
    db.add(version)
    requirement.status = RequirementStatus.DRAFT
    db.flush()
    write_audit(db, employee.id, "DOCUMENT_VERSION_UPLOADED", "document_version", version.id, {"requirement_id": requirement.id, "version": next_number, "file_name": version.file_name})
    db.commit()
    db.refresh(version)
    return {"id": version.id, "version_number": version.version_number, "file_name": version.file_name, "status": requirement.status.value}


@router.post("/versions/{version_id}/submit")
def submit_version(version_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    version = db.get(DocumentVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")
    document = db.get(Document, version.document_id)
    requirement = require_requirement_access(db, document.requirement_id, employee, {AccessLevel.EDIT, AccessLevel.MANAGE})
    if not requirement.reviewer_employee_id:
        raise HTTPException(status_code=400, detail="Assign a reviewer before submitting")
    if latest_version(db, document.id).id != version.id:
        raise HTTPException(status_code=400, detail="Only the newest version can be submitted")
    version.submitted_at = datetime.now(timezone.utc)
    requirement.status = RequirementStatus.SUBMITTED
    review = db.scalar(select(DocumentReview).where(DocumentReview.document_version_id == version.id))
    if not review:
        db.add(DocumentReview(document_version_id=version.id, reviewer_employee_id=requirement.reviewer_employee_id, decision=ReviewDecision.UNDER_REVIEW))
    write_audit(db, employee.id, "DOCUMENT_VERSION_SUBMITTED", "document_version", version.id, {"requirement_id": requirement.id})
    db.commit()
    return {"message": "Version submitted to the assigned reviewer", "status": requirement.status.value}


@router.post("/reviews/{review_id}/start")
def start_review(review_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    review = db.get(DocumentReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.reviewer_employee_id != employee.id and not employee.is_admin:
        raise HTTPException(status_code=403, detail="Only the assigned reviewer can start this review")
    version = db.get(DocumentVersion, review.document_version_id)
    requirement = db.get(DocumentRequirement, db.get(Document, version.document_id).requirement_id)
    requirement.status = RequirementStatus.UNDER_REVIEW
    write_audit(db, employee.id, "DOCUMENT_REVIEW_STARTED", "document_review", review.id, {"requirement_id": requirement.id})
    db.commit()
    return {"message": "Review started", "status": requirement.status.value}


@router.post("/reviews/{review_id}/decision")
def decide_review(review_id: int, payload: ReviewDecisionIn, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    if payload.decision == ReviewDecision.UNDER_REVIEW:
        raise HTTPException(status_code=400, detail="Choose Approved or Changes requested")
    review = db.get(DocumentReview, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.reviewer_employee_id != employee.id and not employee.is_admin:
        raise HTTPException(status_code=403, detail="Only the assigned reviewer can decide this review")
    version = db.get(DocumentVersion, review.document_version_id)
    requirement = db.get(DocumentRequirement, db.get(Document, version.document_id).requirement_id)
    review.decision = payload.decision
    review.comment = payload.comment
    review.decided_at = datetime.now(timezone.utc)
    requirement.status = RequirementStatus.APPROVED if payload.decision == ReviewDecision.APPROVED else RequirementStatus.CHANGES_REQUESTED
    write_audit(db, employee.id, "DOCUMENT_REVIEW_DECIDED", "document_review", review.id, {"decision": payload.decision.value, "comment": payload.comment, "requirement_id": requirement.id})
    db.commit()
    return {"message": "Review decision saved", "status": requirement.status.value}


@router.get("/{document_id}/versions")
def version_history(document_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    require_requirement_access(db, document.requirement_id, employee)
    versions = db.scalars(select(DocumentVersion).where(DocumentVersion.document_id == document_id).order_by(DocumentVersion.version_number.desc())).all()
    return [{"id": item.id, "version_number": item.version_number, "file_name": item.file_name, "mime_type": item.mime_type, "file_size": item.file_size, "checksum_sha256": item.checksum_sha256, "change_summary": item.change_summary, "created_at": item.created_at, "submitted_at": item.submitted_at, "view_url": f"/api/documents/files/project/{item.id}"} for item in versions]


@router.get("/files/project/{version_id}")
def view_project_file(version_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    version = db.get(DocumentVersion, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Document version not found")
    document = db.get(Document, version.document_id)
    require_requirement_access(db, document.requirement_id, employee)
    path = Path(version.file_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file is missing")
    return FileResponse(path, media_type=version.mime_type, filename=version.file_name, content_disposition_type="inline")


@router.delete("/requirements/{requirement_id}")
def archive_requirement(requirement_id: int, employee: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    requirement = require_requirement_access(db, requirement_id, employee)
    require_project_owner(db, requirement.project_id, employee)
    requirement.archived_at = datetime.now(timezone.utc)
    requirement.status = RequirementStatus.ARCHIVED
    write_audit(db, employee.id, "DOCUMENT_REQUIREMENT_ARCHIVED", "document_requirement", requirement.id, {"project_id": requirement.project_id})
    db.commit()
    return {"message": "Document requirement archived and remains recoverable"}


