# Verdant Document Hub

Verdant is a working first version of an internal company documentation system. It combines controlled project documents with an open research library, while keeping project planning outside the product boundary.

## What works

- Employee ID/password login backed by the `employees` table; passwords are Argon2-hashed.
- Project creation from reusable lifecycle templates, plus project-specific stages.
- Project membership with view, edit, review, and manage access.
- Document-specific permissions, including visitor access without exposing the whole project.
- One responsible employee and one different reviewer per required document.
- Versioned file uploads and the workflow `Draft → Submitted → Under review → Changes requested → New version → Approved`.
- Reviewer comments, recoverable archive operations, and audit logging.
- Open research classifications, nested sub-classifications, uploads, versioning, project links, and senior endorsement badges.
- Authenticated in-browser PDF/file viewing.
- Fast metadata search across accessible project documents and the company research library.
- SQLAlchemy 2 models and Alembic migrations for MySQL-compatible databases. No SQLite path is included.

## Technology

- Frontend: React 19, TypeScript, Vinext/Vite, Tailwind and shadcn components
- Backend: FastAPI, SQLAlchemy 2, Alembic, PyMySQL
- Database: MySQL 8.4 in Docker, or an existing MySQL server
- Authentication: signed JWT access tokens and Argon2 password hashes
- File storage: filesystem paths configured by `STORAGE_ROOT`; database rows store metadata, hashes, versions, and audit information

## Fastest start: Docker

Docker Desktop must be running.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Open `http://localhost:3000`. The API documentation is at `http://localhost:8000/api/docs`. The Docker MySQL service is exposed on host port `3307`, avoiding a typical existing MySQL service on `3306`.

Demo accounts all use password `verdant-demo`:

| Employee ID | Name | Demonstrates |
|---|---|---|
| `EMP-1042` | Ananya Rao | Project owner / senior approver |
| `EMP-1088` | Vikram Shah | Assigned reviewer |
| `EMP-1071` | Mira Nair | Responsible design employee |
| `VIS-1100` | Leela Thomas | Document-only visitor |

## Install on Windows without Docker

For a work laptop with an existing MySQL server, follow the dedicated [step-by-step local Windows installation guide](docs/LOCAL_INSTALLATION_WINDOWS.md). It covers prerequisites, MySQL setup, backend and frontend installation, migrations, demo data, startup, updates, and common errors.

## Understand and change the application

The [codebase and application guide](docs/CODEBASE_GUIDE.md) explains the architecture, important files, data and request flows, permissions, document workflow, API routes, current limitations, and where to make common changes.

## Use an existing MySQL server

Create a dedicated database and application user. Adapt the host, password, and account policy to your environment:

```sql
CREATE DATABASE verdant_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'verdant'@'localhost' IDENTIFIED BY 'verdant';
GRANT ALL PRIVILEGES ON verdant_app.* TO 'verdant'@'localhost';
```

Then prepare and start the backend:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
```

In another terminal, start React:

```powershell
Set-Location ..
npm ci
npm run dev
```

If your database is not on the development default, edit `backend/.env`:

```dotenv
DATABASE_URL=mysql+pymysql://user:password@host:3306/database?charset=utf8mb4
JWT_SECRET=use-a-long-random-production-secret
STORAGE_ROOT=C:/company/document-storage/verdant
```

## Database migrations

The checked-in initial migration creates the full schema. For a model change:

```powershell
Set-Location backend
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe the change"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe check
```

Review generated migrations before applying them to a shared company database. Back up production data before any destructive migration.

## Verification

```powershell
npm run build
Set-Location backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\alembic.exe check
```

The prototype has also been exercised against a live MySQL-compatible server through login, project dashboard reads, version upload, submission, reviewer start/approval, research listing, search, audit recording, and document-only visitor viewing.

## Repository publishing

This folder is already a Git repository. After choosing GitHub or GitLab and creating an empty remote repository, add that remote and push:

```powershell
git remote add origin <your-repository-url>
git push -u origin main
```

No remote is created or published automatically, so company code is not sent to an external service without an explicit decision.
