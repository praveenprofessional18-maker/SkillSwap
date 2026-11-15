from pydantic import BaseModel, EmailStr, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class PostCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    description: str = ""
    skill_name: str = Field(min_length=1, max_length=100)
    category: str = ""

class ExchangeCreate(BaseModel):
    receiver_id: int
    offered_skill: str = Field(min_length=1, max_length=100)
    requested_skill: str = Field(min_length=1, max_length=100)
    duration_days: int = Field(ge=1, le=365)

class ExchangeDecision(BaseModel):
    status: str
