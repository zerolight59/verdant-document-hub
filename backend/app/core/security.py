from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Employee

from .config import settings
from .database import get_db

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login", auto_error=False)
SESSION_COOKIE = "verdant_session"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return password_hash.verify(password, hashed)
    except Exception:
        return False


def create_access_token(employee_id: int) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode(
        {"sub": str(employee_id), "exp": expires},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def get_current_employee(
    request: Request,
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Employee:
    if not token:
        token = request.cookies.get(SESSION_COOKIE)
        if token and request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("origin") != settings.frontend_origin:
                raise HTTPException(status_code=403, detail="Untrusted request origin")
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if not token:
            raise credentials_error
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        employee_id = int(payload.get("sub", ""))
    except (InvalidTokenError, ValueError):
        raise credentials_error from None

    employee = db.scalar(
        select(Employee).where(
            Employee.id == employee_id,
            Employee.is_active.is_(True),
        )
    )
    if not employee:
        raise credentials_error
    return employee
