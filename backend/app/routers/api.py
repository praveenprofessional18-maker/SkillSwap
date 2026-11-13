import re
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import CATEGORIES, RATE_LIMIT_AUTH, UPLOAD_DIR
from ..database import get_db
from ..dependencies import get_current_user, get_optional_user, require_admin
from ..models import (
    Comment, ExchangeRequest, Like, Notification, Post, PostMedia, Report, Skill,
    SkillCategory, SkillExchange, User, UserLearningSkill, UserProfile, user_teaching_skills,
)
from ..schemas import (
    CommentCreate, ExchangeCreate, ExchangeDuration, LearningSkillCreate, LikeAction, LoginIn,
    PostCreate, ProfileUpdate, RegisterIn, ReportCreate, ReportResolve, SkillCreate,
    UserStatusUpdate,
)
from ..security import create_access_token, hash_password, verify_password
from ..services.exchange_service import (
    accept_request, combination, counter_request, create_request, exchange_view,
    get_participant_request, maybe_notify_near_end, remaining_days, request_view,
)
from ..services.notification_service import notify
from ..services.upload_service import store_upload

router = APIRouter()
auth_attempts = defaultdict(deque)
try:
    limit_count, limit_period = RATE_LIMIT_AUTH.lower().split("/", 1)
    AUTH_LIMIT = int(limit_count)
    AUTH_WINDOW_SECONDS = {"second": 1, "minute": 60, "hour": 3600}[limit_period.rstrip("s")]
    if AUTH_LIMIT < 1:
        raise ValueError
except (ValueError, KeyError):
    raise RuntimeError("RATE_LIMIT_AUTH must use a positive count and second, minute, or hour period")


def rate_limit(request: Request):
    key = request.client.host if request.client else "unknown"
    now = time.monotonic()
    attempts = auth_attempts[key]
    while attempts and now - attempts[0] > AUTH_WINDOW_SECONDS:
        attempts.popleft()
    if len(attempts) >= AUTH_LIMIT:
        raise HTTPException(429, detail={"detail": "Too many authentication attempts; try again shortly", "code": "rate_limited"})
    attempts.append(now)


def page_query(query, page, page_size):
    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def page_result(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def profile_dict(db, user, include_email=False):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    result = {
        "id": user.id, "username": user.username, "name": user.name,
        "role": user.role, "created_at": user.created_at,
        "full_name": profile.full_name if profile else user.name,
        "profile_image": profile.profile_image if profile else None,
        "bio": profile.bio if profile else "", "location": profile.location if profile else "",
        "experience_level": profile.experience_level if profile else "Beginner",
        "availability": profile.availability if profile else "",
        "language": profile.language if profile else "",
        "social_links": profile.social_links if profile else {},
    }
    if include_email:
        result["email"] = user.email
    return result


def post_dict(db, post, viewer_id=None):
    return {
        "id": post.id, "author_id": post.author_id,
        "author": db.query(User.username).filter(User.id == post.author_id).scalar(),
        "content": post.content, "created_at": post.created_at, "updated_at": post.updated_at,
        "media": [
            {"id": media.id, "url": f"/uploads/{media.file_path}", "media_type": media.media_type,
             "size_bytes": media.size_bytes}
            for media in db.query(PostMedia).filter(PostMedia.post_id == post.id).all()
        ],
        "like_count": db.query(Like).filter(Like.post_id == post.id).count(),
        "comment_count": db.query(Comment).filter(Comment.post_id == post.id).count(),
        "liked": bool(viewer_id and db.query(Like.id).filter(
            Like.post_id == post.id, Like.user_id == viewer_id).first()),
    }


@router.post("/auth/register", status_code=201, tags=["auth"], dependencies=[Depends(rate_limit)])
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User.id).filter(or_(User.email == data.email.lower(), User.username == data.username)).first():
        raise HTTPException(409, detail={"detail": "Email or username already registered", "code": "account_exists"})
    name = (data.full_name or data.name or data.username).strip()
    user = User(name=name, username=data.username, email=data.email.lower(), password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.flush()
        db.add(UserProfile(user_id=user.id, full_name=name, language=data.language))
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"detail": "Email or username already registered", "code": "account_exists"})
    return {"id": user.id, "username": user.username, "name": user.name, "email": user.email}


@router.post("/auth/login", tags=["auth"], dependencies=[Depends(rate_limit)])
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user is None or not verify_password(data.password, user.password_hash) or not user.is_active:
        raise HTTPException(401, detail={"detail": "Invalid email or password", "code": "invalid_credentials"})
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return profile_dict(db, user, include_email=True)


@router.get("/users", tags=["users"])
def list_users(
    q: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(User).filter(User.is_active.is_(True))
    if q.strip():
        search = f"%{q.strip()}%"
        query = query.filter(or_(User.username.ilike(search), User.name.ilike(search)))
    rows, total = page_query(query.order_by(User.username), page, page_size)
    return page_result([profile_dict(db, item) for item in rows], total, page, page_size)


@router.get("/users/me/profile", tags=["users"])
def my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return profile_dict(db, user, include_email=True)


@router.put("/users/me", tags=["users"])
def update_profile(data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if profile is None:
        profile = UserProfile(user_id=user.id, full_name=user.name)
        db.add(profile)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    if data.full_name is not None:
        user.name = data.full_name
    db.commit()
    db.refresh(profile)
    return profile_dict(db, user, include_email=True)


@router.get("/users/{user_id}", tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    found = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if found is None:
        raise HTTPException(404, detail={"detail": "User not found", "code": "not_found"})
    return profile_dict(db, found, include_email=found.id == user.id)


@router.get("/skills/categories", tags=["skills"])
def list_categories(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = page_query(db.query(SkillCategory).order_by(SkillCategory.name), page, page_size)
    return page_result([{"id": row.id, "name": row.name} for row in rows], total, page, page_size)


@router.get("/skills", tags=["skills"])
def list_skills(
    q: str = "", category: str | None = None, category_id: int | None = None,
    level: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Skill, SkillCategory.name.label("category_name"), User.username).join(
        SkillCategory, Skill.category_id == SkillCategory.id).join(User, Skill.owner_id == User.id).filter(User.is_active.is_(True))
    if q.strip():
        query = query.filter(Skill.name.ilike(f"%{q.strip()}%"))
    if category_id:
        query = query.filter(Skill.category_id == category_id)
    if category:
        query = query.filter(SkillCategory.name.ilike(category))
    if level:
        query = query.filter(Skill.experience_level == level)
    total = query.count()
    rows = query.order_by(Skill.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return page_result([
        {"id": s.id, "owner_id": s.owner_id, "owner_username": username, "name": s.name,
         "category_id": s.category_id, "category": cat, "description": s.description,
         "experience_level": s.experience_level, "created_at": s.created_at}
        for s, cat, username in rows
    ], total, page, page_size)


@router.post("/skills", status_code=201, tags=["skills"])
def create_skill(data: SkillCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(SkillCategory.id).filter(SkillCategory.id == data.category_id).first() is None:
        raise HTTPException(422, detail={"detail": "Unknown skill category", "code": "invalid_category"})
    skill = Skill(owner_id=user.id, **data.model_dump())
    db.add(skill)
    db.flush()
    db.execute(user_teaching_skills.insert().values(user_id=user.id, skill_id=skill.id))
    db.commit()
    db.refresh(skill)
    return {"id": skill.id, **data.model_dump(), "owner_id": user.id}


@router.get("/skills/{skill_id}", tags=["skills"])
def get_skill(skill_id: int, db: Session = Depends(get_db)):
    row = db.query(Skill, SkillCategory.name, User.username).join(SkillCategory).join(User).filter(Skill.id == skill_id).first()
    if row is None:
        raise HTTPException(404, detail={"detail": "Skill not found", "code": "not_found"})
    skill, category, username = row
    return {"id": skill.id, "owner_id": skill.owner_id, "owner_username": username, "name": skill.name,
            "category_id": skill.category_id, "category": category, "description": skill.description,
            "experience_level": skill.experience_level, "created_at": skill.created_at}


@router.put("/skills/{skill_id}", tags=["skills"])
def update_skill(skill_id: int, data: SkillCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.owner_id == user.id).first()
    if skill is None:
        raise HTTPException(404, detail={"detail": "Skill not found", "code": "not_found"})
    if db.query(SkillCategory.id).filter(SkillCategory.id == data.category_id).first() is None:
        raise HTTPException(422, detail={"detail": "Unknown skill category", "code": "invalid_category"})
    for key, value in data.model_dump().items():
        setattr(skill, key, value)
    db.commit()
    return {"id": skill.id, **data.model_dump(), "owner_id": user.id}


@router.delete("/skills/{skill_id}", status_code=204, tags=["skills"])
def delete_skill(skill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.owner_id == user.id).first()
    if skill is None:
        raise HTTPException(404, detail={"detail": "Skill not found", "code": "not_found"})
    if db.query(SkillExchange.id).filter(or_(SkillExchange.offered_skill_id == skill_id, SkillExchange.requested_skill_id == skill_id)).first() \
            or db.query(ExchangeRequest.id).filter(
                ExchangeRequest.status == "pending",
                or_(ExchangeRequest.offered_skill_id == skill_id, ExchangeRequest.requested_skill_id == skill_id),
            ).first():
        raise HTTPException(409, detail={"detail": "A skill used in an exchange cannot be deleted", "code": "skill_in_use"})
    db.delete(skill)
    db.commit()


@router.get("/users/me/teaching-skills", tags=["skills"])
def teaching_skills(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(Skill).join(user_teaching_skills).filter(user_teaching_skills.c.user_id == user.id)
    rows, total = page_query(query, page, page_size)
    return page_result([{"id": row.id, "name": row.name, "category_id": row.category_id} for row in rows],
                       total, page, page_size)


@router.post("/users/me/teaching-skills/{skill_id}", status_code=204, tags=["skills"])
def add_teaching_skill(skill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    skill = db.query(Skill).filter(Skill.id == skill_id, Skill.owner_id == user.id).first()
    if skill is None:
        raise HTTPException(404, detail={"detail": "Skill not found", "code": "not_found"})
    if not db.execute(user_teaching_skills.select().where(
        user_teaching_skills.c.user_id == user.id, user_teaching_skills.c.skill_id == skill_id)).first():
        db.execute(user_teaching_skills.insert().values(user_id=user.id, skill_id=skill_id))
        db.commit()


@router.delete("/users/me/teaching-skills/{skill_id}", status_code=204, tags=["skills"])
def remove_teaching_skill(skill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(user_teaching_skills.delete().where(
        user_teaching_skills.c.user_id == user.id, user_teaching_skills.c.skill_id == skill_id))
    db.commit()


@router.get("/users/me/learning-skills", tags=["skills"])
def learning_skills(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(UserLearningSkill).filter(UserLearningSkill.user_id == user.id)
    rows, total = page_query(query, page, page_size)
    return page_result([{"id": s.id, "skill_name": s.skill_name, "category_id": s.category_id, "level": s.level}
                        for s in rows], total, page, page_size)


@router.post("/users/me/learning-skills", status_code=201, tags=["skills"])
def add_learning_skill(data: LearningSkillCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = UserLearningSkill(user_id=user.id, **data.model_dump())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, detail={"detail": "This learning skill already exists", "code": "duplicate_skill"})
    db.refresh(row)
    return {"id": row.id, **data.model_dump()}


@router.delete("/users/me/learning-skills/{learning_skill_id}", status_code=204, tags=["skills"])
def remove_learning_skill(learning_skill_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(UserLearningSkill).filter(
        UserLearningSkill.id == learning_skill_id, UserLearningSkill.user_id == user.id).first()
    if row is None:
        raise HTTPException(404, detail={"detail": "Learning skill not found", "code": "not_found"})
    db.delete(row)
    db.commit()


@router.post("/posts", status_code=201, tags=["posts"])
def create_post(data: PostCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = Post(author_id=user.id, content=data.content)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_dict(db, post, user.id)


@router.get("/posts", tags=["posts"])
def list_posts(
    q: str = "", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_user),
):
    query = db.query(Post).join(User, User.id == Post.author_id).filter(User.is_active.is_(True))
    if q.strip():
        query = query.filter(Post.content.ilike(f"%{q.strip()}%"))
    items, total = page_query(query.order_by(Post.created_at.desc()), page, page_size)
    return page_result([post_dict(db, post, user.id if user else None) for post in items], total, page, page_size)


@router.get("/posts/{post_id}", tags=["posts"])
def get_post(post_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    return post_dict(db, post, user.id if user else None)


@router.put("/posts/{post_id}", tags=["posts"])
def update_post(post_id: int, data: PostCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == user.id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    post.content = data.content
    db.commit()
    return post_dict(db, post, user.id)


@router.delete("/posts/{post_id}", status_code=204, tags=["posts"])
def delete_post(post_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == user.id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    for media in db.query(PostMedia).filter(PostMedia.post_id == post_id).all():
        (UPLOAD_DIR / media.file_path).unlink(missing_ok=True)
    db.delete(post)
    db.commit()


@router.post("/posts/{post_id}/media", status_code=201, tags=["posts"])
async def upload_post_media(post_id: int, file: UploadFile = File(...),
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id, Post.author_id == user.id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    filename, media_type, size = await store_upload(file)
    media = PostMedia(post_id=post.id, file_path=filename, media_type=media_type, size_bytes=size)
    db.add(media)
    db.commit()
    db.refresh(media)
    return {"id": media.id, "url": f"/uploads/{filename}", "media_type": media_type, "size_bytes": size}


@router.post("/posts/{post_id}/like", tags=["posts"])
def toggle_like(post_id: int, data: LikeAction | None = None,
                db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Post.id).filter(Post.id == post_id).first() is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    like = db.query(Like).filter(Like.post_id == post_id, Like.user_id == user.id).first()
    desired = data.liked if data else None
    if desired is False or (desired is None and like):
        if like:
            db.delete(like)
        liked = False
    elif desired is True or (desired is None and not like):
        if like is None:
            db.add(Like(post_id=post_id, user_id=user.id))
        post = db.query(Post).filter(Post.id == post_id).first()
        if post.author_id != user.id:
            notify(db, post.author_id, "post_like", f"{user.username} liked your post.", "post", post.id)
        liked = True
    else:
        liked = bool(like)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        liked = db.query(Like.id).filter(Like.post_id == post_id, Like.user_id == user.id).first() is not None
    return {"liked": liked, "like_count": db.query(Like).filter(Like.post_id == post_id).count()}


@router.post("/posts/{post_id}/comments", status_code=201, tags=["posts"])
def add_comment(post_id: int, data: CommentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    comment = Comment(post_id=post_id, user_id=user.id, content=data.content)
    db.add(comment)
    if post.author_id != user.id:
        notify(db, post.author_id, "post_comment", f"{user.username} commented on your post.", "post", post.id)
    db.commit()
    db.refresh(comment)
    return {"id": comment.id, "post_id": post_id, "user_id": user.id, "username": user.username,
            "content": comment.content, "created_at": comment.created_at}


@router.get("/posts/{post_id}/comments", tags=["posts"])
def list_comments(post_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db)):
    query = db.query(Comment).filter(Comment.post_id == post_id)
    rows, total = page_query(query.order_by(Comment.created_at), page, page_size)
    return page_result([{"id": c.id, "user_id": c.user_id,
                         "username": db.query(User.username).filter(User.id == c.user_id).scalar(),
                         "content": c.content, "created_at": c.created_at} for c in rows], total, page, page_size)


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=204, tags=["posts"])
def delete_comment(post_id: int, comment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    comment = db.query(Comment).filter(
        Comment.id == comment_id, Comment.post_id == post_id, Comment.user_id == user.id).first()
    if comment is None:
        raise HTTPException(404, detail={"detail": "Comment not found", "code": "not_found"})
    db.delete(comment)
    db.commit()


def create_report(target_type, target_id, data, db, user):
    report = Report(reporter_id=user.id, target_type=target_type, target_id=target_id, reason=data.reason)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "status": report.status}


@router.post("/posts/{post_id}/report", status_code=201, tags=["posts"])
def report_post(post_id: int, data: ReportCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if data.target_type != "post" or data.target_id not in (None, post_id) or db.query(Post.id).filter(Post.id == post_id).first() is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    return create_report("post", post_id, data, db, user)


@router.post("/posts/{post_id}/comments/{comment_id}/report", status_code=201, tags=["posts"])
def report_comment(post_id: int, comment_id: int, data: ReportCreate,
                   db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Comment.id).filter(Comment.id == comment_id, Comment.post_id == post_id).first() is None:
        raise HTTPException(404, detail={"detail": "Comment not found", "code": "not_found"})
    return create_report("comment", comment_id, data, db, user)


@router.post("/exchanges/requests", status_code=201, tags=["exchanges"])
def new_exchange_request(data: ExchangeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = create_request(db, user, data.receiver_id, data.offered_skill_id, data.requested_skill_id, data.duration_days)
    return request_view(row)


@router.get("/exchanges/requests/received", tags=["exchanges"])
def requests_received(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                      db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(ExchangeRequest).filter(ExchangeRequest.receiver_id == user.id)
    rows, total = page_query(query.order_by(ExchangeRequest.created_at.desc()), page, page_size)
    return page_result([request_view(r) for r in rows], total, page, page_size)


@router.get("/exchanges/requests/sent", tags=["exchanges"])
def requests_sent(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(ExchangeRequest).filter(ExchangeRequest.requester_id == user.id)
    rows, total = page_query(query.order_by(ExchangeRequest.created_at.desc()), page, page_size)
    return page_result([request_view(r) for r in rows], total, page, page_size)


@router.get("/exchanges/requests/{request_id}", tags=["exchanges"])
def get_exchange_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return request_view(get_participant_request(db, request_id, user.id))


@router.post("/exchanges/requests/{request_id}/accept", tags=["exchanges"])
def accept_exchange_request(request_id: int, data: ExchangeDuration | None = None,
                            db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_participant_request(db, request_id, user.id)
    exchange = accept_request(db, row, user, data.duration_days if data else None)
    return exchange_view(exchange)


@router.post("/exchanges/requests/{request_id}/counter", tags=["exchanges"])
def counter_exchange_request(request_id: int, data: ExchangeDuration,
                             db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_participant_request(db, request_id, user.id)
    return request_view(counter_request(db, row, user, data.duration_days))


@router.post("/exchanges/requests/{request_id}/reject", tags=["exchanges"])
def reject_exchange_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_participant_request(db, request_id, user.id)
    if row.status != "pending" or row.proposed_by_id == user.id:
        raise HTTPException(409, detail={"detail": "Only the non-proposing participant may reject a pending request", "code": "invalid_transition"})
    row.status = "rejected"
    other = row.requester_id if user.id == row.receiver_id else row.receiver_id
    notify(db, other, "exchange_rejected", f"{user.username} rejected your exchange request.", "exchange_request", row.id)
    db.commit()
    return request_view(row)


@router.post("/exchanges/requests/{request_id}/cancel", tags=["exchanges"])
def cancel_exchange_request(request_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = get_participant_request(db, request_id, user.id)
    if row.status != "pending" or row.requester_id != user.id:
        raise HTTPException(409, detail={"detail": "Only the requester may cancel a pending request", "code": "invalid_transition"})
    row.status = "cancelled"
    db.commit()
    return request_view(row)


@router.get("/exchanges/active", tags=["exchanges"])
def active_exchanges(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    query = db.query(SkillExchange).filter(
        SkillExchange.status == "active",
        or_(SkillExchange.requester_id == user.id, SkillExchange.receiver_id == user.id),
    )
    rows, total = page_query(query.order_by(SkillExchange.end_date), page, page_size)
    for row in rows:
        maybe_notify_near_end(db, row)
    return page_result([exchange_view(row) for row in rows], total, page, page_size)


@router.get("/exchanges/history", tags=["exchanges"])
def exchange_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                     db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(SkillExchange).filter(
        SkillExchange.status.in_(("completed", "cancelled")),
        or_(SkillExchange.requester_id == user.id, SkillExchange.receiver_id == user.id),
    )
    rows, total = page_query(query.order_by(SkillExchange.end_date.desc()), page, page_size)
    return page_result([exchange_view(row) for row in rows], total, page, page_size)


@router.get("/exchanges/{exchange_id}", tags=["exchanges"])
def get_exchange(exchange_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(SkillExchange).filter(
        SkillExchange.id == exchange_id,
        or_(SkillExchange.requester_id == user.id, SkillExchange.receiver_id == user.id),
    ).first()
    if row is None:
        raise HTTPException(404, detail={"detail": "Exchange not found", "code": "not_found"})
    return exchange_view(row)


def update_exchange_status(exchange_id, status, db, user):
    row = db.query(SkillExchange).filter(
        SkillExchange.id == exchange_id,
        or_(SkillExchange.requester_id == user.id, SkillExchange.receiver_id == user.id),
    ).first()
    if row is None:
        raise HTTPException(404, detail={"detail": "Exchange not found", "code": "not_found"})
    if row.status != "active":
        raise HTTPException(409, detail={"detail": "Exchange is no longer active", "code": "invalid_transition"})
    row.status = status
    if status == "completed":
        row.completed_at = datetime.now(timezone.utc)
    for participant in (row.requester_id, row.receiver_id):
        notify(db, participant, f"exchange_{status}", f"Your exchange was {status}.", "skill_exchange", row.id)
    db.commit()
    return exchange_view(row)


@router.post("/exchanges/{exchange_id}/complete", tags=["exchanges"])
def complete_exchange(exchange_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_exchange_status(exchange_id, "completed", db, user)


@router.post("/exchanges/{exchange_id}/cancel", tags=["exchanges"])
def cancel_exchange(exchange_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return update_exchange_status(exchange_id, "cancelled", db, user)


@router.get("/notifications", tags=["notifications"])
def notifications(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    query = db.query(Notification).filter(Notification.user_id == user.id)
    rows, total = page_query(query.order_by(Notification.created_at.desc()), page, page_size)
    return page_result([{"id": n.id, "type": n.type, "message": n.message, "related_type": n.related_type,
                         "related_id": n.related_id, "is_read": n.is_read, "created_at": n.created_at} for n in rows], total, page, page_size)


@router.get("/notifications/unread-count", tags=["notifications"])
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"unread_count": db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)).count()}


@router.patch("/notifications/{notification_id}/read", tags=["notifications"])
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if row is None:
        raise HTTPException(404, detail={"detail": "Notification not found", "code": "not_found"})
    row.is_read = True
    db.commit()
    return {"id": row.id, "is_read": row.is_read}


@router.patch("/notifications/read-all", tags=["notifications"])
def mark_all_notifications_read(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).update(
        {Notification.is_read: True}, synchronize_session=False)
    db.commit()
    return {"updated": True}


@router.get("/search", tags=["search"])
def search(
    q: str = "", type: str = "all", category: str | None = None, level: str | None = None,
    availability: str | None = None, sort: str = "recent",
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    term = f"%{q.strip()}%"
    results = []
    if type in ("all", "users"):
        uq = db.query(User).filter(User.is_active.is_(True), or_(User.username.ilike(term), User.name.ilike(term)))
        if availability:
            uq = uq.join(UserProfile).filter(UserProfile.availability.ilike(f"%{availability}%"))
        users = uq.order_by(User.created_at.desc()).all()
        results.extend({"type": "user", **profile_dict(db, u)} for u in users)
    if type in ("all", "skills"):
        sq = db.query(Skill, SkillCategory.name).join(SkillCategory).join(User, User.id == Skill.owner_id).filter(
            User.is_active.is_(True), Skill.name.ilike(term))
        if category:
            sq = sq.filter(SkillCategory.name.ilike(category))
        if level:
            sq = sq.filter(Skill.experience_level == level)
        if availability:
            sq = sq.join(UserProfile, UserProfile.user_id == User.id).filter(UserProfile.availability.ilike(f"%{availability}%"))
        entries = sq.order_by(Skill.created_at.desc()).all()
        results.extend({"type": "skill", "id": s.id, "owner_id": s.owner_id, "name": s.name,
                        "category": cat, "description": s.description, "experience_level": s.experience_level,
                        "created_at": s.created_at} for s, cat in entries)
    if type in ("all", "categories"):
        cats = db.query(SkillCategory).filter(SkillCategory.name.ilike(term)).all()
        results.extend({"type": "category", "id": c.id, "name": c.name} for c in cats)
    if type in ("all", "posts"):
        posts = db.query(Post).filter(Post.content.ilike(term)).order_by(Post.created_at.desc()).all()
        results.extend({"type": "post", **post_dict(db, p)} for p in posts)
    if sort == "name":
        results.sort(key=lambda result: result.get("name", result.get("username", "")).lower())
    else:
        def date_key(result):
            value = result.get("created_at")
            if not isinstance(value, datetime):
                return 0
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.timestamp()
        results.sort(key=date_key, reverse=True)
    total = len(results)
    start = (page - 1) * page_size
    return page_result(results[start:start + page_size], total, page, page_size)


@router.get("/admin/dashboard", tags=["admin"])
def admin_dashboard(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "users": db.query(User).count(), "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
        "posts": db.query(Post).count(), "active_exchanges": db.query(SkillExchange).filter(SkillExchange.status == "active").count(),
        "completed_exchanges": db.query(SkillExchange).filter(SkillExchange.status == "completed").count(),
        "open_reports": db.query(Report).filter(Report.status == "open").count(),
    }


@router.get("/admin/users", tags=["admin"])
def admin_users(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows, total = page_query(db.query(User).order_by(User.created_at.desc()), page, page_size)
    return page_result([{"id": u.id, "username": u.username, "email": u.email, "role": u.role,
                         "is_active": u.is_active, "created_at": u.created_at} for u in rows], total, page, page_size)


@router.patch("/admin/users/{user_id}/status", tags=["admin"])
def set_user_status(user_id: int, data: UserStatusUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(404, detail={"detail": "User not found", "code": "not_found"})
    if target.id == admin.id and not data.is_active:
        raise HTTPException(409, detail={"detail": "You cannot deactivate your own account", "code": "invalid_action"})
    target.is_active = data.is_active
    db.commit()
    return {"id": target.id, "is_active": target.is_active}


@router.get("/admin/reports", tags=["admin"])
def admin_reports(status: str = "open", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows, total = page_query(db.query(Report).filter(Report.status == status).order_by(Report.created_at.desc()), page, page_size)
    return page_result([{"id": r.id, "reporter_id": r.reporter_id, "target_type": r.target_type,
                         "target_id": r.target_id, "reason": r.reason, "status": r.status,
                         "created_at": r.created_at} for r in rows], total, page, page_size)


@router.patch("/admin/reports/{report_id}", tags=["admin"])
def resolve_report(report_id: int, data: ReportResolve, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None:
        raise HTTPException(404, detail={"detail": "Report not found", "code": "not_found"})
    report.status = data.status
    report.resolved_by = admin.id
    db.commit()
    return {"id": report.id, "status": report.status}


@router.delete("/admin/posts/{post_id}", status_code=204, tags=["admin"])
def admin_delete_post(post_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(404, detail={"detail": "Post not found", "code": "not_found"})
    for media in db.query(PostMedia).filter(PostMedia.post_id == post_id).all():
        (UPLOAD_DIR / media.file_path).unlink(missing_ok=True)
    db.delete(post)
    db.commit()
