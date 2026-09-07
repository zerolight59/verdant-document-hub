# Local Windows Installation (No Docker)

This guide installs Verdant directly on a Windows work laptop using MySQL. Docker is not required.

The commands use PowerShell. Replace `C:\Work` if your company uses another folder.

## 1. Install the prerequisites

Install or ask IT to install:

- Git for Windows
- Python 3.12 or newer
- Node.js 22.13 or newer (Node.js 22 LTS is recommended)
- MySQL Server 8.x and MySQL Workbench or the MySQL command-line client

Confirm them in PowerShell:

```powershell
git --version
python --version
node --version
npm --version
mysql --version
```

If `python` is not recognized but the Python launcher is installed, use `py -3.12` instead of `python` when creating the virtual environment.

Use a dedicated prototype database. Do not point the prototype or its demo-data script at a production company database.

## 2. Download Verdant

```powershell
New-Item -ItemType Directory -Force C:\Work
Set-Location C:\Work
git clone https://github.com/zerolight59/verdant-document-hub.git
Set-Location verdant-document-hub
```

The repository is private, so Git may open a browser and ask you to sign in. Your GitHub account must have repository access. GitHub Desktop can also clone it.

## 3. Create the MySQL database

Check that the MySQL Windows service is running:

```powershell
Get-Service MySQL*
```

Open MySQL Workbench, connect as an administrator, and run:

```sql
CREATE DATABASE IF NOT EXISTS verdant_app
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'verdant_app_user'@'localhost'
  IDENTIFIED BY 'VerdantLocal_2026';

GRANT ALL PRIVILEGES ON verdant_app.*
  TO 'verdant_app_user'@'localhost';

FLUSH PRIVILEGES;
```

The password is only a local example. Use a company-approved password for a real installation. URL-encode characters such as `@`, `:`, `/`, `?`, or `#` when placing a password in `DATABASE_URL`.

If you cannot create databases or users, ask your database administrator to create `verdant_app` and provide an account with full privileges on it.

## 4. Create document storage

```powershell
New-Item -ItemType Directory -Force C:\VerdantData\documents
```

The Windows account starting the backend needs read and write access to this folder. A company file-server path can be used later if its permissions allow the backend account to create, read, and update files.

## 5. Install and configure FastAPI

```powershell
Set-Location C:\Work\verdant-document-hub\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
Copy-Item .env.example .env
```

Generate a random signing secret:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the result. Open `C:\Work\verdant-document-hub\backend\.env` and set:

```dotenv
DATABASE_URL=mysql+pymysql://verdant_app_user:VerdantLocal_2026@localhost:3306/verdant_app?charset=utf8mb4
JWT_SECRET=paste-the-generated-secret-here
FRONTEND_ORIGIN=http://localhost:3000
STORAGE_ROOT=C:/VerdantData/documents
```

Use forward slashes in `STORAGE_ROOT`. If MySQL uses another computer or port, replace `localhost:3306` with the value supplied by your database administrator.

## 6. Create the database tables with Alembic

Keep PowerShell in the `backend` folder and run:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

The migration should finish without an error. Alembic records the installed database version and applies future schema changes in order.

## 7. Add prototype demo data

For the first demonstration, run:

```powershell
.\.venv\Scripts\python.exe seed.py
```

This creates Project X and the following accounts. Every demo account uses password `verdant-demo`.

| Employee ID | Demonstrates |
|---|---|
| `EMP-1042` | Project owner and senior approver |
| `EMP-1088` | Assigned reviewer |
| `EMP-1071` | Responsible employee |
| `VIS-1100` | Document-only visitor |

Seeding is optional after the prototype phase. Never run the demo seed against a real company database.

## 8. Start FastAPI

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Leave this window open. Verify the backend:

- API status: `http://localhost:8000/api/health`
- API documentation: `http://localhost:8000/api/docs`

## 9. Install and start React

Open a second PowerShell window:

```powershell
Set-Location C:\Work\verdant-document-hub
npm ci
Set-Content .env.local 'NEXT_PUBLIC_API_URL=http://localhost:8000/api'
npm run dev
```

Leave this window open, visit `http://localhost:3000`, and sign in with a demo account.

## 10. Check the prototype

1. Sign in as `EMP-1042` and open Project X.
2. View its lifecycle stages, required documents, assignments, and permissions.
3. Upload a version and move it into review.
4. Sign in as `EMP-1088` to review it, request changes, or approve it.
5. Upload a research file, search for it, and preview it inside the application.
6. Open audit history and confirm the actions were recorded.

## Start Verdant again later

Start MySQL, then open two PowerShell windows.

Backend:

```powershell
Set-Location C:\Work\verdant-document-hub\backend
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location C:\Work\verdant-document-hub
npm run dev
```

Open `http://localhost:3000`.

## Update the installation

Back up the MySQL database and document-storage folder before updating an important installation. Then run:

```powershell
Set-Location C:\Work\verdant-document-hub
git pull
npm ci
Set-Location backend
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\alembic.exe upgrade head
```

Restart the backend and frontend afterward.

## Common problems

### `python` is not recognized

Install Python with **Add Python to PATH** enabled, or create the environment with `py -3.12 -m venv .venv`.

### MySQL connection refused

Confirm the MySQL service is running, its port is correct, and `DATABASE_URL` points to the right host. The normal local port is `3306`.

### MySQL access denied

Check the username and password in `backend\.env`. Confirm the user has privileges on `verdant_app` and its allowed host matches the connection host.

### The frontend cannot reach FastAPI

Keep both windows running. Confirm `FRONTEND_ORIGIN=http://localhost:3000` and `.env.local` contains `NEXT_PUBLIC_API_URL=http://localhost:8000/api`. Restart both applications after changing an environment file.

### Port 3000 or 8000 is already in use

```powershell
Get-NetTCPConnection -LocalPort 3000
Get-NetTCPConnection -LocalPort 8000
```

Stop the conflicting program, or use another port and update the matching URLs in both environment files.

### Files upload but cannot be viewed

Confirm `STORAGE_ROOT` exists and that the Windows account running FastAPI has read and write permission for it.

### Installation downloads fail on a managed laptop

A corporate proxy, certificate, or software policy may block Python or npm downloads. Ask IT to configure the approved proxy/certificate or provide the packages internally. Do not disable TLS certificate checks.

## Local-demo security boundary

Binding FastAPI to `127.0.0.1` limits the prototype to that laptop. Before sharing it over the company network, add an approved HTTPS reverse proxy, production process supervision, firewall rules, backups, secrets management, and a company security review.
