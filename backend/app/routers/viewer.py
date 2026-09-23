from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_employee
from app.models import (
    Document,
    DocumentVersion,
    Employee,
    ResearchDocument,
    ResearchDocumentVersion,
)
from app.services.permission_service import require_requirement_access
from app.services.preview_service import preview_content

router = APIRouter(prefix="/viewer", tags=["document previews"])


@router.get("/{kind}/{version_id}")
def preview(
    kind: str,
    version_id: int,
    employee: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if kind == "project":
        version = db.get(DocumentVersion, version_id)
        if not version:
            raise HTTPException(404, "Document version not found")
        document = db.get(Document, version.document_id)
        require_requirement_access(db, document.requirement_id, employee)
    elif kind == "research":
        version = db.get(ResearchDocumentVersion, version_id)
        if not version:
            raise HTTPException(404, "Document version not found")
        document = db.get(ResearchDocument, version.research_document_id)
        if not document or document.archived_at is not None:
            raise HTTPException(404, "Research document not found")
    else:
        raise HTTPException(404, "Unknown document source")
    return preview_content(Path(version.file_path))
