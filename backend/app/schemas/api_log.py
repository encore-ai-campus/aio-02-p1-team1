from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class LogFilters(BaseModel):
    endpoint: str | None = Field(default=None, max_length=255)
    http_method: Literal["GET", "POST", "PATCH", "DELETE"] | None = None
    status_code: int | None = Field(default=None, ge=100, le=599)
    error_only: bool = False


class PeriodRequest(BaseModel):
    period_start: datetime
    period_end: datetime

    @model_validator(mode="after")
    def validate_period(self):
        if self.period_start >= self.period_end:
            raise ValueError("period_start는 period_end보다 이전이어야 합니다.")
        return self


class CleaningRunRequest(PeriodRequest):
    criteria_version: str | None = Field(default=None, max_length=50)


class CleaningRunResponse(BaseModel):
    id: UUID
    period_start: datetime
    period_end: datetime
    criteria_version: str
    status: Literal["running", "succeeded", "failed"]
    source_count: int = Field(ge=0)
    included_count: int = Field(ge=0)
    excluded_count: int = Field(ge=0)
    started_at: datetime
    completed_at: datetime | None = None


class ApiLogItem(BaseModel):
    id: UUID
    request_id: UUID
    profile_id: UUID | None = None
    occurred_at: datetime
    http_method: str
    endpoint: str
    endpoint_path: str
    status_code: int
    response_time_ms: int
    error_code: str | None = None
    client_type: str | None = None
    created_at: datetime


class ApiLogDetailResponse(ApiLogItem):
    is_included: bool | None = None
    normalized_endpoint: str | None = None
    exclusion_reason: str | None = None


class MetricPoint(BaseModel):
    endpoint: str
    http_method: str
    request_count: int = Field(ge=0)
    error_count: int = Field(ge=0)
    error_rate: float | None = Field(default=None, ge=0, le=1)
    avg_response_time_ms: float | None = Field(default=None, ge=0)
    p95_response_time_ms: float | None = Field(default=None, ge=0)


class ApiStatisticsResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    cleaning_run_id: UUID | None = None
    points: list[MetricPoint]


class LogSummaryRequest(PeriodRequest):
    cleaning_run_id: UUID
    filters: LogFilters = Field(default_factory=LogFilters)


class EvidenceLog(BaseModel):
    api_log_id: UUID
    occurred_at: datetime
    http_method: str
    endpoint: str
    status_code: int
    response_time_ms: int
    error_code: str | None = None
    claim_text: str | None = None


class LogSummaryResponse(BaseModel):
    summary_id: UUID
    status: Literal["running", "succeeded", "failed"]
    period_start: datetime
    period_end: datetime
    filters: LogFilters
    summary_text: str | None = None
    evidence: list[EvidenceLog] = Field(default_factory=list)
    model_name: str
    prompt_version: str
    error_code: str | None = None
    created_at: datetime


class EvaluationRunRequest(BaseModel):
    summary_id: UUID
    case_id: UUID | None = None
    experiment_id: UUID | None = None
    run_type: Literal["baseline", "before", "after"] = "baseline"


class EvaluationRunResponse(BaseModel):
    id: UUID
    case_id: UUID
    summary_id: UUID
    experiment_id: UUID | None = None
    run_type: Literal["baseline", "before", "after"]
    factuality_score: float
    completeness_score: float
    total_score: float
    notes: str | None = None
    created_at: datetime


class ExperimentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    hypothesis: str = Field(min_length=1)
    change_description: str = Field(min_length=1)
    before_version: str = Field(min_length=1, max_length=50)
    after_version: str = Field(min_length=1, max_length=50)


class ExperimentResponse(BaseModel):
    id: UUID
    name: str
    hypothesis: str
    change_description: str
    before_version: str
    after_version: str
    status: Literal["planned", "running", "completed", "failed"]
    created_at: datetime
    runs: list[EvaluationRunResponse] = Field(default_factory=list)
