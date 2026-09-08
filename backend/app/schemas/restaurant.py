from uuid import UUID

from pydantic import BaseModel, Field


class MenuSummary(BaseModel):
    id: UUID
    name: str
    price: int = Field(ge=0)


class TagCategory(BaseModel):
    id: UUID
    code: str
    name: str


class RestaurantTag(BaseModel):
    id: UUID
    category_id: UUID
    name: str


class RestaurantSummary(BaseModel):
    id: UUID
    name: str
    address: str | None = None
    phone: str | None = None
    description: str | None = None
    storage_path: str | None = None
    category_id: UUID | None = None
    category_name: str | None = None
    kakao_place_id: str | None = None
    kakao_place_url: str | None = None
    road_address: str | None = None
    is_active: bool = True
    menus: list[MenuSummary] = Field(default_factory=list)
    matched_tags: list[str] = Field(default_factory=list)


class RestaurantCategory(BaseModel):
    id: UUID
    name: str
