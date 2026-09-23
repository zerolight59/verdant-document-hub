# Workspace update: document-first experience

## What changed

- Login opens **Home**, with only the projects the employee owns or belongs to, plus their pending document actions.
- **My actions** groups uploads/submissions and reviews assigned to that employee. While the app is visible, the workspace refreshes every 30 seconds, except while a form or action is in progress.
- Projects have a document list grouped by lifecycle stage and a persistent reader. People/stages, linked research and activity are separate tabs.
- PDFs use an in-app reader with fit-to-width, paging and zoom. Images and readable text/Office previews stay inside Verdant. Version history and side-by-side comparison preserve earlier files.
- Research has a classification tree, document list and reader. Categories include documents in their subcategories. Project references and related research are clickable and stored, with links visible in both directions.
- Search opens the matching document, including individually shared files; inaccessible project names are not exposed through research links.

## Exact responsibility rules

Project ownership controls membership, document requirements, assignments and sharing. It does not grant the right to perform someone else's upload or review.

Only the assigned responsible employee (who must belong to the project) can upload and submit. Only the assigned reviewer can start or decide the current review. Neither an administrator nor an owner bypasses this. Existing EDIT/MANAGE membership labels no longer grant task-wide upload access.

A submitted/under-review document cannot receive another upload or be reassigned until that review finishes. A changes request needs written feedback; the responsible employee must upload a new version before resubmitting. Reading an old version does not offer buttons to approve the current version.

## Supported viewing formats

| Format | In-app experience |
|---|---|
| PDF | Original page layout, page controls, zoom, fit-to-width |
| PNG, JPEG, GIF, WebP | Image reader |
| TXT, Markdown | Plain text; Markdown is not executed or rendered as HTML |
| CSV, XLSX | Readable tables; no formula execution |
| DOCX, PPTX | Extracted text, with slide sections for presentations |

Office previews are content previews, not exact Office rendering. Charts, embedded media, tracked changes and original pagination are not reproduced. Export to PDF when exact appearance matters. Legacy .doc/.xls, CAD, HTML/SVG and executable files are not accepted; convert them to PDF.

Uploads retain the configured maximum size (100 MB by default). Office/text previews are limited to 20 MB of input/uncompressed archive content; tabular output is bounded to 2,000 rows/50 columns and 20 worksheets. The reader states these limits.

## Update an existing local installation

Back up the database and document storage together first. From the repository folder:

```powershell
.\Stop-Verdant.ps1
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m alembic upgrade head
Set-Location ..\frontend
npm ci
Set-Location ..
.\Start-Verdant.ps1
```

Open http://localhost:3000 and sign in again. The one schema addition is migration **0003_research_related_links**, which creates a research-reference table; it does not delete or rewrite existing documents or employees.

Use localhost consistently for the frontend and API in local settings. Switching one address to 127.0.0.1 makes it a different browser site and can prevent cookies from being sent. For company deployment use same-site HTTPS addresses (ideally a single origin with /api reverse-proxied).

## Security changes and limits

- Credentials are submitted in a POST JSON body, not URL parameters. The login form does not render before JavaScript is ready and its inputs have no native-submission names.
- Session tokens are in HttpOnly, SameSite=Strict cookies, not localStorage. Cookies are Secure outside development.
- Cookie-authenticated writes require the configured frontend Origin. Invalid sessions return the user to login.
- Failed login attempts are throttled. The local limiter is per process; a shared gateway limit is still required for a multi-worker company deployment.
- Authorization is enforced in FastAPI, including file/preview routes, archives and latest-version review checks.
- Employee-directory responses omit private profile details.
- File MIME types come from an allowed extension map, not the sender's claimed content type; raw files receive sandbox/no-sniff headers. Office XML parsing rejects entity expansion.
- Non-development startup rejects placeholder signing secrets and an HTTP frontend origin.

This update is **not a penetration-test certification**. Before opening the service to a company network, configure HTTPS, restricted PostgreSQL authentication, managed secrets, backups, malware scanning/quarantine, upload quotas, proxy request limits, production process management and an independent security review. Logout clears the browser cookie; centrally revoking an already stolen JWT before expiry is not implemented. Employee administration/password reset and SSO remain separate work.

If a real password previously appeared in a URL, treat it as exposed: change it through your employee administration process and review browser history/access logs. Removing query parameters now does not erase historical copies.

## Repeatable verification

Standard checks:

```powershell
Set-Location frontend
npm run lint
npm run build
Set-Location ..\backend
.\.venv\Scripts\python.exe -m ruff check app scripts tests alembic
.\.venv\Scripts\python.exe -m pytest
```

PostgreSQL integration tests create a randomly named `verdant_test_*` database, migrate it, and remove only that database afterward. They never run against the application's data. Set `TEST_POSTGRES_ADMIN_URL` locally to a PostgreSQL URL with CREATE DATABASE permission; use an appropriate local secret mechanism, not a committed password.

```powershell
# In backend/, after setting TEST_POSTGRES_ADMIN_URL locally:
.\.venv\Scripts\python.exe -m pytest tests/test_workspace_integration.py -q
```

For the complete browser workflow, run the frontend at localhost:3000 with its API URL at localhost:8000/api, install frontend dependencies, then:

```powershell
$env:TEST_RUN_BROWSER = "1"
.\.venv\Scripts\python.exe -m pytest tests/test_workspace_integration.py -q -s
```

The test runner launches a separate backend against the disposable database, and redirects only its isolated browser contexts to it. It uses installed Microsoft Edge by default; alternatively install a Playwright-supported browser and set PLAYWRIGHT_CHANNEL. The local app database is unaffected.

The browser check covers login privacy, personal home, project creation, members/stages, responsible-only upload, reviewer feedback, new-version submission, approval, comparison, research categories, related/project links, search and mobile PDF layout.

## Where to make changes

- Home/login/search/navigation: `frontend/app/verdant-app.tsx`
- Project documents and review UI: `frontend/app/features/workspace/project-workspace.tsx`
- Research browsing and references: `frontend/app/features/workspace/research-workspace.tsx`
- Embedded file reader: `frontend/app/features/viewer/document-reader.tsx`
- Reusable form dialogs: `frontend/app/features/workspace/common.tsx`
- Styling: `frontend/app/workspace.css`
- Session transport: `frontend/app/workspace-api.ts`
- Task authority: `backend/app/services/permission_service.py`
- Review transitions: `backend/app/routers/documents.py`
- Cookie authentication: `backend/app/core/security.py`, `backend/app/routers/auth.py`
- Office/text previews: `backend/app/services/preview_service.py`, `backend/app/routers/viewer.py`
- Research references: `backend/app/models/research.py`, `backend/app/routers/research.py`
