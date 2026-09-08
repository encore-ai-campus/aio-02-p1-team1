from fastapi import APIRouter, Query

from app.db import supabase
from app.schemas.common import build_error_response, build_success_response
from app.schemas.feedback import AdminFeedbackCounts, AdminFeedbackItem

router = APIRouter(tags=["admin-feedback"])


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


def get_feedback_value_counts():
    counts = {"1": 0, "2": 0, "3": 0}
    result = supabase.table("feedback").select("feedback_value").execute()
    for row in result.data or []:
        value = str(row.get("feedback_value") or "")
        if value in counts:
            counts[value] += 1
    return AdminFeedbackCounts(
        feedback_1=counts["1"],
        feedback_2=counts["2"],
        feedback_3=counts["3"],
    )


def build_admin_feedback_item(row, matched_tags):
    restaurant = row.get("restaurants") if isinstance(row.get("restaurants"), dict) else {}
    category = restaurant.get("restaurant_categories")
    category_name = category.get("name") if isinstance(category, dict) else None
    return AdminFeedbackItem(
        feedback_id=row["feedback_id"],
        profile_id=row["profile_id"],
        conversation_id=row["conversation_id"],
        restaurant_id=row["restaurant_id"],
        restaurant_name=restaurant.get("name"),
        category_name=category_name,
        feedback_value=str(row["feedback_value"]),
        matched_tags=matched_tags,
        created_at=row["created_at"],
        updated_at=row.get("updated_at"),
    ).model_dump(mode="json")


@router.get("/admin/feedback")
def list_admin_feedback(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    start = (page - 1) * page_size
    end = start + page_size - 1
    try:
        result = (
            supabase.table("feedback")
            .select(
                "feedback_id, profile_id, conversation_id, restaurant_id, "
                "feedback_value, created_at, updated_at, "
                "restaurants(name, restaurant_categories(name))",
                count="exact",
            )
            .order("created_at", desc=True)
            .range(start, end)
            .execute()
        )
        counts = get_feedback_value_counts()
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    rows = result.data or []
    restaurant_ids = [row["restaurant_id"] for row in rows]
    try:
        tags_by_restaurant_id = list_tags_by_restaurant_ids(restaurant_ids)
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    items = [
        build_admin_feedback_item(
            row,
            tags_by_restaurant_id.get(row["restaurant_id"], []),
        )
        for row in rows
    ]
    return build_success_response(
        {
            "items": items,
            "counts": counts.model_dump(mode="json"),
        },
        page=page,
        page_size=page_size,
        total_count=result.count or 0,
    )
