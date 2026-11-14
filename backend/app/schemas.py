from typing import Literal

from pydantic import AwareDatetime, BaseModel, EmailStr, Field, field_validator

LEVELS = ("Beginner", "Intermediate", "Advanced", "Expert")


def validate_password_bytes(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 UTF-8 bytes")
    return password


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=100)
    language: str = Field(default="", max_length=80)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        return validate_password_bytes(value)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        return validate_password_bytes(value)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    profile_image: str | None = Field(default=None, max_length=500)
    bio: str | None = Field(default=None, max_length=2000)
    location: str | None = Field(default=None, max_length=120)
    experience_level: Literal["Beginner", "Intermediate", "Advanced", "Expert"] | None = None
    availability: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=80)
    social_links: dict[str, str] | None = None


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category_id: int
    description: str = Field(default="", max_length=2000)
    experience_level: Literal["Beginner", "Intermediate", "Advanced", "Expert"] = "Beginner"


class LearningSkillCreate(BaseModel):
    skill_name: str = Field(min_length=1, max_length=120)
    category_id: int | None = None
    level: Literal["Beginner", "Intermediate", "Advanced", "Expert"] = "Beginner"


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class LikeAction(BaseModel):
    liked: bool | None = None


class ExchangeCreate(BaseModel):
    receiver_id: int
    offered_skill_id: int
    requested_skill_id: int
    duration_days: int = Field(ge=1, le=365)


class ExchangeDuration(BaseModel):
    duration_days: int = Field(ge=1, le=365)


class MessageCreate(BaseModel):
    exchange_id: int = Field(ge=1)
    body: str = Field(min_length=1, max_length=2000)


class ScheduleEventCreate(BaseModel):
    exchange_id: int = Field(ge=1)
    title: str = Field(min_length=3, max_length=120)
    starts_at: AwareDatetime


class ReportCreate(BaseModel):
    target_type: Literal["post", "comment"] = "post"
    target_id: int | None = None
    reason: str = Field(min_length=3, max_length=1000)


class ReportResolve(BaseModel):
    status: Literal["resolved", "dismissed"]


class UserStatusUpdate(BaseModel):
    is_active: bool
