import logging
import os
import re
import secrets
from pathlib import Path

from dotenv import load_dotenv
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
    verify_password,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROOT_DIR = Path(__file__).resolve().parents[3]


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


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1)


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


@router.post("/google", response_model=AuthResponse)
def google_login(request: GoogleLoginRequest, session: SessionDep) -> AuthResponse:
    load_dotenv(ROOT_DIR / ".env", override=True)
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        )

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in dependency is not installed.",
        ) from exc

    try:
        profile = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            google_client_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify Google sign-in.",
        ) from exc

    email = str(profile.get("email", "")).strip().lower()
    email_verified = profile.get("email_verified")
    if not email or email_verified is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email could not be verified.",
        )

    user = get_user_by_email(session, email)
    if user is None:
        name = str(profile.get("name") or email.split("@")[0]).strip()
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
        )
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
        except Exception as exc:
            session.rollback()
            logger.exception("Failed to create Google-authenticated user")
            raise HTTPException(
                status_code=500,
                detail="Could not create Google account.",
            ) from exc

    token = create_access_token(user.id)  # type: ignore[arg-type]
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_current_user(
    request: ProfileUpdateRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> UserRead:
    current_user.name = request.name.strip()
    try:
        session.add(current_user)
        session.commit()
        session.refresh(current_user)
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to update user profile")
        raise HTTPException(status_code=500, detail="Could not update profile.") from exc

    return UserRead.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    request: ChangePasswordRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.hashed_password = hash_password(request.new_password)
    try:
        session.add(current_user)
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.exception("Failed to change password")
        raise HTTPException(status_code=500, detail="Could not change password.") from exc
