from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.db import supabase
from app.schemas.common import build_error_response, build_success_response
from app.schemas.restaurant import (
    MenuSummary,
    RestaurantCategory,
    RestaurantSummary,
    RestaurantTag,
    TagCategory,
)

router = APIRouter(tags=["restaurants"])


def get_category_name(row):
    category = row.get("restaurant_categories")
    if isinstance(category, dict):
        return category.get("name")
    return None


def build_restaurant_item(row, menus, matched_tags):
    return RestaurantSummary(
        id=row["id"],
        name=row["name"],
        address=row.get("address"),
        phone=row.get("phone"),
        description=row.get("description"),
        storage_path=row.get("storage_path"),
        category_id=row.get("category_id"),
        category_name=get_category_name(row),
        kakao_place_id=row.get("kakao_place_id"),
        kakao_place_url=row.get("kakao_place_url"),
        road_address=row.get("road_address"),
        is_active=row.get("is_active", True),
        menus=menus,
        matched_tags=matched_tags,
    ).model_dump(mode="json")


def list_menus_by_restaurant_ids(restaurant_ids):
    if not restaurant_ids:
        return {}
    result = (
        supabase.table("menus")
        .select("id, restaurant_id, name, price")
        .in_("restaurant_id", restaurant_ids)
        .order("name")
        .execute()
    )
    menus_by_restaurant_id = {restaurant_id: [] for restaurant_id in restaurant_ids}
    for row in result.data or []:
        restaurant_id = row["restaurant_id"]
        menus_by_restaurant_id.setdefault(restaurant_id, []).append(
            MenuSummary(
                id=row["id"],
                name=row["name"],
                price=row["price"],
            )
        )
    return menus_by_restaurant_id


def list_tags_by_restaurant_ids(restaurant_ids):
    if not restaurant_ids:
        return {}
    result = (
        supabase.table("restaurant_tag_map")
        .select("restaurant_id, restaurant_tags(name)")
        .in_("restaurant_id", restaurant_ids)
        .execute()
    )
    tags_by_restaurant_id = {restaurant_id: [] for restaurant_id in restaurant_ids}
    for row in result.data or []:
        tag = row.get("restaurant_tags")
        tag_name = tag.get("name") if isinstance(tag, dict) else None
        if tag_name:
            tags_by_restaurant_id.setdefault(row["restaurant_id"], []).append(tag_name)
    return tags_by_restaurant_id


@router.get("/restaurant-categories")
def list_restaurant_categories():
    try:
        result = (
            supabase.table("restaurant_categories")
            .select("id, name")
            .order("name")
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    items = [
        RestaurantCategory(id=row["id"], name=row["name"]).model_dump(mode="json")
        for row in result.data or []
    ]
    return build_success_response({"items": items})


@router.get("/restaurants")
def list_restaurants(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    start = (page - 1) * page_size
    end = start + page_size - 1
    try:
        result = (
            supabase.table("restaurants")
            .select("*, restaurant_categories(name)", count="exact")
            .order("name")
            .range(start, end)
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    rows = result.data or []
    restaurant_ids = [row["id"] for row in rows]
    try:
        menus_by_restaurant_id = list_menus_by_restaurant_ids(restaurant_ids)
        tags_by_restaurant_id = list_tags_by_restaurant_ids(restaurant_ids)
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    items = [
        build_restaurant_item(
            row,
            menus_by_restaurant_id.get(row["id"], []),
            tags_by_restaurant_id.get(row["id"], []),
        )
        for row in rows
    ]
    return build_success_response(
        {"items": items},
        page=page,
        page_size=page_size,
        total_count=result.count or 0,
    )


@router.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: UUID):
    try:
        result = (
            supabase.table("restaurants")
            .select("*, restaurant_categories(name)")
            .eq("id", str(restaurant_id))
            .limit(1)
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    rows = result.data or []
    if not rows:
        return build_error_response(
            404,
            "RESOURCE_NOT_FOUND",
            "식당을 찾을 수 없습니다.",
        )

    row = rows[0]
    try:
        menus_by_restaurant_id = list_menus_by_restaurant_ids([row["id"]])
        tags_by_restaurant_id = list_tags_by_restaurant_ids([row["id"]])
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    return build_success_response(
        build_restaurant_item(
            row,
            menus_by_restaurant_id.get(row["id"], []),
            tags_by_restaurant_id.get(row["id"], []),
        )
    )


@router.get("/tag-categories")
def list_tag_categories():
    try:
        result = (
            supabase.table("tag_categories")
            .select("id, code, name")
            .order("name")
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )
    items = [
        TagCategory(id=row["id"], code=row["code"], name=row["name"]).model_dump(
            mode="json"
        )
        for row in result.data or []
    ]
    return build_success_response({"items": items})


@router.get("/restaurant-tags")
def list_restaurant_tags():
    try:
        result = (
            supabase.table("restaurant_tags")
            .select("id, category_id, name")
            .order("name")
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )
    items = [
        RestaurantTag(
            id=row["id"],
            category_id=row["category_id"],
            name=row["name"],
        ).model_dump(mode="json")
        for row in result.data or []
    ]
    return build_success_response({"items": items})


@router.delete("/admin/restaurants/{restaurant_id}")
def delete_admin_restaurant(restaurant_id: UUID):
    try:
        result = (
            supabase.table("restaurants")
            .select("id")
            .eq("id", str(restaurant_id))
            .limit(1)
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )
    if not result.data:
        return build_error_response(
            404,
            "RESOURCE_NOT_FOUND",
            "식당을 찾을 수 없습니다.",
        )
    try:
        supabase.table("restaurants").update({"is_active": False}).eq(
            "id", str(restaurant_id)
        ).execute()
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "식당을 비활성화하지 못했습니다.",
        )
    return Response(status_code=204)
