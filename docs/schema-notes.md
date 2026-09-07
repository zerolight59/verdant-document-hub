# Database review and implemented changes

The supplied diagram was a useful domain starting point, but it was not sufficient for the workflow described. The original SVG is preserved unchanged in this repository.

The implemented schema deliberately adds:

- `lifecycle_templates`, template stages, and project-stage copies so company standards can be reused while each project remains customizable.
- `project_members` and `document_permissions` as separate scopes. Membership exposes a project; a document permission can expose only one document to a visitor.
- `document_requirements` as the project checklist item. One requirement owns at most one document, and that document owns many immutable versions.
- Separate responsible and reviewer foreign keys with a database check constraint preventing the same employee from filling both roles.
- `document_reviews` tied to an exact document version. This keeps the decision and feedback historically accurate when a new version is uploaded.
- Research categories with a self-reference for nested classifications, research versions, endorsements, and optional project links.
- `audit_logs` for traceability and SHA-256 hashes on stored versions for integrity checks.
- Archive timestamps instead of ordinary hard deletion for project and research document records.

Important issues in the original diagram:

1. A simple “reviewed” flag cannot represent submission, change requests, repeated versions, reviewer comments, or who made a decision.
2. Project membership alone cannot express document-specific write/review rights or a visitor who may see only one shared document.
3. Storing a current file without an immutable version/review relationship makes historical approvals ambiguous.
4. A single project-document-type table does not cleanly separate the required checklist item from the uploaded document and its versions.
5. Research folders need a parent relationship for arbitrary nesting, while research approval should be an endorsement badge rather than the project review workflow.
6. Embedding/search-index data should be treated as a later derived subsystem, not the source of truth. Version 1 therefore implements indexed metadata search and leaves full-content/topic search for a later release.

The source of truth for the working first version is the SQLAlchemy model plus reviewed Alembic migrations.
