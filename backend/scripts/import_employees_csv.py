"""Import the existing Verdant employee table into PostgreSQL from a CSV export."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from sqlalchemy import func, select, text

from app.core.database import SessionLocal
from app.models import Employee

REQUIRED_COLUMNS = {"employee_code", "name", "email", "password_hash"}


def parse_bool(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_profile(value: str | None) -> dict[str, Any]:
    if not value or not value.strip():
        return {}
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("profile_data must contain a JSON object")
    return parsed


def employee_values(row: dict[str, str]) -> dict[str, Any]:
    values: dict[str, Any] = {
        "employee_code": row["employee_code"].strip(),
        "username": (row.get("username") or "").strip() or None,
        "name": row["name"].strip(),
        "email": row["email"].strip(),
        "password_hash": row["password_hash"].strip(),
        "job_title": (row.get("job_title") or "Employee").strip() or "Employee",
        "department": (row.get("department") or "").strip() or None,
        "profile_data": parse_profile(row.get("profile_data")),
        "is_admin": parse_bool(row.get("is_admin"), False),
        "is_active": parse_bool(row.get("is_active"), True),
    }
    source_id = (row.get("id") or "").strip()
    if source_id:
        values["id"] = int(source_id)
    return values


def import_employees(csv_path: Path, dry_run: bool = False) -> tuple[int, int]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError("CSV is missing required columns: " + ", ".join(sorted(missing)))
        rows = list(reader)

    inserted = 0
    updated = 0
    with SessionLocal() as db:
        for row_number, row in enumerate(rows, start=2):
            try:
                values = employee_values(row)
            except Exception as exc:
                raise ValueError(f"Invalid employee row {row_number}: {exc}") from exc

            existing = db.scalar(
                select(Employee).where(Employee.employee_code == values["employee_code"])
            )
            if existing:
                values.pop("id", None)
                for key, value in values.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(Employee(**values))
                inserted += 1

        if dry_run:
            db.rollback()
            return inserted, updated

        db.flush()
        maximum_id = db.scalar(select(func.max(Employee.id))) or 1
        db.execute(
            text("SELECT setval(pg_get_serial_sequence('employees', 'id'), :maximum_id, true)"),
            {"maximum_id": maximum_id},
        )
        db.commit()
    return inserted, updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import a MySQL Verdant employee-table CSV into PostgreSQL."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and report without committing database changes.",
    )
    args = parser.parse_args()
    inserted, updated = import_employees(args.csv_path, args.dry_run)
    mode = "validated" if args.dry_run else "imported"
    print(f"Employees {mode}: {inserted} new, {updated} updated")


if __name__ == "__main__":
    main()
