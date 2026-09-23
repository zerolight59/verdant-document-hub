# Demo pack and presentation notes

The optional showcase adds 3 fictional projects, 14 required-document slots, 13 actual project-file versions, 8 research documents, 8 classifications and 2 extra sample employees. It includes all 6 active document states, review comments, audit timelines, visitor shares, 9 project/research links and 5 related-research links.

## Install or extend

- A fresh `Install-Verdant.ps1 -DemoData` installs the original sample accounts plus this showcase.
- On the existing sample installation, run `Add-DemoData.ps1` from the repository root.
- Installer demo seeding still skips a nonempty employee table. Use the separate add-demo command only on an intended demonstration installation.
- The add-demo script requires the exact original active sample identities. It refuses account/name collisions, never replaces passwords, and applies its data in one transaction.
- A completed pack has a persistent install marker. Repeating the command preserves current records and progress; it is not a reset command. For a clean rehearsal use a separate fresh demo database.

## Scenarios

| Project | Owner | What to demonstrate |
|---|---|---|
| DEMO - Atlas EV platform | Ananya, EMP-1042 | Missing files, draft submission, changes requested, approved versions, project references |
| DEMO - Nova lightweight seat | Ananya, EMP-1042 | Review in progress, version comparison and observer access |
| DEMO - Lab methods refresh | Mira, EMP-1071 | A different owner and narrower membership; Ananya is deliberately not a member |

Original Project X and its documents remain unchanged.

All seeded accounts use `verdant-demo` unless you have already changed their passwords:

| Employee ID | Username | Role |
|---|---|---|
| EMP-1042 | ananya.rao | Owner / administrator |
| EMP-1071 | mira.nair | Responsible employee; Lab project owner |
| EMP-1088 | vikram.shah | Assigned reviewer |
| VIS-1100 | leela.thomas | Document-only visitor |
| DEMO-1201 | demo.rohan | Additional engineer |
| DEMO-1202 | demo.sara | View-only project observer |

Use separate browser profiles for simultaneous users. Tabs in the same browser profile share the session.

## Presentation materials

- [Visual user guide: 20 pages](../output/pdf/Verdant-User-Guide.pdf): actual screens, instructions for every application page and a 10-minute walkthrough.
- [Ready-to-upload fictional revision](../demo-files/battery-enclosure-v3.pdf): use as Mira's response to the Atlas battery drawing feedback.
- [Full local setup](LOCAL_INSTALLATION_WINDOWS.md): Docker-free installation, migration and startup.

The walkthrough performs real uploads and reviews in the demo database. It is not a mock interaction.

## File formats and safety

The sample files contain only invented data, generated locally without third-party downloads. Multi-page PDFs, XLSX, CSV, DOCX and TXT demonstrate the in-app viewers. Seeded audit timestamps simulate an earlier workflow and are explicitly marked `demo: true`; they are not evidence of real employee activity.

Raw installed document files and database credentials are not committed. The seed creates its files in the configured STORAGE_ROOT on each installation. The guide's upload fixture is intentionally checked in as a small, fictional PDF.

Never enable demo accounts in a production employee database or use the fictional technical values for real decisions.

## Refreshing the guide

Prefer the isolated capture mode below, so screenshots cannot include real project names or employee records. It creates a temporary demo database and removes it afterward. Start the frontend at `http://localhost:3000`, then run from `backend/` in PowerShell:

```powershell
$env:TEST_POSTGRES_ADMIN_URL = 'postgresql+psycopg://USER:PASSWORD@localhost:5432/postgres'
$env:TEST_RUN_BROWSER = '1'
$env:TEST_CAPTURE_GUIDE = '1'
.\.venv\Scripts\python.exe -m pytest tests/test_workspace_integration.py::test_browser_workflows -q -s
Remove-Item Env:TEST_CAPTURE_GUIDE
Remove-Item Env:TEST_RUN_BROWSER
Remove-Item Env:TEST_POSTGRES_ADMIN_URL
```

Supply your local PostgreSQL test administrator connection (URL-encode special characters in credentials). This account needs permission to create temporary databases. Never commit the connection string. Install backend test dependencies and frontend dependencies first.

Alternatively, on a separate, fictional-data-only demo installation using the default frontend/API addresses:

1. Install frontend dependencies and start the app.
2. In frontend/, run `node tests/capture-guide.mjs`. It signs in only to sample accounts and opens forms without saving them.
3. Install `scripts/requirements-docs.txt` in a Python environment.
4. From the repository root, run `python scripts/build_user_guide.py`.
5. Render and visually inspect every PDF page before publishing the guide.

Capture uses Microsoft Edge by default; PLAYWRIGHT_CHANNEL can select another installed supported browser. Screenshots assume the baseline demo states. If a walkthrough has changed them, use isolated capture. In either mode, regenerate the PDF with steps 3-5 and check that screenshots contain only fictional records before publishing.
