import random
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

@router.get("/restaurants/search")
def search_restaurants(
    category: str | None = Query(default=None),
    menu_types: list[str] | None = Query(default=None),
    price_level: str | None = Query(default=None),
):
    """
    사용자가 선택한 조건과 가장 많이 일치하는 식당을 조회한다.

    모든 조건을 만족할 필요는 없다.
    음식문화권과 태그가 일치할 때마다 1점을 부여하고
    점수가 높은 식당부터 반환한다.
    """

    # 1. 활성화된 식당 전체 조회
    try:
        result = (
            supabase.table("restaurants")
            .select("*, restaurant_categories(name)")
            .eq("is_active", True)
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
        return build_success_response(
            {
                "items": None,
            }
        )

    # 2. 식당 ID 목록
    restaurant_ids = [
        row["id"]
        for row in rows
    ]

    # 3. 메뉴 / 태그 조회
    try:
        menus_by_restaurant_id = (
            list_menus_by_restaurant_ids(
                restaurant_ids
            )
        )

        tags_by_restaurant_id = (
            list_tags_by_restaurant_ids(
                restaurant_ids
            )
        )

    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    # 4. 사용자가 선택한 태그 정리
    required_tags = []

    if menu_types:
        required_tags.extend(menu_types)

    if price_level:
        required_tags.append(price_level)

    # 5. 식당별 점수 계산
    scored_items = []

    for row in rows:

        restaurant_id = row["id"]

        restaurant_tags = tags_by_restaurant_id.get(
            restaurant_id,
            [],
        )

        # 점수
        score = 0

        matched_conditions = []

        # 음식문화권 비교
        restaurant_category = get_category_name(row)

        if category and restaurant_category == category:
            score += 1

            matched_conditions.append(
                category
            )

        # 태그 비교
        for tag in required_tags:

            if tag in restaurant_tags:
                score += 1

                matched_conditions.append(
                    tag
                )

        # 총 선택 조건 개수
        total_conditions = len(required_tags)

        if category:
            total_conditions += 1

        # 기본 식당 데이터
        item = build_restaurant_item(
            row,
            menus_by_restaurant_id.get(
                restaurant_id,
                [],
            ),
            restaurant_tags,
        )

        # 추천 관련 정보 추가
        item["match_score"] = score

        item["total_conditions"] = total_conditions

        item["matched_conditions"] = matched_conditions

        # 일치율
        if total_conditions > 0:
            item["match_rate"] = round(
                score / total_conditions * 100,
                1,
            )
        else:
            item["match_rate"] = 0

        scored_items.append(item)

    # 6. 하나도 맞지 않는 식당 제거
    if category or required_tags:
        scored_items = [
            item
            for item in scored_items
            if item["match_score"] > 0
        ]

    # 추천할 식당이 없는 경우
    if not scored_items:
        return build_success_response(
            {
                "item": None,
            }
        )

    # 7. 가장 높은 점수 찾기
    max_score = max(
        item["match_score"]
        for item in scored_items
    )

    # 8. 최고 점수인 식당들만 추리기
    top_items = [
        item
        for item in scored_items
        if item["match_score"] == max_score
    ]

    # 9. 최고 점수 식당 중 하나 랜덤 선택
    item = random.choice(top_items)

    return build_success_response(
        {
            "item": item,
        }
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


@router.get("/restaurant-tags/{category_id}")
def list_restaurant_tags_by_category(category_id: UUID):
    try:
        result = (
            supabase.table("restaurant_tags")
            .select("id, category_id, name")
            .eq("category_id", str(category_id))
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


