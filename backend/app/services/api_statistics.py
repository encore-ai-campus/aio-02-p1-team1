from app.db import supabase
from app.schemas.api_log import MetricPoint
from app.services.log_cleaning import (
    calculate_p95,
    is_error_status,
    normalize_endpoint,
)


def calculate_error_rate(error_count, request_count):
    if not request_count:
        return None
    return error_count / request_count


def filter_log_row(row, endpoint, http_method, status_code, error_only):
    path = row.get("endpoint_path") or ""
    normalized = row.get("normalized_endpoint") or normalize_endpoint(path)
    if endpoint:
        if endpoint not in (path, normalized) and not path.startswith(endpoint):
            return False
    if http_method and row.get("http_method") != http_method:
        return False
    if status_code is not None and int(row.get("status_code") or 0) != int(status_code):
        return False
    if error_only and not is_error_status(row.get("status_code")):
        return False
    return True


def build_metric_points(rows, endpoint_key="endpoint"):
    grouped = {}
    for row in rows:
        endpoint = row.get(endpoint_key) or normalize_endpoint(row.get("endpoint_path"))
        http_method = row.get("http_method")
        grouped.setdefault((endpoint, http_method), []).append(row)

    points = []
    for (endpoint, http_method), items in sorted(grouped.items()):
        times = [int(item["response_time_ms"]) for item in items]
        request_count = len(items)
        error_count = sum(
            1 for item in items if is_error_status(item.get("status_code"))
        )
        points.append(
            MetricPoint(
                endpoint=endpoint,
                http_method=http_method,
                request_count=request_count,
                error_count=error_count,
                error_rate=calculate_error_rate(error_count, request_count),
                avg_response_time_ms=round(sum(times) / request_count, 2)
                if request_count
                else None,
                p95_response_time_ms=calculate_p95(times),
            )
        )
    return points


def list_statistics_from_cleaning_run(
    cleaning_run_id,
    endpoint=None,
    http_method=None,
    status_code=None,
    error_only=False,
):
    result = (
        supabase.table("api_statistics")
        .select(
            "endpoint, http_method, request_count, error_count, "
            "avg_response_time_ms, p95_response_time_ms"
        )
        .eq("cleaning_run_id", str(cleaning_run_id))
        .execute()
    )
    points = []
    for row in result.data or []:
        if endpoint and row.get("endpoint") != endpoint:
            continue
        if http_method and row.get("http_method") != http_method:
            continue
        request_count = int(row.get("request_count") or 0)
        error_count = int(row.get("error_count") or 0)
        if error_only and error_count == 0:
            continue
        if status_code is not None:
            continue
        points.append(
            MetricPoint(
                endpoint=row["endpoint"],
                http_method=row["http_method"],
                request_count=request_count,
                error_count=error_count,
                error_rate=calculate_error_rate(error_count, request_count),
                avg_response_time_ms=float(row["avg_response_time_ms"])
                if row.get("avg_response_time_ms") is not None
                else None,
                p95_response_time_ms=float(row["p95_response_time_ms"])
                if row.get("p95_response_time_ms") is not None
                else None,
            )
        )
    return points


def list_statistics_from_raw_logs(
    period_start,
    period_end,
    endpoint=None,
    http_method=None,
    status_code=None,
    error_only=False,
):
    query = (
        supabase.table("api_request_logs")
        .select("endpoint_path, http_method, status_code, response_time_ms")
        .gte("occurred_at", period_start.isoformat())
        .lte("occurred_at", period_end.isoformat())
    )
    if http_method:
        query = query.eq("http_method", http_method)
    if status_code is not None:
        query = query.eq("status_code", int(status_code))
    result = query.execute()
    rows = []
    for row in result.data or []:
        normalized = normalize_endpoint(row.get("endpoint_path"))
        row["normalized_endpoint"] = normalized
        if not filter_log_row(
            row, endpoint, http_method, status_code, error_only
        ):
            continue
        rows.append(row)
    return build_metric_points(rows, endpoint_key="normalized_endpoint")
