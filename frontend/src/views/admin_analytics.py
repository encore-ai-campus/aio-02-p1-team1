from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

from src.common.api_client import get_json
from src.common.components import (
    CHART_DANGER,
    CHART_PRIMARY,
    CHART_SECONDARY,
    render_empty_state,
    render_error_state,
    render_loading_state,
    render_page_header,
    render_section_title,
)

HTTP_METHOD_OPTIONS = ["전체", "GET", "POST", "PATCH", "DELETE"]
DEFAULT_PAGE_SIZE = 20
ADMIN_ANALYTICS_KEYS = {
    "draft_query": "admin_analytics_draft_query",
    "applied_query": "admin_analytics_applied_query",
    "needs_fetch": "admin_analytics_needs_fetch",
    "is_loading": "admin_analytics_is_loading",
    "result": "admin_analytics_result",
    "selected_log_id": "admin_analytics_selected_log_id",
    "log_page": "admin_analytics_log_page",
}


def get_default_period():
    period_end = datetime.now(timezone.utc)
    period_start = period_end - timedelta(days=7)
    return period_start, period_end


def build_default_query():
    period_start, period_end = get_default_period()
    return {
        "period_start": period_start,
        "period_end": period_end,
        "endpoint": "",
        "http_method": "전체",
        "status_code": None,
        "error_only": False,
        "page": 1,
        "page_size": DEFAULT_PAGE_SIZE,
    }


def format_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def build_statistics_params(query):
    params = {
        "period_start": format_datetime(query["period_start"]),
        "period_end": format_datetime(query["period_end"]),
        "error_only": query["error_only"],
    }

    endpoint = (query.get("endpoint") or "").strip()
    if endpoint:
        params["endpoint"] = endpoint

    http_method = query.get("http_method")
    if http_method and http_method != "전체":
        params["http_method"] = http_method

    status_code = query.get("status_code")
    if status_code:
        params["status_code"] = int(status_code)

    return params


def build_api_log_params(query):
    params = build_statistics_params(query)
    params["page"] = query.get("page", 1)
    params["page_size"] = query.get("page_size", DEFAULT_PAGE_SIZE)
    return params


def get_access_token():
    return st.session_state.get("access_token")


def list_metric_points(payload):
    if isinstance(payload, dict):
        points = payload.get("points")
        if isinstance(points, list):
            return points
        return []
    if isinstance(payload, list):
        return payload
    return []


def list_api_log_items(payload):
    if isinstance(payload, list):
        return payload, len(payload)
    if not isinstance(payload, dict):
        return [], 0

    items = (
        payload.get("items")
        or payload.get("logs")
        or payload.get("results")
        or []
    )
    total_count = payload.get("total_count", payload.get("total", len(items)))
    return items, total_count


def aggregate_request_count(points):
    return sum(int(point.get("request_count") or 0) for point in points)


def aggregate_error_count(points):
    return sum(int(point.get("error_count") or 0) for point in points)


def aggregate_average_response_time(points):
    weighted_total = 0.0
    request_count = 0
    for point in points:
        point_request_count = int(point.get("request_count") or 0)
        average_time = point.get("avg_response_time_ms")
        if average_time is None or point_request_count == 0:
            continue
        weighted_total += float(average_time) * point_request_count
        request_count += point_request_count

    if request_count == 0:
        return None
    return weighted_total / request_count


def aggregate_p95_response_time(points):
    values = [
        float(point["p95_response_time_ms"])
        for point in points
        if point.get("p95_response_time_ms") is not None
    ]
    if not values:
        return None
    return max(values)


def count_unidentified_users(log_items):
    return sum(
        1
        for item in log_items
        if item.get("profile_id") in (None, "")
    )


def fetch_admin_analytics(query):
    access_token = get_access_token()
    statistics_params = build_statistics_params(query)
    log_params = build_api_log_params(query)

    usage_result = get_json(
        "/admin/api-statistics/usage",
        params=statistics_params,
        access_token=access_token,
    )
    latency_result = get_json(
        "/admin/api-statistics/latency",
        params=statistics_params,
        access_token=access_token,
    )
    error_result = get_json(
        "/admin/api-statistics/errors",
        params=statistics_params,
        access_token=access_token,
    )
    log_result = get_json(
        "/admin/api-logs",
        params=log_params,
        access_token=access_token,
    )

    return {
        "usage": usage_result,
        "latency": latency_result,
        "errors": error_result,
        "logs": log_result,
        "fetched_at": datetime.now(timezone.utc),
    }


def initialize_admin_analytics_state():
    if ADMIN_ANALYTICS_KEYS["applied_query"] not in st.session_state:
        default_query = build_default_query()
        st.session_state[ADMIN_ANALYTICS_KEYS["draft_query"]] = default_query.copy()
        st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]] = default_query.copy()
        st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = True
        st.session_state[ADMIN_ANALYTICS_KEYS["is_loading"]] = False
        st.session_state[ADMIN_ANALYTICS_KEYS["result"]] = None
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_log_id"]] = None
        st.session_state[ADMIN_ANALYTICS_KEYS["log_page"]] = 1


def handle_filter_apply(
    period_start,
    period_end,
    endpoint,
    http_method,
    status_code,
    error_only,
):
    applied_query = st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]].copy()
    applied_query["period_start"] = period_start
    applied_query["period_end"] = period_end
    applied_query["endpoint"] = endpoint
    applied_query["http_method"] = http_method
    applied_query["status_code"] = status_code
    applied_query["error_only"] = error_only
    applied_query["page"] = 1
    st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]] = applied_query
    st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = True
    st.session_state[ADMIN_ANALYTICS_KEYS["selected_log_id"]] = None


def handle_filter_reset():
    default_query = build_default_query()
    st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]] = default_query
    st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = True
    st.session_state[ADMIN_ANALYTICS_KEYS["selected_log_id"]] = None
    for widget_key in (
        "admin_analytics_period_input",
        "admin_analytics_endpoint_input",
        "admin_analytics_method_input",
        "admin_analytics_status_input",
        "admin_analytics_error_only_input",
    ):
        st.session_state.pop(widget_key, None)


def handle_refresh():
    if st.session_state.get(ADMIN_ANALYTICS_KEYS["is_loading"]):
        return
    st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = True


def refresh_admin_analytics_if_needed():
    if not st.session_state.get(ADMIN_ANALYTICS_KEYS["needs_fetch"]):
        return

    query = st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]]
    with st.spinner("통계와 원본 로그를 조회합니다."):
        st.session_state[ADMIN_ANALYTICS_KEYS["result"]] = fetch_admin_analytics(
            query
        )
    st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = False


def parse_period_input(period_value, fallback_query):
    if isinstance(period_value, (list, tuple)) and len(period_value) == 2:
        start_date, end_date = period_value
    else:
        start_date = period_value or fallback_query["period_start"].date()
        end_date = start_date

    period_start = datetime.combine(
        start_date,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    now = datetime.now(timezone.utc)
    if end_date == now.date():
        period_end = now
    else:
        period_end = datetime.combine(
            end_date,
            datetime.max.time().replace(microsecond=0),
            tzinfo=timezone.utc,
        )

    if period_start >= period_end:
        period_end = period_start + timedelta(days=1)
    return period_start, period_end


def render_filter_form(query):
    render_section_title("조회 조건")

    with st.form("admin_analytics_filter_form"):
        period_value = st.date_input(
            "조회 기간",
            value=(
                query["period_start"].date(),
                query["period_end"].date(),
            ),
            key="admin_analytics_period_input",
        )
        endpoint = st.text_input(
            "엔드포인트",
            value=query.get("endpoint") or "",
            key="admin_analytics_endpoint_input",
        )
        method_column, status_column, error_column = st.columns(3)
        with method_column:
            http_method = st.selectbox(
                "HTTP Method",
                options=HTTP_METHOD_OPTIONS,
                index=HTTP_METHOD_OPTIONS.index(query.get("http_method") or "전체"),
                key="admin_analytics_method_input",
            )
        with status_column:
            status_code = st.number_input(
                "상태 코드",
                min_value=0,
                max_value=599,
                value=int(query["status_code"] or 0),
                step=1,
                key="admin_analytics_status_input",
                help="0이면 상태 코드 필터를 적용하지 않습니다.",
            )
        with error_column:
            error_only = st.checkbox(
                "에러만 보기",
                value=bool(query.get("error_only")),
                key="admin_analytics_error_only_input",
            )

        apply_column, reset_column, refresh_column = st.columns(3)
        with apply_column:
            apply_clicked = st.form_submit_button("적용", type="primary")
        with reset_column:
            reset_clicked = st.form_submit_button("초기화")
        with refresh_column:
            refresh_clicked = st.form_submit_button("새로고침")

    if apply_clicked:
        period_start, period_end = parse_period_input(period_value, query)
        parsed_status_code = int(status_code) if status_code else None
        handle_filter_apply(
            period_start,
            period_end,
            endpoint,
            http_method,
            parsed_status_code,
            error_only,
        )
        st.rerun()

    if reset_clicked:
        handle_filter_reset()
        st.rerun()

    if refresh_clicked:
        handle_refresh()
        st.rerun()


def render_applied_query_caption(query, fetched_at):
    period_start = query["period_start"].strftime("%Y-%m-%d %H:%M")
    period_end = query["period_end"].strftime("%Y-%m-%d %H:%M")
    refreshed_at = fetched_at.strftime("%Y-%m-%d %H:%M:%S") if fetched_at else "-"
    st.caption(
        f"적용 기간: {period_start} ~ {period_end} UTC / 마지막 갱신 시각: {refreshed_at}"
    )


def render_kpi_row(usage_points, log_items):
    render_section_title("운영 KPI")

    request_count = aggregate_request_count(usage_points)
    error_count = aggregate_error_count(usage_points)
    average_response_time = aggregate_average_response_time(usage_points)
    p95_response_time = aggregate_p95_response_time(usage_points)
    unidentified_count = count_unidentified_users(log_items)
    error_rate = (
        (error_count / request_count) * 100
        if request_count
        else None
    )

    with st.container(horizontal=True):
        st.metric("총 요청 수", f"{request_count:,}", border=True)
        st.metric(
            "고유 사용자 수",
            "계산 불가",
            delta=f"식별 불가 {unidentified_count}건",
            delta_color="off",
            border=True,
            help="통계 API 응답에 고유 사용자 수가 없으면 계산하지 않습니다.",
        )
        st.metric(
            "평균 응답시간",
            "-" if average_response_time is None else f"{average_response_time:.0f} ms",
            border=True,
        )
        st.metric(
            "p95 응답시간",
            "-" if p95_response_time is None else f"{p95_response_time:.0f} ms",
            border=True,
        )
        st.metric(
            "에러율",
            "-" if error_rate is None else f"{error_rate:.1f}%",
            help=f"분모: 총 요청 수 {request_count}건, 분자: 에러 {error_count}건",
            border=True,
        )


def render_points_chart(title, points, y_field, color):
    with st.container(border=True):
        st.subheader(title)
        if not points:
            render_empty_state("표시할 통계가 없습니다.")
            return

        chart_df = pd.DataFrame(points)
        if y_field not in chart_df.columns:
            render_empty_state("표시할 통계가 없습니다.")
            return

        if "endpoint" not in chart_df.columns:
            chart_df["endpoint"] = chart_df.index.astype(str)

        chart_df = chart_df[["endpoint", y_field]].fillna(0)
        st.bar_chart(
            chart_df,
            x="endpoint",
            y=y_field,
            color=color,
            horizontal=True,
            x_label="엔드포인트",
            y_label=y_field,
        )


def render_operation_charts(usage_points, latency_points, error_points):
    render_section_title("API 운영 지표")
    left_column, right_column = st.columns(2, gap="medium")

    with left_column:
        render_points_chart(
            "사용량",
            usage_points,
            "request_count",
            CHART_PRIMARY,
        )
        render_points_chart(
            "에러 건수",
            error_points,
            "error_count",
            CHART_DANGER,
        )

    with right_column:
        render_points_chart(
            "평균 응답시간",
            latency_points,
            "avg_response_time_ms",
            CHART_SECONDARY,
        )
        render_points_chart(
            "p95 응답시간",
            latency_points,
            "p95_response_time_ms",
            CHART_PRIMARY,
        )


def render_summary_panel():
    render_section_title("LLM 요약")
    render_empty_state(
        "요약은 정제 실행 ID가 연결된 뒤에 조회합니다.",
        next_action="근거 없는 내용을 만들지 않습니다.",
    )


def render_log_table(log_items, total_count):
    render_section_title("원본 로그")

    if not log_items:
        render_empty_state("조건에 맞는 원본 로그가 없습니다.")
        return

    table_rows = []
    for item in log_items:
        profile_id = item.get("profile_id")
        table_rows.append(
            {
                "로그 ID": item.get("id") or item.get("api_log_id"),
                "발생 시각": item.get("occurred_at"),
                "Method": item.get("http_method"),
                "엔드포인트": item.get("endpoint") or item.get("endpoint_path"),
                "상태": item.get("status_code"),
                "응답시간(ms)": item.get("response_time_ms"),
                "사용자 식별": "식별" if profile_id else "미식별",
                "에러 코드": item.get("error_code") or "-",
            }
        )

    log_df = pd.DataFrame(table_rows)
    st.caption(f"전체 {total_count}건, 기본 정렬 occurred_at DESC")
    selected = st.dataframe(
        log_df,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="admin_analytics_log_table",
        column_config={
            "로그 ID": None,
            "응답시간(ms)": st.column_config.NumberColumn(
                "응답시간(ms)",
                format="%d",
            ),
        },
    )

    selected_rows = selected.selection.rows if selected and selected.selection else []
    if selected_rows:
        selected_index = selected_rows[0]
        selected_log_id = table_rows[selected_index]["로그 ID"]
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_log_id"]] = selected_log_id


def render_log_detail(log_items):
    selected_log_id = st.session_state.get(ADMIN_ANALYTICS_KEYS["selected_log_id"])
    if not selected_log_id:
        st.caption("로그 행을 선택하면 상세를 표시합니다.")
        return

    selected_item = next(
        (
            item
            for item in log_items
            if str(item.get("id") or item.get("api_log_id")) == str(selected_log_id)
        ),
        None,
    )

    with st.container(border=True):
        st.subheader("로그 상세")
        if selected_item is None:
            render_empty_state("선택한 로그 상세를 찾을 수 없습니다.")
            return

        st.write(
            {
                "api_log_id": selected_item.get("id") or selected_item.get("api_log_id"),
                "request_id": selected_item.get("request_id"),
                "occurred_at": selected_item.get("occurred_at"),
                "http_method": selected_item.get("http_method"),
                "endpoint": selected_item.get("endpoint")
                or selected_item.get("endpoint_path"),
                "status_code": selected_item.get("status_code"),
                "response_time_ms": selected_item.get("response_time_ms"),
                "error_code": selected_item.get("error_code"),
                "profile_id": selected_item.get("profile_id"),
            }
        )


def render_product_metrics_tab():
    render_empty_state(
        "제품 지표는 API 운영 지표와 같은 화면에 합산하지 않습니다.",
        next_action="제품 통계 API가 연결되면 이 탭에서 별도로 표시합니다.",
    )


def get_first_error(result):
    for key in ("usage", "latency", "errors", "logs"):
        item = result.get(key) or {}
        if not item.get("ok"):
            return item.get("error") or {
                "message": "조회에 실패했습니다.",
                "request_id": None,
            }
    return None


def get_error_next_action(error_body):
    error_code = (error_body or {}).get("code")
    status_code = (error_body or {}).get("status")
    if error_code in {"AUTH_REQUIRED", "TOKEN_EXPIRED"} or status_code == 401:
        return "로그인 화면으로 이동해 다시 인증해 주세요."
    if error_code == "ADMIN_REQUIRED" or status_code == 403:
        return "관리자 권한이 있는 계정으로 다시 시도해 주세요."
    return "기존 화면을 성공 결과처럼 바꾸지 않고 다시 조회하세요."


def render_admin_analytics():
    initialize_admin_analytics_state()
    render_page_header(
        "검색정보분석",
        "기간과 필터를 적용한 뒤 API 사용량, 응답시간, 에러율과 원본 로그를 확인합니다.",
    )

    query = st.session_state[ADMIN_ANALYTICS_KEYS["applied_query"]]
    render_filter_form(query)
    refresh_admin_analytics_if_needed()
    result = st.session_state.get(ADMIN_ANALYTICS_KEYS["result"])

    if result is None:
        render_loading_state("처음 조회를 준비하고 있습니다.")
        return

    render_applied_query_caption(query, result.get("fetched_at"))

    first_error = get_first_error(result)
    operation_tab, product_tab = st.tabs(["API 운영 지표", "제품 지표"])

    with operation_tab:
        if first_error:
            render_error_state(
                first_error.get("message") or "조회에 실패했습니다.",
                request_id=first_error.get("request_id"),
                next_action=get_error_next_action(first_error),
            )
        else:
            usage_points = list_metric_points(result["usage"]["data"])
            latency_points = list_metric_points(result["latency"]["data"])
            error_points = list_metric_points(result["errors"]["data"])
            log_items, total_count = list_api_log_items(result["logs"]["data"])

            if not usage_points and not log_items:
                render_empty_state("선택한 기간에 표시할 운영 데이터가 없습니다.")
            else:
                render_kpi_row(usage_points, log_items)
                render_operation_charts(
                    usage_points,
                    latency_points,
                    error_points,
                )
                render_summary_panel()
                render_log_table(log_items, total_count)
                render_log_detail(log_items)

    with product_tab:
        render_product_metrics_tab()
