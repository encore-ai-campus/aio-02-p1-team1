
from pydantic import BaseModel
from typing import Literal
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field

# ── 피드백 클래스 ────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    message_id: UUID
    # None 이면 취소다. 한 번 누른 것을 되돌릴 수 있어야 한다.
    value: Literal["up", "down"] | None = None

class AdminFeedbackItem(BaseModel):
    feedback_id: UUID
    profile_id: UUID
    conversation_id: UUID
    restaurant_id: UUID
    restaurant_name: str | None = None
    category_name: str | None = None
    feedback_value: Literal["1", "2", "3"]
    matched_tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None = None


class AdminFeedbackCounts(BaseModel):
    feedback_1: int = Field(ge=0)
    feedback_2: int = Field(ge=0)
    feedback_3: int = Field(ge=0)

