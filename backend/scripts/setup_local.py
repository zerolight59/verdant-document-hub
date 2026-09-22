"""Configure a local installation and provision its PostgreSQL database."""

import argparse
import getpass
import secrets
import subprocess
import sys
from pathlib import Path

import psycopg
from psycopg import sql

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent


def configure() -> None:
    env_path = BACKEND / ".env"
    if not env_path.exists():
        env_path.write_text(
            "APP_NAME=Verdant Document Hub\nENVIRONMENT=development\n"
            "VERDANT_DB_HOST=localhost\nVERDANT_DB_PORT=5432\n"
            "VERDANT_DB_USER=verdant_app\n"
            f"VERDANT_DB_PASSWORD={secrets.token_urlsafe(32)}\n"
            "VERDANT_DB_NAME=verdant\nVERDANT_DB_SSLMODE=prefer\n"
            f"JWT_SECRET={secrets.token_urlsafe(48)}\n"
            "FRONTEND_ORIGIN=http://localhost:3000\n"
            f"STORAGE_ROOT={(BACKEND / 'storage').as_posix()}\n"
            "MAX_UPLOAD_SIZE_MB=100\n",
            encoding="utf-8",
        )
    frontend_env = ROOT / "frontend" / ".env.local"
    if not frontend_env.exists():
        frontend_env.write_text("NEXT_PUBLIC_API_URL=http://localhost:8000/api\n", encoding="utf-8")
    (BACKEND / "storage").mkdir(exist_ok=True)
    print("Local environment files and document storage are ready. Existing settings preserved.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configure-only", action="store_true")
    parser.add_argument("--seed-demo", action="store_true")
    args = parser.parse_args()
    configure()
    if args.configure_only:
        return

    from app.core.config import settings

    connection_args = {
        "host": settings.verdant_db_host,
        "port": settings.verdant_db_port,
        "user": settings.verdant_db_user,
        "password": settings.verdant_db_password,
        "dbname": settings.verdant_db_name,
        "connect_timeout": 5,
    }
    try:
        with psycopg.connect(**connection_args):
            print("Verdant database connection verified.")
    except psycopg.OperationalError:
        print("Provisioning the local database. The administrator password is never saved.")
        admin_password = getpass.getpass("PostgreSQL postgres administrator password: ")
        with psycopg.connect(
            **{
                **connection_args,
                "user": "postgres",
                "password": admin_password,
                "dbname": "postgres",
            },
            autocommit=True,
        ) as conn:
            role_exists = conn.execute(
                "SELECT 1 FROM pg_roles WHERE rolname = %s", (settings.verdant_db_user,)
            ).fetchone()
            if not role_exists:
                conn.execute(
                    sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                        sql.Identifier(settings.verdant_db_user),
                        sql.Literal(settings.verdant_db_password),
                    )
                )
            database_exists = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s", (settings.verdant_db_name,)
            ).fetchone()
            if not database_exists:
                conn.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8'").format(
                        sql.Identifier(settings.verdant_db_name),
                        sql.Identifier(settings.verdant_db_user),
                    )
                )
        del admin_password
        with psycopg.connect(**connection_args):
            print("Verdant application login verified.")

    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True)
    if args.seed_demo:
        with psycopg.connect(**connection_args) as conn:
            employee_count = conn.execute("SELECT count(*) FROM employees").fetchone()[0]
        if employee_count == 0:
            subprocess.run([sys.executable, "-m", "scripts.seed_demo"], cwd=BACKEND, check=True)
        else:
            print("Employees already exist; skipping demo seed to preserve existing data.")
    print("Database setup complete. Run Start-Verdant.ps1 from the project folder.")


if __name__ == "__main__":
    main()
