from contextlib import asynccontextmanager
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import DDL, inspect, update

from . import models
from .config import ADMIN_EMAIL, ADMIN_PASSWORD, CATEGORIES, FRONTEND_ORIGIN, UPLOAD_DIR, validate_settings
from .database import Base, SessionLocal, engine
from .routers.api import router
from .security import hash_password

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def migrate_legacy_users():
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    missing = ("username", "role", "is_active", "updated_at")
    with engine.begin() as connection:
        for name in missing:
            if name not in columns:
                source = models.User.__table__.c[name]
                sql_type = source.type.compile(dialect=engine.dialect)
                connection.execute(DDL(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
        if "username" not in columns:
            rows = connection.execute(models.User.__table__.select()).mappings().all()
            for row in rows:
                suffix = f"_{row['id']}"
                local_part = row.get("email", "").split("@")[0] or f"user{row['id']}"
                username = re.sub(r"[^A-Za-z0-9_.-]", "_", local_part)[:40 - len(suffix)]
                connection.execute(
                    update(models.User.__table__).where(models.User.id == row["id"])
                    .values(username=f"{username}{suffix}")
                )
        connection.execute(
            update(models.User.__table__).where(models.User.__table__.c.role.is_(None))
            .values(role="user")
        )
        connection.execute(
            update(models.User.__table__).where(models.User.__table__.c.is_active.is_(None))
            .values(is_active=True)
        )
        connection.execute(
            update(models.User.__table__).where(models.User.__table__.c.updated_at.is_(None))
            .values(updated_at=models.func.now())
        )
    Base.metadata.create_all(bind=engine)


def initialize_database():
    migrate_legacy_users()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for name in CATEGORIES:
            if db.query(models.SkillCategory.id).filter(models.SkillCategory.name == name).first() is None:
                db.add(models.SkillCategory(name=name))
        db.commit()
        if ADMIN_EMAIL and ADMIN_PASSWORD and not db.query(models.User.id).filter(models.User.role == "admin").first():
            username = ADMIN_EMAIL.split("@")[0][:32]
            if db.query(models.User.id).filter(models.User.username == username).first():
                username = f"{username}_admin"
            admin = models.User(
                name=username, username=username, email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD), role="admin", is_active=True,
            )
            db.add(admin)
            db.flush()
            db.add(models.UserProfile(user_id=admin.id, full_name=username))
            db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_settings()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield


app = FastAPI(title="SkillSwap API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        body = exc.detail
    else:
        body = {"detail": exc.detail, "code": "request_error"}
    return JSONResponse(status_code=exc.status_code, content=body, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    messages = [error["msg"] for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": " ".join(messages), "code": "validation_error"})


@app.get("/")
def root():
    return {"message": "SkillSwap API is running"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(router, prefix="/api")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
