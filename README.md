# Verdant Document Hub

Verdant is an internal company document-management product. It combines controlled project documentation with an open research library while keeping project planning outside the product boundary.

## Product capabilities

- Verdant-owned employee ID/username and password authentication with Argon2 hashes.
- Reusable lifecycle templates plus project-specific stages.
- Project membership with view, edit, review, and manage access.
- Document-specific sharing for visitors without exposing a complete project.
- One responsible employee and one different reviewer per required document.
- Immutable file versions and the workflow `Draft → Submitted → Under review → Changes requested → New version → Approved`.
- Reviewer comments, project-scoped audit history, recoverable archives, and SHA-256 file checksums.
- Nested research classifications, research versioning, project links, and administrator endorsement badges.
- Authenticated in-browser file viewing and metadata search.
- Streamed uploads with a configurable size limit and failed-transaction cleanup.

## Technology

- Frontend: React 19, TypeScript, Vinext/Vite, Tailwind, and shadcn/Base UI
- Backend: FastAPI, SQLAlchemy 2, Alembic, and Pydantic
- Database: PostgreSQL through psycopg
- Authentication: JWT access tokens and Argon2 password hashes
- File storage: a configured filesystem root; PostgreSQL stores metadata, paths, versions, and integrity hashes

Docker is not required and Docker configuration is not included on this branch.

## Install on Windows

Follow the [complete Docker-free Windows installation guide](docs/LOCAL_INSTALLATION_WINDOWS.md). It covers PostgreSQL, Python, Node.js, environment configuration, Alembic, optional demo data, startup, updates, and troubleshooting.

Demo accounts created by the optional seed all use password `verdant-demo`:

| Employee ID | Username | Demonstrates |
|---|---|---|
| `EMP-1042` | `ananya.rao` | Project owner and administrator |
| `EMP-1088` | `vikram.shah` | Assigned reviewer |
| `EMP-1071` | `mira.nair` | Responsible employee |
| `VIS-1100` | `leela.thomas` | Document-only visitor |

Do not seed a database that contains real company data.

## Repository structure

```text
verdant-document-hub/
├── backend/
│   ├── alembic/                 PostgreSQL schema migrations
│   ├── app/
│   │   ├── core/                Configuration, database, security
│   │   ├── models/              SQLAlchemy models by domain
│   │   ├── routers/             FastAPI HTTP endpoints
│   │   ├── schemas/             Pydantic API contracts by domain
│   │   ├── services/            Authentication, permissions, storage, audit
│   │   └── main.py              FastAPI entry point
│   ├── scripts/                 Demo seed and employee migration utilities
│   ├── tests/                   Backend quality checks
│   └── pyproject.toml           Python packages and tool configuration
├── frontend/
│   ├── app/                     React application and feature modules
│   ├── components/              Shared UI primitives
│   ├── public/                  Static browser assets
│   └── package.json             Frontend packages and commands
└── docs/                        Installation, architecture, and migration guides
```

## PostgreSQL configuration

Copy `backend/.env.example` to `backend/.env` and configure separate values:

```dotenv
VERDANT_DB_HOST=localhost
VERDANT_DB_PORT=5432
VERDANT_DB_USER=verdant_app
VERDANT_DB_PASSWORD=replace-with-a-strong-password
VERDANT_DB_NAME=verdant
VERDANT_DB_SSLMODE=prefer
```

The backend safely constructs the SQLAlchemy connection URL. It does not require a MySQL root password, a PostgreSQL administrator password, or a connection to the Calibration database.

Copy `frontend/.env.example` to `frontend/.env.local` to configure the browser API address.

## Start development services

Backend terminal:

```powershell
Set-Location backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:3000`. FastAPI documentation is at `http://localhost:8000/api/docs`.

## Database migrations

The PostgreSQL baseline is `0001_postgresql`. For a model change:

```powershell
Set-Location backend
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe the change"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe check
```

Review every generated migration before applying it. Back up PostgreSQL and the document-storage directory together before changing an important installation.

## Quality checks

```powershell
Set-Location frontend
npm run lint
npm run build

Set-Location ..\backend
.\.venv\Scripts\ruff.exe format --check app scripts tests alembic
.\.venv\Scripts\ruff.exe check app scripts tests alembic
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\alembic.exe upgrade head --sql
```

The final Alembic check generates PostgreSQL SQL without changing a database. `alembic check` should additionally be run against the configured PostgreSQL development database.

## Documentation

- [Codebase and application guide](docs/CODEBASE_GUIDE.md)
- [Docker-free Windows installation](docs/LOCAL_INSTALLATION_WINDOWS.md)
- [MySQL employee-table to PostgreSQL migration](docs/MYSQL_TO_POSTGRESQL_MIGRATION.md)
- [Database design review](docs/schema-notes.md)
- [Original database diagram](docs/original-database-diagram.svg)

## PostgreSQL and future embeddings

PostgreSQL is now the single product database. The current baseline does not require pgvector because embeddings and chunking are not implemented yet. When that feature is built, it should be introduced through a new Alembic migration with chunks tied to immutable document-version IDs. Embeddings remain derived, regeneratable data rather than the document source of truth.
