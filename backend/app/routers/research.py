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
    Employee,
    ProjectResearchLink,
    ResearchCategory,
    ResearchDocument,
    ResearchDocumentVersion,
    ResearchEndorsement,
)
from app.schemas import CategoryCreate, EndorseResearch, LinkResearch
from app.services.audit_service import write_audit
from app.services.permission_service import require_project_access
from app.services.storage_service import remove_stored_upload, store_upload

router = APIRouter(prefix="/research", tags=["research library"])


@router.get("/categories")
def list_categories(
    _: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    categories = db.scalars(select(ResearchCategory).order_by(ResearchCategory.name)).all()
    return [{"id": item.id, "name": item.name, "parent_id": item.parent_id} for item in categories]


@router.post("/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if payload.parent_id and not db.get(ResearchCategory, payload.parent_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent classification not found",
        )
    duplicate = db.scalar(
        select(ResearchCategory).where(
            ResearchCategory.parent_id == payload.parent_id,
            ResearchCategory.name == payload.name,
        )
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This classification already exists here",
        )

    category = ResearchCategory(
        name=payload.name,
        parent_id=payload.parent_id,
        created_by_id=employee.id,
    )
    db.add(category)
    db.flush()
    write_audit(
        db,
        employee.id,
        "RESEARCH_CATEGORY_CREATED",
        "research_category",
        category.id,
        {"name": category.name, "parent_id": category.parent_id},
    )
    db.commit()
    return {"id": category.id, "name": category.name, "parent_id": category.parent_id}


@router.get("")
def list_research(
    _: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    documents = db.scalars(
        select(ResearchDocument)
        .where(ResearchDocument.archived_at.is_(None))
        .order_by(ResearchDocument.created_at.desc())
    ).all()
    result = []
    for document in documents:
        version = db.scalar(
            select(ResearchDocumentVersion)
            .where(ResearchDocumentVersion.research_document_id == document.id)
            .order_by(ResearchDocumentVersion.version_number.desc())
        )
        endorsements = db.execute(
            select(ResearchEndorsement, Employee)
            .join(Employee, Employee.id == ResearchEndorsement.employee_id)
            .where(ResearchEndorsement.research_document_id == document.id)
        ).all()
        result.append(
            {
                "id": document.id,
                "name": document.name,
                "description": document.description,
                "category_id": document.category_id,
                "category": db.get(ResearchCategory, document.category_id).name,
                "uploaded_by": db.get(Employee, document.uploaded_by_id).name,
                "created_at": document.created_at,
                "current_version": (
                    None
                    if not version
                    else {
                        "id": version.id,
                        "version_number": version.version_number,
                        "file_name": version.file_name,
                        "mime_type": version.mime_type,
                        "file_size": version.file_size,
                        "view_url": f"/api/research/files/{version.id}",
                    }
                ),
                "endorsements": [
                    {
                        "employee_id": item.employee_id,
                        "employee_name": endorser.name,
                        "label": item.label,
                    }
                    for item, endorser in endorsements
                ],
            }
        )
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_research(
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    category_id: int = Form(...),
    name: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
) -> dict:
    if not db.get(ResearchCategory, category_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research classification not found",
        )
    stored = await store_upload(file, "research", str(category_id))

    try:
        document = ResearchDocument(
            category_id=category_id,
            name=name,
            description=description,
            uploaded_by_id=employee.id,
        )
        db.add(document)
        db.flush()
        version = ResearchDocumentVersion(
            research_document_id=document.id,
            version_number=1,
            file_name=stored.original_name,
            file_path=str(stored.path),
            mime_type=stored.mime_type,
            file_size=stored.size,
            checksum_sha256=stored.checksum_sha256,
            uploaded_by_id=employee.id,
        )
        db.add(version)
        db.flush()
        write_audit(
            db,
            employee.id,
            "RESEARCH_DOCUMENT_UPLOADED",
            "research_document",
            document.id,
            {
                "name": name,
                "file_name": version.file_name,
                "checksum_sha256": version.checksum_sha256,
            },
        )
        db.commit()
    except Exception:
        db.rollback()
        remove_stored_upload(stored)
        raise
    return {"id": document.id, "version_id": version.id, "name": document.name}


@router.post("/{document_id}/versions", status_code=status.HTTP_201_CREATED)
async def upload_research_version(
    document_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> dict:
    document = db.get(ResearchDocument, document_id)
    if not document or document.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research document not found",
        )
    stored = await store_upload(file, "research", str(document.category_id))

    try:
        version_number = (
            db.scalar(
                select(func.max(ResearchDocumentVersion.version_number)).where(
                    ResearchDocumentVersion.research_document_id == document.id
                )
            )
            or 0
        ) + 1
        version = ResearchDocumentVersion(
            research_document_id=document.id,
            version_number=version_number,
            file_name=stored.original_name,
            file_path=str(stored.path),
            mime_type=stored.mime_type,
            file_size=stored.size,
            checksum_sha256=stored.checksum_sha256,
            uploaded_by_id=employee.id,
        )
        db.add(version)
        db.flush()
        write_audit(
            db,
            employee.id,
            "RESEARCH_VERSION_UPLOADED",
            "research_document_version",
            version.id,
            {"research_document_id": document.id, "version": version_number},
        )
        db.commit()
    except Exception:
        db.rollback()
        remove_stored_upload(stored)
        raise
    return {"id": version.id, "version_number": version.version_number}


@router.get("/files/{version_id}")
def view_research_file(
    version_id: int,
    _: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> FileResponse:
    version = db.get(ResearchDocumentVersion, version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research version not found",
        )
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


@router.post("/{document_id}/links")
def link_to_project(
    document_id: int,
    payload: LinkResearch,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    document = db.get(ResearchDocument, document_id)
    if not document or document.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research document not found",
        )
    require_project_access(db, payload.project_id, employee)
    link = db.scalar(
        select(ProjectResearchLink).where(
            ProjectResearchLink.project_id == payload.project_id,
            ProjectResearchLink.research_document_id == document_id,
        )
    )
    if not link:
        link = ProjectResearchLink(
            project_id=payload.project_id,
            research_document_id=document_id,
            linked_by_id=employee.id,
        )
        db.add(link)
        db.flush()
        write_audit(
            db,
            employee.id,
            "RESEARCH_LINKED_TO_PROJECT",
            "project_research_link",
            link.id,
            {"research_document_id": document_id},
            project_id=payload.project_id,
        )
        db.commit()
    return {"message": "Research document linked to project"}


@router.post("/{document_id}/endorse")
def endorse(
    document_id: int,
    payload: EndorseResearch,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    if not employee.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a senior approver can add an endorsement badge",
        )
    document = db.get(ResearchDocument, document_id)
    if not document or document.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research document not found",
        )
    endorsement = db.scalar(
        select(ResearchEndorsement).where(
            ResearchEndorsement.research_document_id == document_id,
            ResearchEndorsement.employee_id == employee.id,
        )
    )
    if endorsement:
        endorsement.label = payload.label
    else:
        db.add(
            ResearchEndorsement(
                research_document_id=document_id,
                employee_id=employee.id,
                label=payload.label,
            )
        )
    write_audit(
        db,
        employee.id,
        "RESEARCH_ENDORSED",
        "research_document",
        document_id,
        {"label": payload.label},
    )
    db.commit()
    return {"message": "Endorsement badge saved"}


@router.delete("/{document_id}")
def archive_research(
    document_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, str]:
    document = db.get(ResearchDocument, document_id)
    if not document or document.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research document not found",
        )
    if document.uploaded_by_id != employee.id and not employee.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the uploader or an administrator can archive this research document",
        )
    document.archived_at = datetime.now(UTC)
    write_audit(
        db,
        employee.id,
        "RESEARCH_DOCUMENT_ARCHIVED",
        "research_document",
        document.id,
    )
    db.commit()
    return {"message": "Research document archived and remains recoverable"}
