import logging
import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import SessionDep
from app.models import User
from app.services.auth import (
    CurrentUser,
    authenticate_user,
    create_access_token,
    get_user_by_email,
    hash_password,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(value: str) -> str:
    cleaned = value.strip().lower()
    if not _EMAIL_PATTERN.match(cleaned):
        raise ValueError("Enter a valid email address.")

    return cleaned


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, session: SessionDep) -> AuthResponse:
    normalized_email = request.email.strip().lower()

    existing_user = get_user_by_email(session, normalized_email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=request.name.strip(),
        email=normalized_email,
        hashed_password=hash_password(request.password),
    )

    try:
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to register user")
        raise HTTPException(
            status_code=500,
            detail="Could not create account.",
        ) from exc

    token = create_access_token(user.id)  # type: ignore[arg-type]
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, session: SessionDep) -> AuthResponse:
    user = authenticate_user(session, request.email, request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token(user.id)  # type: ignore[arg-type]
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)