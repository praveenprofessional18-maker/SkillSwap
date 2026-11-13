import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillswap.db")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5500").strip()
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads")).resolve()
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_MB", "5")) * 1024 * 1024
MAX_VIDEO_BYTES = int(os.getenv("MAX_VIDEO_MB", "50")) * 1024 * 1024
MAX_EXCHANGES_PER_COMBINATION = int(os.getenv("MAX_EXCHANGES_PER_COMBINATION", "2"))
RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
CATEGORIES = (
    "Programming", "Cybersecurity", "Web Development", "Mobile Development",
    "UI/UX Design", "Graphic Design", "Video Editing", "Digital Marketing",
    "Communication", "Business", "Other",
)


def validate_settings():
    if len(JWT_SECRET) < 32:
        raise RuntimeError("JWT_SECRET must be set and contain at least 32 characters")
    if JWT_EXPIRE_MINUTES < 1:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be a positive integer")
    if MAX_EXCHANGES_PER_COMBINATION != 2:
        raise RuntimeError("MAX_EXCHANGES_PER_COMBINATION is fixed at 2 by the exchange rules")
