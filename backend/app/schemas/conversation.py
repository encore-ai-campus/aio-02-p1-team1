from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ── 대화 ──────────────────────────────────────────────────────────
# ConversationCreate — user_id(UUID), title(1~100자)
class ConversationCreate(BaseModel):
    user_id: UUID
    title: str = Field(min_length=1, max_length=100)

# ConversationOut    — id, user_id, title, created_at
class ConversationOut(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    created_at: datetime

class MyConversationCreate(BaseModel):
    # 주의: user_id 를 받지 않는다. 토큰에서 꺼낸 값만 신뢰한다.
    #      받으면 남의 명의로 대화를 만들 수 있다.
    title: str | None = None

class ConversationUpdate(BaseModel):
    title: str