"""Add a coherent showcase once, without resetting existing users or documents.

Run from backend/: python -m scripts.seed_showcase
Requires the original sample identities created by scripts.seed_demo.
"""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    AccessLevel,
    AuditLog,
    Document,
    DocumentPermission,
    DocumentRequirement,
    DocumentReview,
    DocumentType,
    DocumentVersion,
    Employee,
    Project,
    ProjectMember,
    ProjectResearchLink,
    ProjectStage,
    RequirementStatus,
    ResearchCategory,
    ResearchDocument,
    ResearchDocumentVersion,
    ResearchEndorsement,
    ReviewDecision,
)
from app.models.research import ResearchRelatedLink
from app.services.preview_service import MIME_TYPES
from scripts.demo_files import demo_docx, demo_pdf, demo_xlsx

MARKER = "DEMO_SHOWCASE_V1_INSTALLED"
SAMPLE_IDENTITIES = {
    "owner": ("EMP-1042", "ananya.rao"),
    "writer": ("EMP-1071", "mira.nair"),
    "reviewer": ("EMP-1088", "vikram.shah"),
    "visitor": ("VIS-1100", "leela.thomas"),
}
PROJECTS = [
    (
        "DEMO - Atlas EV platform",
        "owner",
        "Fictional battery enclosure programme. Demonstrates every document review state.",
        [
            (
                "Material selection report",
                0,
                "APPROVED",
                "writer",
                2,
                "Candidate comparison completed.",
            ),
            (
                "Battery enclosure drawing",
                1,
                "CHANGES_REQUESTED",
                "writer",
                2,
                "Increase the illustrative flange clearance from 12 mm to 16 mm; "
                "update the revision note.",
            ),
            (
                "Thermal validation plan",
                2,
                "SUBMITTED",
                "writer",
                1,
                "Ready for reviewer assessment.",
            ),
            (
                "Supplier compliance dossier",
                0,
                "MISSING",
                "engineer",
                0,
                "Awaiting a fictional supplier pack.",
            ),
            (
                "Design risk assessment",
                1,
                "DRAFT",
                "owner",
                1,
                "Initial risk register for internal discussion.",
            ),
            (
                "Release checklist",
                3,
                "MISSING",
                "owner",
                0,
                "Complete after all required documents are approved.",
            ),
        ],
    ),
    (
        "DEMO - Nova lightweight seat",
        "owner",
        "Fictional seat component study. Compare revisions and follow an active review.",
        [
            (
                "Aluminium bracket drawing",
                1,
                "UNDER_REVIEW",
                "writer",
                2,
                "Hole pattern revised for review.",
            ),
            (
                "Fastener specification",
                1,
                "APPROVED",
                "engineer",
                1,
                "Fictional fastener schedule checked.",
            ),
            (
                "Fatigue test method",
                2,
                "DRAFT",
                "writer",
                1,
                "Add the proposed sample identification scheme.",
            ),
            (
                "Prototype inspection record",
                2,
                "MISSING",
                "engineer",
                0,
                "Inspection evidence not uploaded.",
            ),
            (
                "Packaging guideline",
                3,
                "APPROVED",
                "owner",
                1,
                "Demonstration handling notes approved.",
            ),
        ],
    ),
    (
        "DEMO - Lab methods refresh",
        "writer",
        "Fictional lab methods workspace owned by Mira. Shows project-specific visibility.",
        [
            (
                "Sample preparation instruction",
                0,
                "APPROVED",
                "engineer",
                1,
                "Illustrative preparation notes checked.",
            ),
            (
                "Measurement uncertainty worksheet",
                2,
                "SUBMITTED",
                "writer",
                1,
                "Fictional worksheet ready for review.",
            ),
            (
                "Maintenance verification",
                3,
                "MISSING",
                "writer",
                0,
                "Evidence to be added by the responsible employee.",
            ),
        ],
    ),
]
STAGES = ["Research & requirements", "Design", "Validation", "Release"]


def seed_showcase(db: Session | None = None, storage_root: Path | None = None) -> dict:
    """One transaction and an advisory lock make repeats/concurrent runs safe."""
    if db is None:
        with SessionLocal() as session:
            return seed_showcase(session, storage_root)
    files: list[Path] = []
    folder = (storage_root or settings.storage_root) / "demo-showcase" / uuid4().hex
    try:
        db.execute(text("SELECT pg_advisory_xact_lock(762319051)"))
        marker = db.scalar(select(AuditLog).where(AuditLog.action == MARKER))
        if marker:
            db.rollback()
            return {
                "created": False,
                "message": "Showcase already installed; current data preserved",
            }
        people = {}
        for key, (code, username) in SAMPLE_IDENTITIES.items():
            employee = db.scalar(select(Employee).where(Employee.employee_code == code))
            if (
                not employee
                or employee.username != username
                or employee.email != username + "@example.internal"
                or not employee.is_active
            ):
                raise ValueError(
                    "Showcase requires the original active demo identities. "
                    "Use a separate demo database; existing employee accounts are never replaced."
                )
            people[key] = employee
        if db.scalar(select(Project.id).where(Project.name.in_([p[0] for p in PROJECTS]))):
            raise ValueError(
                "A showcase project name already exists without its install marker. "
                "Nothing was changed; use a fresh demo database."
            )
        if db.scalar(select(ResearchCategory.id).where(ResearchCategory.name == "DEMO research")):
            raise ValueError(
                "DEMO research already exists without its install marker; nothing changed."
            )
        for code, username, name, key, title in [
            ("DEMO-1201", "demo.rohan", "Rohan Mehta (Demo)", "engineer", "Test engineer"),
            ("DEMO-1202", "demo.sara", "Sara Das (Demo)", "observer", "Project observer"),
        ]:
            if db.scalar(
                select(Employee).where(
                    (Employee.employee_code == code)
                    | (Employee.username == username)
                    | (Employee.email == username + "@example.invalid")
                )
            ):
                raise ValueError(
                    f"Demo identifier {code} is already used; no account was overwritten."
                )
            employee = Employee(
                employee_code=code,
                username=username,
                name=name,
                email=username + "@example.invalid",
                password_hash=hash_password("verdant-demo"),
                job_title=title,
                profile_data={"demo_pack": "showcase-v1"},
            )
            db.add(employee)
            db.flush()
            people[key] = employee
        folder.mkdir(parents=True, exist_ok=False)
        now = datetime.now(UTC)
        start = now - timedelta(days=18)

        def audit(actor, action, entity, identifier, details=None, project=None, when=None):
            db.add(
                AuditLog(
                    actor_employee_id=actor,
                    action=action,
                    entity_type=entity,
                    entity_id=identifier,
                    project_id=project,
                    details={"demo": True, **(details or {})},
                    created_at=when or now,
                )
            )

        def store(name, content):
            path = folder / name
            with path.open("xb") as destination:
                destination.write(content)
            files.append(path)
            return {
                "file_name": name,
                "file_path": str(path.resolve()),
                "file_size": len(content),
                "checksum_sha256": sha256(content).hexdigest(),
                "mime_type": MIME_TYPES[path.suffix],
            }

        projects = []
        requirement_count = version_count = 0
        for p_index, (name, owner_key, description, specs) in enumerate(PROJECTS):
            owner = people[owner_key]
            project = Project(
                name=name,
                description=description,
                owner_id=owner.id,
                created_at=start + timedelta(days=p_index),
            )
            db.add(project)
            db.flush()
            projects.append(project)
            member_keys = (
                ["owner", "writer", "reviewer", "engineer", "observer"]
                if p_index < 2
                else ["writer", "reviewer", "engineer"]
            )
            for key in member_keys:
                db.add(
                    ProjectMember(
                        project_id=project.id,
                        employee_id=people[key].id,
                        access_level=AccessLevel.MANAGE if key == owner_key else AccessLevel.VIEW,
                        added_by_id=owner.id,
                    )
                )
            stages = []
            for position, label in enumerate(STAGES, 1):
                stage = ProjectStage(project_id=project.id, name=label, position=position)
                db.add(stage)
                db.flush()
                stages.append(stage)
            audit(
                owner.id,
                "PROJECT_CREATED",
                "project",
                project.id,
                {"name": name},
                project.id,
                start,
            )
            for r_index, (title, stage_index, state, author_key, version_total, note) in enumerate(
                specs
            ):
                author, reviewer = people[author_key], people["reviewer"]
                document_type = DocumentType(
                    project_id=project.id, name=title, created_by_id=owner.id
                )
                db.add(document_type)
                db.flush()
                requirement = DocumentRequirement(
                    project_id=project.id,
                    stage_id=stages[stage_index].id,
                    document_type_id=document_type.id,
                    title=title,
                    description="Fictional demonstration requirement. " + note,
                    responsible_employee_id=author.id,
                    reviewer_employee_id=reviewer.id,
                    status=RequirementStatus(state),
                    due_date=(now + timedelta(days=5 + r_index * 3)).date(),
                    created_at=start + timedelta(days=1),
                )
                db.add(requirement)
                db.flush()
                requirement_count += 1
                audit(
                    owner.id,
                    "DOCUMENT_REQUIREMENT_CREATED",
                    "document_requirement",
                    requirement.id,
                    {"title": title},
                    project.id,
                    start + timedelta(days=1, minutes=r_index),
                )
                if state == "APPROVED" and r_index == 0:
                    db.add(
                        DocumentPermission(
                            requirement_id=requirement.id,
                            employee_id=people["visitor"].id,
                            access_level=AccessLevel.VIEW,
                            granted_by_id=owner.id,
                        )
                    )
                if version_total == 0:
                    continue
                document = Document(
                    requirement_id=requirement.id, name=title, created_by_id=author.id
                )
                db.add(document)
                db.flush()
                for number in range(1, version_total + 1):
                    timestamp = start + timedelta(days=3 + number * 3, minutes=r_index * 20)
                    latest = number == version_total
                    submitted = not (latest and state == "DRAFT")
                    payload = demo_pdf(
                        title,
                        name,
                        number,
                        [
                            note
                            if latest
                            else "Initial concept: review feedback is awaiting incorporation.",
                            f"Prepared by {author.name}; assigned reviewer: {reviewer.name}.",
                            "Fictional design parameter: clearance "
                            + (
                                "16 mm."
                                if number > 1 and state != "CHANGES_REQUESTED"
                                else "12 mm."
                            ),
                            "Scope: controlled files, review decisions and retained versions.",
                            "Evidence and figures in this document are invented.",
                        ],
                    )
                    version = DocumentVersion(
                        document_id=document.id,
                        version_number=number,
                        created_by_id=author.id,
                        change_summary=note
                        if latest
                        else "Initial proposal for reviewer feedback.",
                        created_at=timestamp,
                        submitted_at=timestamp + timedelta(hours=1) if submitted else None,
                        **store(
                            f"demo-p{p_index + 1}-document-{r_index + 1}-v{number}.pdf", payload
                        ),
                    )
                    db.add(version)
                    db.flush()
                    version_count += 1
                    audit(
                        author.id,
                        "DOCUMENT_VERSION_UPLOADED",
                        "document_version",
                        version.id,
                        {"requirement_id": requirement.id, "version": number},
                        project.id,
                        timestamp,
                    )
                    if submitted:
                        decision = (
                            ReviewDecision.CHANGES_REQUESTED
                            if not latest
                            else ReviewDecision.APPROVED
                            if state == "APPROVED"
                            else ReviewDecision.CHANGES_REQUESTED
                            if state == "CHANGES_REQUESTED"
                            else ReviewDecision.UNDER_REVIEW
                        )
                        decided = decision != ReviewDecision.UNDER_REVIEW
                        comment = (
                            (
                                note
                                if latest
                                else "Clarify the illustrative clearance and revision notes."
                            )
                            if decided
                            else None
                        )
                        review = DocumentReview(
                            document_version_id=version.id,
                            reviewer_employee_id=reviewer.id,
                            decision=decision,
                            comment=comment,
                            created_at=timestamp + timedelta(hours=1),
                            decided_at=timestamp + timedelta(hours=4) if decided else None,
                        )
                        db.add(review)
                        db.flush()
                        audit(
                            author.id,
                            "DOCUMENT_VERSION_SUBMITTED",
                            "document_version",
                            version.id,
                            {"requirement_id": requirement.id},
                            project.id,
                            timestamp + timedelta(hours=1),
                        )
                        if decided or state == "UNDER_REVIEW":
                            audit(
                                reviewer.id,
                                "DOCUMENT_REVIEW_STARTED",
                                "document_review",
                                review.id,
                                {"requirement_id": requirement.id},
                                project.id,
                                timestamp + timedelta(hours=2),
                            )
                        if decided:
                            audit(
                                reviewer.id,
                                "DOCUMENT_REVIEW_DECIDED",
                                "document_review",
                                review.id,
                                {
                                    "decision": decision.value,
                                    "comment": comment,
                                    "requirement_id": requirement.id,
                                },
                                project.id,
                                timestamp + timedelta(hours=4),
                            )

        root = ResearchCategory(name="DEMO research", created_by_id=people["owner"].id)
        db.add(root)
        db.flush()
        categories = {}
        for key, label, parent in [
            ("materials", "Materials", None),
            ("metals", "Metals & alloys", "materials"),
            ("polymers", "Polymers", "materials"),
            ("testing", "Testing methods", None),
            ("thermal", "Thermal studies", "testing"),
            ("fatigue", "Fatigue studies", "testing"),
            ("process", "Working practices", None),
        ]:
            category = ResearchCategory(
                name=label,
                parent_id=categories[parent].id if parent else root.id,
                created_by_id=people["writer"].id,
            )
            db.add(category)
            db.flush()
            categories[key] = category
        research_specs = [
            (
                "[DEMO] Aluminium alloy selection notes",
                "metals",
                "pdf",
                "Compare fictional candidates A, B and C for mass, cost and review readiness.",
            ),
            (
                "[DEMO] Material comparison workbook",
                "metals",
                "xlsx",
                "A small spreadsheet with invented candidate scores; no engineering claims.",
            ),
            (
                "[DEMO] Polymer enclosure reference",
                "polymers",
                "pdf",
                "A reference for documenting fictional housing material choices.",
            ),
            (
                "[DEMO] Thermal test checklist",
                "thermal",
                "pdf",
                "Example evidence checklist for a demonstration-only thermal study.",
            ),
            (
                "[DEMO] Fatigue study observations",
                "fatigue",
                "csv",
                "Invented observations for showing in-app CSV viewing.",
            ),
            (
                "[DEMO] Supplier handover notes",
                "process",
                "docx",
                "A modern Word file demonstrating readable in-app content preview.",
            ),
            (
                "[DEMO] Research naming conventions",
                "process",
                "txt",
                "A short naming guide for the fictional research library.",
            ),
            (
                "[DEMO] Measurement uncertainty primer",
                "testing",
                "pdf",
                "A fictional reference linked to the laboratory methods workspace.",
            ),
        ]
        research = []
        for index, (title, category_key, extension, description) in enumerate(research_specs):
            content = (
                demo_xlsx()
                if extension == "xlsx"
                else demo_docx(
                    title,
                    [
                        description,
                        "Record the source, version, owner and context.",
                        "Link the reference to a project instead of copying it.",
                    ],
                )
                if extension == "docx"
                else (
                    b"DEMO ONLY - invented observations\nSpecimen,Sample count,Observation\n"
                    b"A,5,Stable example\nB,5,Follow-up example\nC,5,Reference example\n"
                )
                if extension == "csv"
                else (
                    title + "\nFICTIONAL DEMO ONLY\n\nUse clear titles.\n"
                    "Keep revisions together.\nLink reusable references.\n"
                ).encode()
                if extension == "txt"
                else demo_pdf(
                    title,
                    "Company research / fictional showcase",
                    1,
                    [
                        description,
                        "This reference is illustrative, not an engineering source.",
                        "Research uploads are immediately visible to authenticated employees.",
                    ],
                )
            )
            item = ResearchDocument(
                category_id=categories[category_key].id,
                name=title,
                description=description,
                uploaded_by_id=people["writer"].id,
                created_at=start + timedelta(days=index),
            )
            db.add(item)
            db.flush()
            research.append(item)
            db.add(
                ResearchDocumentVersion(
                    research_document_id=item.id,
                    version_number=1,
                    uploaded_by_id=people["writer"].id,
                    **store(f"demo-research-{index + 1}.{extension}", content),
                )
            )
            if index in (0, 3, 7):
                db.add(
                    ResearchEndorsement(
                        research_document_id=item.id,
                        employee_id=people["owner"].id,
                        label="Demo: useful reference",
                    )
                )
            audit(
                people["writer"].id,
                "RESEARCH_DOCUMENT_UPLOADED",
                "research_document",
                item.id,
                {"name": title},
            )
        for project_index, research_indices in [(0, [0, 2, 3, 5]), (1, [0, 1, 4]), (2, [7, 6])]:
            project = projects[project_index]
            for index in research_indices:
                link = ProjectResearchLink(
                    project_id=project.id,
                    research_document_id=research[index].id,
                    linked_by_id=project.owner_id,
                )
                db.add(link)
                db.flush()
                audit(
                    project.owner_id,
                    "RESEARCH_LINKED_TO_PROJECT",
                    "project_research_link",
                    link.id,
                    {"research_document_id": research[index].id},
                    project.id,
                )
        for first, second in [(0, 1), (0, 2), (3, 7), (4, 7), (5, 6)]:
            source, target = sorted((research[first].id, research[second].id))
            db.add(
                ResearchRelatedLink(
                    source_id=source, target_id=target, linked_by_id=people["writer"].id
                )
            )
            audit(
                people["writer"].id,
                "RESEARCH_REFERENCE_ADDED",
                "research_document",
                source,
                {"target_id": target},
            )
        totals = {
            "projects": len(projects),
            "requirements": requirement_count,
            "project_versions": version_count,
            "research_documents": len(research),
            "new_employees": 2,
            "categories": len(categories) + 1,
        }
        audit(people["owner"].id, MARKER, "demo_pack", None, totals)
        db.commit()
        return {"created": True, **totals}
    except Exception:
        db.rollback()
        for path in files:
            path.unlink(missing_ok=True)
        if folder.exists():
            folder.rmdir()
        raise


if __name__ == "__main__":
    print(seed_showcase())
