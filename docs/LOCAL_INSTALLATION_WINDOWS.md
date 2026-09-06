# Local Windows Installation (PostgreSQL, No Docker)

This guide installs Verdant directly on a Windows laptop using PostgreSQL. Docker is not required and no Docker files are used.

The examples use PowerShell and `C:\Work\verdant-document-hub`. Replace that path when your company uses another approved location.

## 1. Required software

Install or ask IT to install:

- Git for Windows
- Python 3.12 or newer
- Node.js 22.13 or newer; Node.js 22 LTS is recommended
- PostgreSQL 16 or newer
- pgAdmin 4 or the PostgreSQL `psql` command-line client

Confirm the development tools in PowerShell:

```powershell
git --version
python --version
node --version
npm --version
psql --version
```

`psql` may not be on `PATH` even when PostgreSQL and pgAdmin are installed. You can perform the database steps in pgAdmin instead. If `python` is unavailable but the Python launcher exists, use `py -3.12` in the virtual-environment command.

## 2. Download the product branch

```powershell
New-Item -ItemType Directory -Force C:\Work
Set-Location C:\Work
git clone https://github.com/zerolight59/verdant-document-hub.git
Set-Location verdant-document-hub
git switch product-architecture-postgresql
```

The repository is private. Git may open a browser for GitHub sign-in, and your GitHub account must have access. After this branch is merged into the default branch, the final `git switch` command will no longer be necessary.

## 3. Create the PostgreSQL role and database

The PostgreSQL Windows service must be running. You can inspect it with:

```powershell
Get-Service postgresql*
```

Open pgAdmin, connect to the PostgreSQL server with an administrator account, and open the Query Tool for the default `postgres` database.

Create a dedicated Verdant login role:

```sql
CREATE ROLE verdant_app
    WITH LOGIN
    PASSWORD 'replace-with-a-strong-company-password';
```

Create the database in a separate Query Tool execution:

```sql
CREATE DATABASE verdant
    WITH OWNER = verdant_app
    ENCODING = 'UTF8';
```

The PostgreSQL administrator password is used only by you or your database administrator for server administration. Do not put it in Verdant’s `.env`. Verdant uses only the limited `verdant_app` login.

For a company-hosted PostgreSQL server, ask the database administrator for:

- server hostname or IP address;
- port, normally `5432`;
- Verdant database name;
- limited application username and password;
- required SSL mode; and
- firewall permission from the application laptop/server.

## 4. Create the document-storage directory

```powershell
New-Item -ItemType Directory -Force C:\VerdantData\documents
```

The Windows account that starts FastAPI must have read and write access. PostgreSQL contains file metadata and history; this directory contains the actual file bytes. Back up both as one system.

## 5. Configure and install the backend

```powershell
Set-Location C:\Work\verdant-document-hub\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
```

Generate the JWT signing secret:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Open `C:\Work\verdant-document-hub\backend\.env` and configure it:

```dotenv
APP_NAME=Verdant Document Hub
ENVIRONMENT=development

VERDANT_DB_HOST=localhost
VERDANT_DB_PORT=5432
VERDANT_DB_USER=verdant_app
VERDANT_DB_PASSWORD=replace-with-a-strong-company-password
VERDANT_DB_NAME=verdant
VERDANT_DB_SSLMODE=prefer

JWT_SECRET=paste-the-generated-secret-here
ACCESS_TOKEN_MINUTES=480
FRONTEND_ORIGIN=http://localhost:3000

STORAGE_ROOT=C:/VerdantData/documents
MAX_UPLOAD_SIZE_MB=100
```

Separate database variables are used intentionally. The application safely constructs the PostgreSQL URL, including passwords containing special characters.

Use `VERDANT_DB_SSLMODE=require` when the company database requires encrypted connections. Follow the database administrator’s certificate requirements for a production installation.

## 6. Create the PostgreSQL schema

Keep PowerShell in the `backend` directory:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

The current revision should be `0001_postgresql`.

If you are importing the existing MySQL Verdant employee table, stop here and follow [Moving Verdant Employees from MySQL to PostgreSQL](MYSQL_TO_POSTGRESQL_MIGRATION.md). Do not seed real company data.

## 7. Optional demonstration data

For an empty demonstration installation only:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed_demo
```

The seed creates Project X and these accounts, all with password `verdant-demo`:

| Employee ID | Username | Role shown |
|---|---|---|
| `EMP-1042` | `ananya.rao` | Project owner and administrator |
| `EMP-1088` | `vikram.shah` | Reviewer |
| `EMP-1071` | `mira.nair` | Responsible employee |
| `VIS-1100` | `leela.thomas` | Document-only visitor |

## 8. Start FastAPI

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Leave this PowerShell window open. Verify:

- Service status: `http://localhost:8000/api/health`
- Interactive API documentation: `http://localhost:8000/api/docs`

## 9. Configure and start React

Open a second PowerShell window:

```powershell
Set-Location C:\Work\verdant-document-hub\frontend
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Leave the window open and visit `http://localhost:3000`.

## 10. Acceptance check

1. Sign in using an employee ID or username.
2. Create or open a project.
3. Verify lifecycle stages and required documents.
4. Upload a document version and preview it in the browser.
5. Submit it as the responsible employee.
6. Start and decide the review as the assigned reviewer.
7. Confirm project activity contains the upload, submission, and review actions.
8. Upload and view a research document.
9. Confirm an unauthorized employee cannot access another project.
10. Confirm PostgreSQL records and `C:\VerdantData\documents` files are both present.

## Start Verdant again later

Start PostgreSQL first, then use two PowerShell windows.

Backend:

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location C:\Work\verdant-document-hub\frontend
npm run dev
```

Open `http://localhost:3000`.

## Run the frontend in production mode locally

Build after every frontend code change:

```powershell
Set-Location C:\Work\verdant-document-hub\frontend
npm ci
npm run build
npm run start
```

Run FastAPI without `--reload` for a stable product process. A company-wide deployment also needs approved process supervision, HTTPS, network/firewall configuration, monitoring, and backups.

## Update an installation

Back up PostgreSQL and the document-storage directory first. Then:

```powershell
Set-Location C:\Work\verdant-document-hub
git pull

Set-Location backend
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\alembic.exe upgrade head

Set-Location ..\frontend
npm ci
npm run build
```

Restart both services after updating.

## Quality checks

Backend:

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\ruff.exe format --check app scripts tests alembic
.\.venv\Scripts\ruff.exe check app scripts tests alembic
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\alembic.exe check
```

Frontend:

```powershell
Set-Location C:\Work\verdant-document-hub\frontend
npm run lint
npm run build
```

`alembic check` connects to the configured PostgreSQL database. Run it against a development database rather than production during ordinary development.

## Common problems

### `python` is not recognized

Install Python with **Add Python to PATH** selected, or use:

```powershell
py -3.12 -m venv .venv
```

### `psql` is not recognized

Use pgAdmin, or add the PostgreSQL `bin` directory to your user `PATH`. A normal location resembles `C:\Program Files\PostgreSQL\16\bin`.

### Connection refused

Confirm the PostgreSQL service is running, the hostname and port are correct, and company firewall rules allow the connection.

### Password authentication failed

Check `VERDANT_DB_USER` and `VERDANT_DB_PASSWORD`. Verify the PostgreSQL role can connect to the selected database. Do not substitute the server administrator password.

### `no pg_hba.conf entry`

The PostgreSQL server does not allow the laptop’s address or selected authentication method. Ask the database administrator to add an approved rule; do not weaken authentication globally.

### Alembic reports that a table already exists

Do not delete tables blindly. Confirm whether the database is empty, whether it came from MySQL, and whether an Alembic version record exists. Back up the database before repairing migration state.

### Frontend cannot reach FastAPI

Confirm both windows are running. `backend/.env` must contain `FRONTEND_ORIGIN=http://localhost:3000`, while `frontend/.env.local` must contain `NEXT_PUBLIC_API_URL=http://localhost:8000/api`. Restart both services after changing environment files.

### File upload is rejected as too large

Increase `MAX_UPLOAD_SIZE_MB` only after checking server memory, storage capacity, reverse-proxy limits, and company policy.

### Files upload but cannot be viewed

Confirm `STORAGE_ROOT` exists and that the Windows account running FastAPI has read and write permission.

### Package installation fails on a managed laptop

A corporate proxy, certificate, or package policy may block Python or npm downloads. Ask IT for the approved proxy/certificate or internal package source. Do not disable TLS certificate verification.

## Network deployment boundary

Binding FastAPI to `127.0.0.1` limits it to the laptop. Before allowing other employees to connect, use an approved HTTPS reverse proxy, a production process manager/service account, firewall rules, database TLS, secrets management, centralized logs, monitoring, database backups, document-storage backups, restore testing, and a company security review.

PostgreSQL makes a later pgvector migration possible, but pgvector is not required for this version. Add it only with the embedding/chunking feature and a reviewed Alembic migration.
