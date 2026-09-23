from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import SESSION_COOKIE, create_access_token, get_current_employee
from app.models import Employee
from app.schemas import EmployeeOut, LoginRequest
from app.services.auth_service import authenticate_employee
from app.services.login_limit_service import (
    check_login_limit,
    clear_account_failures,
    record_login_failure,
)
from app.services.project_service import employee_json

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if request.headers.get("origin") not in {None, settings.frontend_origin}:
        raise HTTPException(status_code=403, detail="Untrusted request origin")
    check_login_limit(request, payload.employee_code)
    employee = authenticate_employee(db, payload.employee_code, payload.password)
    if not employee:
        record_login_failure(request, payload.employee_code)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect employee ID, username, or password",
        )
    clear_account_failures(request, payload.employee_code)
    response.set_cookie(
        SESSION_COOKIE,
        create_access_token(employee.id),
        httponly=True,
        secure=settings.environment != "development",
        samesite="strict",
        max_age=settings.access_token_minutes * 60,
        path="/api",
    )
    response.headers["Cache-Control"] = "no-store"
    return {"employee": EmployeeOut.model_validate(employee)}


@router.post("/logout")
def logout(response: Response, _: Annotated[Employee, Depends(get_current_employee)]) -> dict:
    response.delete_cookie(SESSION_COOKIE, path="/api")
    return {"message": "Signed out"}


@router.get("/me", response_model=EmployeeOut)
def me(
    employee: Annotated[Employee, Depends(get_current_employee)],
) -> Employee:
    return employee


@router.get("/employees")
def employees(
    _: Annotated[Employee, Depends(get_current_employee)],
    db: Annotated[Session, Depends(get_db)],
) -> list[dict]:
    return [
        employee_json(employee)
        for employee in db.scalars(
            select(Employee).where(Employee.is_active.is_(True)).order_by(Employee.name)
        ).all()
    ]
