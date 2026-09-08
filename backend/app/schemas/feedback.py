from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
