from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Table,
    Text, TypeDecorator, UniqueConstraint, func,
)
from datetime import timezone

from .database import Base


class UTCDateTime(TypeDecorator):
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


user_teaching_skills = Table(
    "user_teaching_skills", Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, default="")
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(40), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    updated_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name = Column(String(100), nullable=False, default="")
    profile_image = Column(String(500))
    bio = Column(Text, nullable=False, default="")
    location = Column(String(120), nullable=False, default="")
    experience_level = Column(String(20), nullable=False, default="Beginner")
    social_links = Column(JSON, nullable=False, default=dict)
    availability = Column(String(120), nullable=False, default="")
    language = Column(String(80), nullable=False, default="")
    updated_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), onupdate=func.now())


class SkillCategory(Base):
    __tablename__ = "skill_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    owner_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(ForeignKey("skill_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=False, default="")
    experience_level = Column(String(20), nullable=False, default="Beginner")
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    updated_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), onupdate=func.now())


class UserLearningSkill(Base):
    __tablename__ = "user_learning_skills"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(120), nullable=False)
    category_id = Column(ForeignKey("skill_categories.id", ondelete="SET NULL"))
    level = Column(String(20), nullable=False, default="Beginner")
    __table_args__ = (UniqueConstraint("user_id", "skill_name", name="uq_learning_user_topic"),)


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    author_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    updated_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), onupdate=func.now())


class PostMedia(Base):
    __tablename__ = "post_media"
    id = Column(Integer, primary_key=True)
    post_id = Column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    media_type = Column(String(20), nullable=False)
    size_bytes = Column(Integer, nullable=False)


class Like(Base):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    post_id = Column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),)


class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    post_id = Column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())


class ExchangeRequest(Base):
    __tablename__ = "exchange_requests"
    id = Column(Integer, primary_key=True)
    requester_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    offered_skill_id = Column(ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False)
    requested_skill_id = Column(ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False)
    proposed_by_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    duration_days = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    user_low_id = Column(Integer, nullable=False)
    user_high_id = Column(Integer, nullable=False)
    skill_of_low_id = Column(Integer, nullable=False)
    skill_of_high_id = Column(Integer, nullable=False)
    exchange_id = Column(ForeignKey("skill_exchanges.id", ondelete="SET NULL"))
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    __table_args__ = (
        Index(
            "uq_pending_exchange_request_combination",
            "user_low_id", "user_high_id", "skill_of_low_id", "skill_of_high_id",
            unique=True, sqlite_where=(status == "pending"),
            postgresql_where=(status == "pending"),
        ),
    )


class SkillExchange(Base):
    __tablename__ = "skill_exchanges"
    id = Column(Integer, primary_key=True)
    requester_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    offered_skill_id = Column(ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False)
    requested_skill_id = Column(ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False)
    duration_days = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="active", index=True)
    user_low_id = Column(Integer, nullable=False)
    user_high_id = Column(Integer, nullable=False)
    skill_of_low_id = Column(Integer, nullable=False)
    skill_of_high_id = Column(Integer, nullable=False)
    cycle_number = Column(Integer, nullable=False)
    start_date = Column(UTCDateTime(), nullable=False)
    end_date = Column(UTCDateTime(), nullable=False)
    completed_at = Column(UTCDateTime())
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    __table_args__ = (
        UniqueConstraint(
            "user_low_id", "user_high_id", "skill_of_low_id", "skill_of_high_id",
            "cycle_number", name="uq_exchange_combination_cycle",
        ),
        Index(
            "uq_open_skill_exchange_combination",
            "user_low_id", "user_high_id", "skill_of_low_id", "skill_of_high_id",
            unique=True, sqlite_where=(status == "active"),
            postgresql_where=(status == "active"),
        ),
    )


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(60), nullable=False)
    message = Column(String(300), nullable=False)
    related_type = Column(String(40))
    related_id = Column(Integer)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index(
            "uq_exchange_nearing_notification",
            "user_id", "related_type", "related_id",
            unique=True,
            sqlite_where=(type == "exchange_nearing_completion"),
            postgresql_where=(type == "exchange_nearing_completion"),
        ),
    )


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    token_hash = Column(String(64), primary_key=True)
    expires_at = Column(UTCDateTime(), nullable=False, index=True)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    exchange_id = Column(ForeignKey("skill_exchanges.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    body = Column(String(2000), nullable=False)
    read_at = Column(UTCDateTime())
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now(), index=True)


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"
    id = Column(Integer, primary_key=True)
    exchange_id = Column(ForeignKey("skill_exchanges.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    starts_at = Column(UTCDateTime(), nullable=False, index=True)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    reporter_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type = Column(String(20), nullable=False)
    target_id = Column(Integer, nullable=False)
    reason = Column(String(1000), nullable=False)
    status = Column(String(20), nullable=False, default="open", index=True)
    created_at = Column(UTCDateTime(), nullable=False, server_default=func.now())
    resolved_by = Column(ForeignKey("users.id", ondelete="SET NULL"))
