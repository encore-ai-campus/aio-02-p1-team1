from pydantic import BaseModel
from typing import Literal
from uuid import UUID

# ── 피드백 클래스 ────────────────────────────────────────────────────────
class FeedbackRequest(BaseModel):
    message_id: UUID
    # None 이면 취소다. 한 번 누른 것을 되돌릴 수 있어야 한다.
    value: Literal["up", "down"] | None = None