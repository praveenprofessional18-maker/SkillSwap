from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SkillPost(Base):
    __tablename__ = "skill_posts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(180), nullable=False)
    description = Column(Text, default="")
    skill_name = Column(String(100), nullable=False, index=True)
    category = Column(String(80), default="")
    media_url = Column(String(500), nullable=True)
    media_type = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Exchange(Base):
    __tablename__ = "exchanges"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    offered_skill = Column(String(100), nullable=False)
    requested_skill = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    repeat_count = Column(Integer, nullable=False, default=0)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
