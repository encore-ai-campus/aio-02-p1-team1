from pydantic import BaseModel, Field


class SearchStatPoint(BaseModel):
    label: str
    value: int = Field(ge=0)


class SearchStatsResponse(BaseModel):
    food: list[SearchStatPoint] = Field(default_factory=list)
    price: list[SearchStatPoint] = Field(default_factory=list)
    feature: list[SearchStatPoint] = Field(default_factory=list)
