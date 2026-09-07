from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from sqlalchemy import select

from app.audit import write_audit
from app.config import settings
from app.db import SessionLocal
from app.models import AccessLevel, Document, DocumentPermission, DocumentRequirement, DocumentReview, DocumentType, DocumentVersion, Employee, LifecycleTemplate, LifecycleTemplateStage, Project, ProjectMember, ProjectStage, RequirementStatus, ResearchCategory, ResearchDocument, ResearchDocumentVersion, ResearchEndorsement, ReviewDecision
from app.security import hash_password


def small_pdf(lines: list[str]) -> bytes:
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    commands = ["BT", "/F1 18 Tf", "72 720 Td"]
    for index, line in enumerate(escaped):
        if index:
            commands.append("0 -28 Td")
        commands.append(f"({line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output)); output.extend(f"{number} 0 obj\n".encode()); output.extend(obj); output.extend(b"\nendobj\n")
    xref = len(output); output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]: output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


def seed() -> None:
    with SessionLocal() as db:
        existing_owner = db.scalar(select(Employee).where(Employee.employee_code == "EMP-1042"))
        if existing_owner:
            visitor = db.scalar(select(Employee).where(Employee.employee_code == "VIS-1100"))
            if not visitor:
                visitor = Employee(employee_code="VIS-1100", name="Leela Thomas", email="leela.thomas@example.internal", password_hash=hash_password("verdant-demo"), job_title="Document visitor")
                db.add(visitor)
                db.flush()
            drawing = db.scalar(select(DocumentRequirement).where(DocumentRequirement.title == "Technical drawing - front assembly"))
            if drawing and not db.scalar(select(DocumentPermission).where(DocumentPermission.requirement_id == drawing.id, DocumentPermission.employee_id == visitor.id)):
                db.add(DocumentPermission(requirement_id=drawing.id, employee_id=visitor.id, access_level=AccessLevel.VIEW, granted_by_id=existing_owner.id))
            db.commit()
            print("Demo data already exists; visitor access is ready")
            return
        common_password = hash_password("verdant-demo")
        ananya = Employee(employee_code="EMP-1042", name="Ananya Rao", email="ananya.rao@example.internal", password_hash=common_password, job_title="Project owner", is_admin=True)
        vikram = Employee(employee_code="EMP-1088", name="Vikram Shah", email="vikram.shah@example.internal", password_hash=common_password, job_title="Senior reviewer")
        mira = Employee(employee_code="EMP-1071", name="Mira Nair", email="mira.nair@example.internal", password_hash=common_password, job_title="Design engineer")
        visitor = Employee(employee_code="VIS-1100", name="Leela Thomas", email="leela.thomas@example.internal", password_hash=common_password, job_title="Document visitor")
        db.add_all([ananya, vikram, mira, visitor]); db.flush()
        template = LifecycleTemplate(name="Standard product lifecycle", description="A reusable company baseline that each project can customize.")
        db.add(template); db.flush()
        stage_names = ["Research & requirements", "Design", "Validation", "Release"]
        template_stages = []
        for position, name in enumerate(stage_names, 1):
            item = LifecycleTemplateStage(template_id=template.id, name=name, position=position); db.add(item); template_stages.append(item)
        db.flush()
        project = Project(name="Project X", description="Demonstration project for the first working Verdant version.", owner_id=ananya.id, lifecycle_template_id=template.id)
        db.add(project); db.flush()
        db.add_all([ProjectMember(project_id=project.id, employee_id=ananya.id, access_level=AccessLevel.MANAGE, added_by_id=ananya.id), ProjectMember(project_id=project.id, employee_id=vikram.id, access_level=AccessLevel.REVIEW, added_by_id=ananya.id), ProjectMember(project_id=project.id, employee_id=mira.id, access_level=AccessLevel.EDIT, added_by_id=ananya.id)])
        project_stages = []
        for item in template_stages:
            stage = ProjectStage(project_id=project.id, template_stage_id=item.id, name=item.name, position=item.position); db.add(stage); project_stages.append(stage)
        db.flush()
        drawing_type = DocumentType(name="Technical drawing", project_id=project.id, created_by_id=ananya.id)
        material_type = DocumentType(name="Material specification", project_id=project.id, created_by_id=ananya.id)
        test_type = DocumentType(name="Test plan", project_id=project.id, created_by_id=ananya.id)
        db.add_all([drawing_type, material_type, test_type]); db.flush()
        drawing = DocumentRequirement(project_id=project.id, stage_id=project_stages[1].id, document_type_id=drawing_type.id, title="Technical drawing - front assembly", responsible_employee_id=mira.id, reviewer_employee_id=vikram.id, status=RequirementStatus.APPROVED)
        material = DocumentRequirement(project_id=project.id, stage_id=project_stages[0].id, document_type_id=material_type.id, title="Material specification", responsible_employee_id=mira.id, reviewer_employee_id=vikram.id, status=RequirementStatus.CHANGES_REQUESTED)
        test_plan = DocumentRequirement(project_id=project.id, stage_id=project_stages[2].id, document_type_id=test_type.id, title="Validation test plan", responsible_employee_id=ananya.id, reviewer_employee_id=vikram.id, status=RequirementStatus.MISSING)
        db.add_all([drawing, material, test_plan]); db.flush()
        db.add(DocumentPermission(requirement_id=drawing.id, employee_id=visitor.id, access_level=AccessLevel.VIEW, granted_by_id=ananya.id))
        folder = settings.storage_root / "demo"; folder.mkdir(parents=True, exist_ok=True)
        drawing_bytes = small_pdf(["Project X", "Technical drawing - front assembly", "Version 3 - Approved", "Verdant demonstration document"])
        drawing_path = folder / "project-x-technical-drawing-v3.pdf"; drawing_path.write_bytes(drawing_bytes)
        drawing_doc = Document(requirement_id=drawing.id, name=drawing.title, created_by_id=mira.id); db.add(drawing_doc); db.flush()
        drawing_version = DocumentVersion(document_id=drawing_doc.id, version_number=3, file_name=drawing_path.name, file_path=str(drawing_path), mime_type="application/pdf", file_size=len(drawing_bytes), checksum_sha256=sha256(drawing_bytes).hexdigest(), change_summary="Final front assembly dimensions", created_by_id=mira.id, submitted_at=datetime.now(timezone.utc)); db.add(drawing_version); db.flush()
        db.add(DocumentReview(document_version_id=drawing_version.id, reviewer_employee_id=vikram.id, decision=ReviewDecision.APPROVED, comment="Dimensions and tolerances confirmed.", decided_at=datetime.now(timezone.utc)))
        materials = ResearchCategory(name="Materials", created_by_id=ananya.id); db.add(materials); db.flush()
        metals = ResearchCategory(name="Metals", parent_id=materials.id, created_by_id=ananya.id); db.add(metals); db.flush()
        research_bytes = small_pdf(["Company research library", "High-strength steel comparison", "Reference upload for Project X"])
        research_path = folder / "high-strength-steel-comparison.pdf"; research_path.write_bytes(research_bytes)
        research = ResearchDocument(category_id=metals.id, name="High-strength steel comparison", description="Reference notes covering candidate grades and typical properties.", uploaded_by_id=mira.id); db.add(research); db.flush()
        db.add(ResearchDocumentVersion(research_document_id=research.id, version_number=1, file_name=research_path.name, file_path=str(research_path), mime_type="application/pdf", file_size=len(research_bytes), checksum_sha256=sha256(research_bytes).hexdigest(), uploaded_by_id=mira.id))
        db.add(ResearchEndorsement(research_document_id=research.id, employee_id=ananya.id, label="Approved reference"))
        write_audit(db, ananya.id, "DEMO_DATA_CREATED", "project", project.id, {"project_id": project.id})
        db.commit()
        print("Seeded demo employees, Project X, workflow records, and research library")


if __name__ == "__main__":
    seed()

