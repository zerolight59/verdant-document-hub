from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_employee
from app.models import Employee
from app.schemas import EmployeeOut, LoginRequest, TokenOut
from app.services.auth_service import authenticate_employee

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenOut)
def login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    employee = authenticate_employee(db, payload.employee_code, payload.password)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee ID, username, or password",
        )
    return TokenOut(
        access_token=create_access_token(employee.id),
        employee=employee,
    )


@router.get("/me", response_model=EmployeeOut)
def me(
    employee: Annotated[Employee, Depends(get_current_employee)],
) -> Employee:
    return employee


@router.get("/employees", response_model=list[EmployeeOut])
def employees(
    _: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> list[Employee]:
    return list(
        db.scalars(
            select(Employee).where(Employee.is_active.is_(True)).order_by(Employee.name)
        ).all()
    )
