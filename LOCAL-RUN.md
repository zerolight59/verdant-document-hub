# Install and run Verdant locally

These commands work from any folder where you clone the repository. Docker is not required. The frontend, API, and PostgreSQL run on your own computer.

## First installation

Install Git, Python 3.12 or newer, Node.js 22.13 or newer, and PostgreSQL 16 or newer. During PostgreSQL installation, use port 5432 if available and remember the `postgres` administrator password. Start the PostgreSQL service.

```powershell
git clone --branch product-architecture-postgresql https://github.com/zerolight59/verdant-document-hub.git
cd verdant-document-hub
powershell -ExecutionPolicy Bypass -File .\Install-Verdant.ps1 -DemoData
powershell -ExecutionPolicy Bypass -File .\Start-Verdant.ps1
```

You need repository access if GitHub marks the repository private. Downloads require internet access during installation. Run the scripts from a writable checkout folder.

The installer creates `backend/.venv`, installs Python and frontend dependencies, creates local environment files with unique secrets, provisions the database, and applies Alembic migrations. Enter the PostgreSQL administrator password at the local prompt; it is not saved. Verdant itself uses the separate `verdant_app` database login.

`-DemoData` adds sample employees, Project X, and research documents only when the employee table is empty. Omit this switch if importing company employees using `docs/MYSQL_TO_POSTGRESQL_MIGRATION.md`. Without sample or imported employees there is no account to sign in with.

If PostgreSQL is not ready yet, run `Install-Verdant.ps1 -SkipDatabase` first. Later run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Setup-Database.ps1 -DemoData
```

Existing environment files, database role passwords, and employee records are preserved. If `verdant_app` already exists, put its correct password in `backend/.env`. For a different PostgreSQL host or port, edit that file and rerun `Setup-Database.ps1`.

## Open the app

Visit <http://localhost:3000>. Sample owner: `EMP-1042` / `verdant-demo`. Other sample accounts are in the full Windows installation guide. FastAPI documentation is at <http://localhost:8000/api/docs>.

The visual walkthrough is `output/pdf/Verdant-User-Guide.pdf`.

## Start again after restarting Windows

Start PostgreSQL, open PowerShell in your checkout folder, and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Start-Verdant.ps1
```

Both app processes run in the background and listen only on this computer. Repeated starts reuse processes launched by this checkout. If another application owns port 3000 or 8000, the helper reports it rather than stopping that application.

## Stop

```powershell
powershell -ExecutionPolicy Bypass -File .\Stop-Verdant.ps1
```

This stops the app processes launched by this checkout. PostgreSQL stays running.

## Settings, data, and logs

- `backend/.env`: database connection, JWT secret, storage path, and upload limit.
- `frontend/.env.local`: API address.
- `backend/storage/`: uploaded document files by default.
- `.local/`: app logs and process records.
- PostgreSQL: employees, projects, file metadata, review history, and audit records.

Settings, logs, dependencies, and uploaded files are ignored by Git. Back up the PostgreSQL database and uploaded files together. If you move an installed checkout, update `STORAGE_ROOT` in `backend/.env` and recreate its Python virtual environment.

For updates, back up your data, stop the app, pull the branch, rerun the installer without `-DemoData`, and start the app. Existing settings are preserved.

Full manual instructions and troubleshooting: `docs/LOCAL_INSTALLATION_WINDOWS.md`.
