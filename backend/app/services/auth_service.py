from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import Employee


def authenticate_employee(db: Session, identifier: str, password: str) -> Employee | None:
    """Authenticate with either the employee code or Verdant username."""

    normalized = identifier.strip()
    employee = db.scalar(
        select(Employee).where(
            Employee.is_active.is_(True),
            or_(
                Employee.employee_code == normalized,
                Employee.username == normalized,
            ),
        )
    )
    if not employee or not verify_password(password, employee.password_hash):
        return None
    return employee
