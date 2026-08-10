import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from app.database import SessionDep
from app.models import User


ROOT_DIR = Path(__file__).resolve().parents[3]

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

_bearer_scheme = HTTPBearer(auto_error=False)


def _get_secret_key() -> str:
    load_dotenv(ROOT_DIR / ".env")
    secret_key = os.getenv("ATLAS_SECRET_KEY")
    if not secret_key:
        # Falls back to a fixed development key so the app still runs
        # without a .env file. Set ATLAS_SECRET_KEY in production.
        secret_key = "atlas-lite-dev-secret-key-change-me"

    return secret_key


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


class InvalidTokenError(Exception):
    pass


def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Token is missing a subject")

    try:
        return int(subject)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError("Token subject is not a valid user id") from exc


def get_user_by_email(session: Session, email: str) -> User | None:
    normalized_email = email.strip().lower()
    return session.exec(select(User).where(User.email == normalized_email)).first()


def authenticate_user(session: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(session, email)
    if user is None:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise unauthorized from exc

    user = session.get(User, user_id)
    if user is None:
        raise unauthorized

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]