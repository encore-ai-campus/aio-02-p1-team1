from datetime import datetime, timezone
from uuid import UUID

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.request_context import get_current_request_id


def utc_now():
    return datetime.now(timezone.utc)


def new_request_id():
    return get_current_request_id()


class ResponseMeta(BaseModel):
    request_id: UUID
    timestamp: datetime
    page: int | None = None
    page_size: int | None = None
    total_count: int | None = None


class ErrorDetail(BaseModel):
    field: str | None = None
    reason: str


class ErrorBody(BaseModel):
    status: int = Field(ge=400, le=599)
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)
    request_id: UUID
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: ErrorBody


def build_error_response(status, code, message, details=None):
    request_id = new_request_id()
    response = JSONResponse(
        status_code=status,
        content=ErrorResponse(
            error=ErrorBody(
                status=status,
                code=code,
                message=message,
                details=details or [],
                request_id=request_id,
                timestamp=utc_now(),
            )
        ).model_dump(mode="json"),
    )
    response.headers["X-Request-ID"] = str(request_id)
    return response


def build_success_response(data, page=None, page_size=None, total_count=None):
    meta = ResponseMeta(
        request_id=new_request_id(),
        timestamp=utc_now(),
        page=page,
        page_size=page_size,
        total_count=total_count,
    )
    payload = {"data": data, "meta": meta.model_dump(mode="json")}
    if page is None:
        payload["meta"].pop("page", None)
        payload["meta"].pop("page_size", None)
        payload["meta"].pop("total_count", None)
    return payload
