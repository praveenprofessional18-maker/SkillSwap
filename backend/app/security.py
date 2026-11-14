from datetime import datetime, timedelta, timezone
import secrets

import bcrypt
import jwt

from .config import JWT_EXPIRE_MINUTES, JWT_SECRET

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int) -> str:
    expiry = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expiry, "jti": secrets.token_urlsafe(16)},
        JWT_SECRET,
        algorithm=ALGORITHM,
    )
