from datetime import datetime
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


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

# 회원가입 요청으로 받을 값과 검사 규칙
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nickname: str = Field(min_length=1, max_length=45)
    terms_agreed: Literal[True]
    privacy_agreed: Literal[True]

    @field_validator("nickname", mode="before")
    @classmethod
    def strip_nickname(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value

# 회원가입 완료 후 돌려줄 회원 정보
class SignUpResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    nickname: str
    created_at: datetime

# 응답에 함께 담을 요청 번호와 시각
class ResponseMeta(BaseModel):
    request_id: UUID
    timestamp: datetime

# 성공 응답에 담을 데이터의 종류
T = TypeVar("T")


# 공통 성공 응답
class SuccessResponse(BaseModel, Generic[T]):
    data: T
    meta: ResponseMeta

# 닉네임 수정 요청 데이터
class NicknameUpdateRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=45)
    @field_validator("nickname", mode="before")
    @classmethod
    def strip_nickname(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value