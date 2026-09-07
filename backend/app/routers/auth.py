from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Employee
from ..schemas import EmployeeOut, LoginRequest, TokenOut
from ..security import create_access_token, get_current_employee, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    employee = db.scalar(select(Employee).where(Employee.employee_code == payload.employee_code, Employee.is_active.is_(True)))
    if not employee or not verify_password(payload.password, employee.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect employee ID or password")
    return TokenOut(access_token=create_access_token(employee.id), employee=employee)


@router.get("/me", response_model=EmployeeOut)
def me(employee: Annotated[Employee, Depends(get_current_employee)]):
    return employee


@router.get("/employees", response_model=list[EmployeeOut])
def employees(_: Annotated[Employee, Depends(get_current_employee)], db: Annotated[Session, Depends(get_db)]):
    return db.scalars(select(Employee).where(Employee.is_active.is_(True)).order_by(Employee.name)).all()
