from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ── 메시지 ────────────────────────────────────────────────────────
# 주의: role 은 Literal 로 값을 고정한다. str 로 두면 'robot' 같은 값이 그대로 통과한다.
# MessageCreate — role(Literal), content(1자 이상)
class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

# MessageOut    — id, conversation_id, role, content, created_at
class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
