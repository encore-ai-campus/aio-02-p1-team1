from fastapi import APIRouter

from app.db import supabase
from app.schemas.common import build_error_response, build_success_response
from app.schemas.search_stats import SearchStatPoint, SearchStatsResponse

router = APIRouter(tags=["admin-search-stats"])

STAT_TYPE_FOOD = "0"
STAT_TYPE_PRICE = "1"
STAT_TYPE_FEATURE = "2"


def aggregate_search_stat_points(rows, stat_type):
    totals = {}
    for row in rows:
        if str(row.get("stat_type") or "") != stat_type:
            continue
        label = str(row.get("stat_key") or "").strip()
        if not label:
            continue
        totals[label] = totals.get(label, 0) + int(row.get("count") or 0)
    return [
        SearchStatPoint(label=label, value=value)
        for label, value in sorted(totals.items())
        if value > 0
    ]


@router.get("/admin/search-stats")
def list_search_stats():
    try:
        result = (
            supabase.table("dashboard_search_stats")
            .select("stat_type, stat_key, count")
            .execute()
        )
    except Exception:
        return build_error_response(
            503,
            "DATABASE_UNAVAILABLE",
            "데이터베이스에 연결하지 못했습니다.",
        )

    rows = result.data or []
    payload = SearchStatsResponse(
        food=aggregate_search_stat_points(rows, STAT_TYPE_FOOD),
        price=aggregate_search_stat_points(rows, STAT_TYPE_PRICE),
        feature=aggregate_search_stat_points(rows, STAT_TYPE_FEATURE),
    )
    return build_success_response(payload.model_dump(mode="json"))
