import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .database import Base, engine, get_db
from .models import User, SkillPost, Exchange
from .schemas import RegisterIn, LoginIn, PostCreate, ExchangeCreate, ExchangeDecision
from .auth import hash_password, verify_password, create_access_token, get_current_user

Base.metadata.create_all(bind=engine)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SkillSwap API", version="0.1.0")
origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5500")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin, "http://127.0.0.1:5500", "http://localhost:8000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

@app.get("/")
def root():
    return {"message": "SkillSwap API is running"}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/register", status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email}

@app.post("/api/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@app.get("/api/profile")
def profile(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email}

@app.post("/api/posts", status_code=201)
def create_post(data: PostCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = SkillPost(user_id=user.id, **data.model_dump())
    db.add(post); db.commit(); db.refresh(post)
    return {"id": post.id, "message": "Post created"}

@app.get("/api/posts")
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(SkillPost).order_by(SkillPost.id.desc()).all()
    return [{
        "id": p.id, "user_id": p.user_id, "title": p.title,
        "description": p.description, "skill_name": p.skill_name,
        "category": p.category, "media_url": p.media_url,
        "media_type": p.media_type
    } for p in posts]

@app.post("/api/posts/{post_id}/media")
async def upload_post_media(post_id: int, file: UploadFile = File(...),
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.query(SkillPost).filter(SkillPost.id == post_id, SkillPost.user_id == user.id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    allowed = {".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image", ".mp4": "video"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(400, "Only JPG, JPEG, PNG, WEBP and MP4 files are allowed")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Maximum upload size is 10 MB")
    safe_name = f"user{user.id}_post{post.id}_{int(datetime.now().timestamp())}{ext}"
    (UPLOAD_DIR / safe_name).write_bytes(content)
    post.media_url = f"/uploads/{safe_name}"
    post.media_type = allowed[ext]
    db.commit()
    return {"media_url": post.media_url, "media_type": post.media_type}

@app.post("/api/exchanges", status_code=201)
def create_exchange(data: ExchangeCreate, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    if data.receiver_id == user.id:
        raise HTTPException(400, "You cannot exchange skills with yourself")
    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not receiver:
        raise HTTPException(404, "Receiver not found")
    existing = db.query(Exchange).filter(
        Exchange.requester_id == user.id,
        Exchange.receiver_id == data.receiver_id,
        Exchange.offered_skill == data.offered_skill,
        Exchange.requested_skill == data.requested_skill,
        Exchange.status.in_(["pending", "accepted"])
    ).first()
    if existing:
        raise HTTPException(409, "An active or pending matching exchange already exists")
    exchange = Exchange(requester_id=user.id, receiver_id=data.receiver_id,
        offered_skill=data.offered_skill, requested_skill=data.requested_skill,
        duration_days=data.duration_days)
    db.add(exchange); db.commit(); db.refresh(exchange)
    return {"id": exchange.id, "status": exchange.status}

@app.get("/api/exchanges")
def list_exchanges(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Exchange).filter(
        or_(Exchange.requester_id == user.id, Exchange.receiver_id == user.id)
    ).order_by(Exchange.id.desc()).all()
    return [{
        "id": x.id, "requester_id": x.requester_id, "receiver_id": x.receiver_id,
        "offered_skill": x.offered_skill, "requested_skill": x.requested_skill,
        "duration_days": x.duration_days, "status": x.status,
        "repeat_count": x.repeat_count, "start_date": x.start_date, "end_date": x.end_date
    } for x in rows]

@app.patch("/api/exchanges/{exchange_id}")
def decide_exchange(exchange_id: int, data: ExchangeDecision,
                    db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exchange = db.query(Exchange).filter(Exchange.id == exchange_id).first()
    if not exchange:
        raise HTTPException(404, "Exchange not found")
    if exchange.receiver_id != user.id:
        raise HTTPException(403, "Only the receiver can respond to this request")
    if exchange.status != "pending":
        raise HTTPException(409, "This request is no longer pending")
    if data.status == "accepted":
        now = datetime.now(timezone.utc)
        exchange.status = "accepted"
        exchange.start_date = now
        exchange.end_date = now + timedelta(days=exchange.duration_days)
    elif data.status == "rejected":
        exchange.status = "rejected"
    else:
        raise HTTPException(400, "Status must be accepted or rejected")
    db.commit()
    return {"id": exchange.id, "status": exchange.status}
