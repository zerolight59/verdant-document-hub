# Database design decisions

The supplied diagram is preserved unchanged as `docs/original-database-diagram.svg`. It was the domain starting point; the PostgreSQL SQLAlchemy model and reviewed Alembic migrations are the executable source of truth.

## Current product decisions

- PostgreSQL is the only runtime database. Verdant does not connect to the Calibration database.
- `employees` is owned by Verdant and supports an employee code, optional username, Argon2 password hash, organizational fields, active/admin flags, and PostgreSQL JSONB profile data for company-specific migration fields.
- `lifecycle_templates` and template stages provide company standards. Stages are copied to `project_stages` so each project can customize its lifecycle without changing the standard template.
- `project_members` and `document_permissions` are separate scopes. Project membership exposes a project; document permission can expose only one requirement to a visitor.
- `document_requirements` is the project checklist item. One requirement owns at most one logical document, and that document owns many immutable versions.
- Responsible employee and reviewer are separate foreign keys. An application check and database constraint prevent the same employee from filling both roles.
- `document_reviews` is tied to an exact document version, preserving which bytes were approved or returned for changes.
- Research uses nested categories, immutable file versions, administrator endorsements, and optional project links. It does not use the controlled project review workflow.
- `audit_logs.project_id` directly scopes project activity. This avoids unreliable filtering through unstructured audit details.
- File rows store a SHA-256 checksum. Actual bytes remain under `STORAGE_ROOT` and must be backed up together with PostgreSQL.
- Archive timestamps are used instead of ordinary hard deletion for project requirements and research documents.

## Why the original shape needed refinement

1. A simple reviewed flag cannot represent submission, change requests, repeated versions, reviewer comments, or who made a decision.
2. Project membership alone cannot express document-specific write/review rights or a visitor who may see only one shared document.
3. Storing a current file without immutable versions and version-specific reviews makes historical approval ambiguous.
4. A project document type is different from a required checklist slot, the logical document, and each immutable uploaded version.
5. Research classifications need a parent relationship for arbitrary nesting. Research approval is an endorsement badge rather than workflow state.
6. Audit filtering needs a first-class project reference rather than depending on optional JSON details.
7. Employee data needs stable local IDs so historical assignments and reviews remain valid even when an employee becomes inactive.

## PostgreSQL and embeddings

PostgreSQL was selected now so a later pgvector feature can live beside the product’s relational data. The current baseline deliberately does not install the `vector` extension or create speculative embedding tables.

When content search is implemented, use a new append-only migration with chunks tied to immutable project or research version IDs. Record the source checksum, extraction status, embedding model, dimensions, chunk order, and timestamps. Embeddings are derived indexes and must be rebuildable from the authoritative files and metadata.

## Migration rule

`backend/alembic/versions/0001_postgresql_baseline.py` is the baseline for a new PostgreSQL installation. Once an installation has applied it, do not rewrite it. Every later schema change receives a new ordered Alembic migration.

Moving existing MySQL employees is covered in `docs/MYSQL_TO_POSTGRESQL_MIGRATION.md`. Moving project/document history requires a dedicated, separately tested migration that preserves IDs, foreign keys, audit records, and file paths together.
