from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ── 사용자 ────────────────────────────────────────────────────────
#1. UserCreate  — email(EmailStr), username(2~30자)
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=30)

#2. UserUpdate  — username 만
class UserUpdate(BaseModel):
    username: str = Field(min_length=2, max_length=30)

#3. UserOut     — id(UUID), email, username, created_at(datetime)
class UserOut(BaseModel):
    id: UUID
    email: str
    username: str
    created_at: datetime