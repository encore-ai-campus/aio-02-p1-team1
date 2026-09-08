from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.common.api_client import get_json, post_json
from src.common.components import (
    CHART_DANGER,
    CHART_PRIMARY,
    CHART_SECONDARY,
    render_donut_chart,
    render_download_button,
    render_empty_state,
    render_error_state,
    render_loading_state,
    render_section_title,
    render_toolbar_row,
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
    "cleaning_run_id": "admin_analytics_cleaning_run_id",
    "cleaning_result": "admin_analytics_cleaning_result",
    "summary_result": "admin_analytics_summary_result",
    "selected_claim_text": "admin_analytics_selected_claim_text",
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
    cleaning_run_id = (
        st.session_state.get(ADMIN_ANALYTICS_KEYS["cleaning_run_id"]) or ""
    ).strip()
    if cleaning_run_id:
        params["cleaning_run_id"] = cleaning_run_id

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
    cleaning_run_id = (
        st.session_state.get(ADMIN_ANALYTICS_KEYS["cleaning_run_id"]) or ""
    ).strip()
    if cleaning_run_id:
        params["cleaning_run_id"] = cleaning_run_id
    return params


def build_log_filters(query):
    filters = {
        "error_only": bool(query.get("error_only")),
    }
    endpoint = (query.get("endpoint") or "").strip()
    if endpoint:
        filters["endpoint"] = endpoint
    http_method = query.get("http_method")
    if http_method and http_method != "전체":
        filters["http_method"] = http_method
    status_code = query.get("status_code")
    if status_code:
        filters["status_code"] = int(status_code)
    return filters


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
        st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_run_id"]] = ""
        st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_result"]] = None
        st.session_state[ADMIN_ANALYTICS_KEYS["summary_result"]] = None
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_claim_text"]] = None

    st.session_state.setdefault(ADMIN_ANALYTICS_KEYS["cleaning_run_id"], "")
    st.session_state.setdefault(ADMIN_ANALYTICS_KEYS["cleaning_result"], None)
    st.session_state.setdefault(ADMIN_ANALYTICS_KEYS["summary_result"], None)
    st.session_state.setdefault(ADMIN_ANALYTICS_KEYS["selected_claim_text"], None)


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
    with st.form("admin_analytics_filter_form"):
        with render_toolbar_row():
            render_section_title(
                "조회 조건",
                "기간과 필터를 적용한 뒤 통계와 로그를 조회합니다.",
            )
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                wrap=False,
                width="content",
            ):
                apply_clicked = st.form_submit_button("적용", type="primary")
                reset_clicked = st.form_submit_button("초기화")
                refresh_clicked = st.form_submit_button("새로고침")

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


def split_summary_sections(summary_text):
    if not summary_text:
        return {
            "현황": "판단할 데이터 부족",
            "문제·이상 징후": "판단할 데이터 부족",
            "확인할 조치": "판단할 데이터 부족",
        }

    sections = {
        "현황": "",
        "문제·이상 징후": "",
        "확인할 조치": "",
    }
    current_name = "현황"
    for line in summary_text.splitlines():
        stripped_line = line.strip()
        for section_name in sections:
            if stripped_line.startswith(section_name):
                current_name = section_name
                remainder = stripped_line[len(section_name):].lstrip(" ::-")
                if remainder:
                    sections[current_name] += remainder + "\n"
                stripped_line = ""
                break
        if stripped_line:
            sections[current_name] += stripped_line + "\n"

    for section_name, section_text in sections.items():
        cleaned_text = section_text.strip()
        sections[section_name] = cleaned_text or summary_text.strip()
    return sections


def create_cleaning_run(query):
    return post_json(
        "/admin/log-cleaning-runs",
        json_body={
            "period_start": format_datetime(query["period_start"]),
            "period_end": format_datetime(query["period_end"]),
        },
        access_token=get_access_token(),
        idempotency_key=str(uuid4()),
    )


def create_log_summary(query, cleaning_run_id):
    return post_json(
        "/admin/log-summaries",
        json_body={
            "period_start": format_datetime(query["period_start"]),
            "period_end": format_datetime(query["period_end"]),
            "cleaning_run_id": cleaning_run_id,
            "filters": build_log_filters(query),
        },
        access_token=get_access_token(),
        idempotency_key=str(uuid4()),
    )


def get_log_summary(summary_id):
    return get_json(
        f"/admin/log-summaries/{summary_id}",
        access_token=get_access_token(),
    )


def get_cleaning_run(run_id):
    return get_json(
        f"/admin/log-cleaning-runs/{run_id}",
        access_token=get_access_token(),
    )


def get_api_log_detail(api_log_id):
    return get_json(
        f"/admin/api-logs/{api_log_id}",
        access_token=get_access_token(),
    )


def render_evidence_table(evidence_items):
    if not evidence_items:
        render_empty_state(
            "근거 로그가 없어 요약 주장을 사실로 표시하지 않습니다.",
            next_action="판단할 데이터 부족으로 둡니다.",
        )
        return

    evidence_rows = []
    for item in evidence_items:
        evidence_rows.append(
            {
                "로그 ID": item.get("api_log_id"),
                "발생 시각": item.get("occurred_at"),
                "Method": item.get("http_method"),
                "엔드포인트": item.get("endpoint"),
                "상태": item.get("status_code"),
                "응답시간(ms)": item.get("response_time_ms"),
                "에러 코드": item.get("error_code") or "-",
                "연결 주장": item.get("claim_text") or "-",
            }
        )
    selected = st.dataframe(
        pd.DataFrame(evidence_rows),
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="admin_analytics_evidence_table",
        column_config={"로그 ID": None},
    )
    selected_rows = selected.selection.rows if selected and selected.selection else []
    if selected_rows:
        selected_evidence = evidence_rows[selected_rows[0]]
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_log_id"]] = selected_evidence[
            "로그 ID"
        ]
        claim_text = selected_evidence.get("연결 주장")
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_claim_text"]] = (
            None if claim_text in (None, "-") else claim_text
        )


def render_summary_panel(query):
    with render_toolbar_row():
        render_section_title(
            "LLM 로그 요약",
            "지정 기간의 이상 징후와 주요 이슈를 요약하고, 근거가 된 원본 로그를 함께 봅니다.",
        )
        with st.container(
            horizontal=True,
            vertical_alignment="center",
            gap="small",
            wrap=False,
            width="content",
        ):
            cleaning_clicked = st.button(
                "정제 실행",
                width="content",
                key="admin_analytics_cleaning_button",
            )
            summary_clicked = st.button(
                "요약 실행",
                type="primary",
                width="content",
                key="admin_analytics_summary_button",
            )

    current_cleaning_run_id = (
        st.session_state.get(ADMIN_ANALYTICS_KEYS["cleaning_run_id"]) or ""
    ).strip()

    if cleaning_clicked:
        cleaning_result = create_cleaning_run(query)
        st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_result"]] = cleaning_result
        if cleaning_result.get("ok"):
            cleaning_data = cleaning_result.get("data") or {}
            created_id = (
                cleaning_data.get("id")
                or cleaning_data.get("cleaning_run_id")
            )
            st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_run_id"]] = str(
                created_id or current_cleaning_run_id
            )
            st.session_state[ADMIN_ANALYTICS_KEYS["needs_fetch"]] = True
        st.rerun()

    if summary_clicked:
        cleaning_run_id = current_cleaning_run_id
        st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_run_id"]] = cleaning_run_id
        if not cleaning_run_id:
            render_error_state(
                "요약을 실행하려면 먼저 정제를 실행해 주세요.",
                next_action="정제 실행 후 같은 기간으로 요약을 실행합니다.",
            )
        else:
            summary_result = create_log_summary(query, cleaning_run_id)
            st.session_state[ADMIN_ANALYTICS_KEYS["summary_result"]] = summary_result
            st.rerun()

    cleaning_result = st.session_state.get(ADMIN_ANALYTICS_KEYS["cleaning_result"])
    if cleaning_result and not cleaning_result.get("ok"):
        error_body = cleaning_result.get("error") or {}
        render_error_state(
            error_body.get("message") or "정제 실행에 실패했습니다.",
            request_id=error_body.get("request_id"),
        )
    elif cleaning_result and cleaning_result.get("ok"):
        cleaning_data = cleaning_result.get("data") or {}
        cleaning_status = cleaning_data.get("status")
        cleaning_id = (
            cleaning_data.get("id") or cleaning_data.get("cleaning_run_id")
        )
        if cleaning_status == "running" and cleaning_id:
            polled_cleaning = get_cleaning_run(cleaning_id)
            if polled_cleaning.get("ok"):
                cleaning_data = polled_cleaning.get("data") or cleaning_data
                st.session_state[ADMIN_ANALYTICS_KEYS["cleaning_result"]] = (
                    polled_cleaning
                )
                cleaning_status = cleaning_data.get("status")
        if cleaning_status == "running":
            render_loading_state("로그를 정제하고 있습니다.")
        elif cleaning_status == "failed":
            render_error_state("로그 정제가 실패했습니다.")
        else:
            st.caption(f"정제 상태: {cleaning_status or 'succeeded'}")

    summary_result = st.session_state.get(ADMIN_ANALYTICS_KEYS["summary_result"])
    if summary_result is None:
        render_empty_state(
            "아직 요약을 실행하지 않았습니다.",
            next_action="같은 기간·필터로 정제한 뒤 요약을 실행해 주세요.",
        )
        return

    if not summary_result.get("ok"):
        error_body = summary_result.get("error") or {}
        render_error_state(
            error_body.get("message") or "요약을 불러오지 못했습니다.",
            request_id=error_body.get("request_id"),
        )
        return

    summary_data = summary_result.get("data") or {}
    summary_id = summary_data.get("summary_id") or summary_data.get("id")
    summary_status = summary_data.get("status")
    if summary_status == "running" and summary_id:
        polled_result = get_log_summary(summary_id)
        if polled_result.get("ok"):
            summary_data = polled_result.get("data") or summary_data
            st.session_state[ADMIN_ANALYTICS_KEYS["summary_result"]] = polled_result
            summary_status = summary_data.get("status")

    if summary_status == "running":
        render_loading_state("요약을 생성하고 있습니다.")
        return
    if summary_status == "failed":
        render_error_state(
            "요약 생성이 실패했습니다.",
            next_action="부분 결과를 성공처럼 표시하지 않습니다.",
        )
        return

    evidence_items = summary_data.get("evidence") or []
    summary_text = summary_data.get("summary_text")
    if not evidence_items or not summary_text:
        render_empty_state(
            "판단할 데이터 부족",
            next_action="근거가 없는 내용은 사실로 표시하지 않습니다.",
        )
        return

    sections = split_summary_sections(summary_text)
    with st.container(border=True):
        st.subheader("현황")
        st.write(sections["현황"])
        st.subheader("문제·이상 징후")
        st.write(sections["문제·이상 징후"])
        st.subheader("확인할 조치")
        st.write(sections["확인할 조치"])
        st.caption(
            f"model: {summary_data.get('model_name') or '-'} / prompt: {summary_data.get('prompt_version') or '-'}"
        )
    render_section_title("요약 근거 로그")
    render_evidence_table(evidence_items)
    result = st.session_state.get(ADMIN_ANALYTICS_KEYS["result"]) or {}
    log_items, _total_count = list_api_log_items(
        (result.get("logs") or {}).get("data")
    )
    render_log_detail(log_items)


def render_log_table(log_items, total_count, export_df=None):
    caption = f"전체 {total_count}건, 기본 정렬 occurred_at DESC"
    with render_toolbar_row():
        render_section_title("최근 요청 로그", caption)
        if export_df is not None:
            render_download_button(
                "전체 로그 내려받기",
                export_df,
                "playeat_request_logs.csv",
                "admin_logs_download",
                width="content",
            )

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
        st.session_state[ADMIN_ANALYTICS_KEYS["selected_claim_text"]] = None


def render_log_detail(log_items):
    selected_log_id = st.session_state.get(ADMIN_ANALYTICS_KEYS["selected_log_id"])
    if not selected_log_id:
        st.caption("로그 행이나 요약 근거를 선택하면 상세를 표시합니다.")
        return

    selected_item = next(
        (
            item
            for item in log_items
            if str(item.get("id") or item.get("api_log_id")) == str(selected_log_id)
        ),
        None,
    )
    detail_error = None
    if selected_item is None:
        detail_result = get_api_log_detail(selected_log_id)
        if detail_result.get("ok"):
            selected_item = detail_result.get("data")
        else:
            detail_error = detail_result.get("error") or {}

    with st.container(border=True):
        st.subheader("로그 상세")
        if detail_error:
            render_error_state(
                detail_error.get("message") or "선택한 로그 상세를 불러오지 못했습니다.",
                request_id=detail_error.get("request_id"),
            )
            return
        if selected_item is None:
            render_empty_state("선택한 로그 상세를 찾을 수 없습니다.")
            return

        claim_text = st.session_state.get(ADMIN_ANALYTICS_KEYS["selected_claim_text"])
        if claim_text:
            st.caption(f"요약 연결 주장: {claim_text}")

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


def get_error_next_action(error_body):
    error_code = (error_body or {}).get("code")
    status_code = (error_body or {}).get("status")
    if error_code in {"AUTH_REQUIRED", "TOKEN_EXPIRED"} or status_code == 401:
        return "로그인 화면으로 이동해 다시 인증해 주세요."
    if error_code == "ADMIN_REQUIRED" or status_code == 403:
        return "관리자 권한이 있는 계정으로 다시 시도해 주세요."
    return "기존 화면을 성공 결과처럼 바꾸지 않고 다시 조회하세요."


def build_recent_request_rows(log_items):
    rows = []
    for index, item in enumerate(log_items, start=1):
        rows.append(
            {
                "번호": index,
                "요청 시간": item.get("occurred_at") or "-",
                "음식별": item.get("food_category") or "-",
                "가격대": item.get("price_range") or "-",
                "메뉴 특성": item.get("menu_feature") or "-",
                "검색 키워드": item.get("search_keyword")
                or item.get("endpoint")
                or item.get("endpoint_path")
                or "-",
                "사용자 반응": item.get("user_reaction") or "-",
            }
        )
    return rows


def render_search_ratio_summary():
    render_section_title("검색정보 요약")
    food_column, price_column, feature_column = st.columns(3, gap="medium")
    ratios = {}
    with food_column:
        render_donut_chart("음식별 검색 비율", ratios.get("food") or [])
    with price_column:
        render_donut_chart("가격대별 검색 비율", ratios.get("price") or [])
    with feature_column:
        render_donut_chart("메뉴 특성별 검색 비율", ratios.get("feature") or [])


def render_recent_request_logs(log_result):
    empty_columns = [
        "번호",
        "요청 시간",
        "음식별",
        "가격대",
        "메뉴 특성",
        "검색 키워드",
        "사용자 반응",
    ]
    log_items, _total_count = list_api_log_items(
        log_result.get("data") if log_result.get("ok") else None
    )
    log_df = (
        pd.DataFrame(build_recent_request_rows(log_items))
        if log_result.get("ok")
        else pd.DataFrame(columns=empty_columns)
    )
    export_df = log_df if not log_df.empty else pd.DataFrame(columns=empty_columns)

    with render_toolbar_row():
        render_section_title(
            "최근 요청 로그",
            "원본 API 로그의 시각·엔드포인트를 표시합니다. 음식·가격·반응 컬럼은 해당 필드가 없으면 비웁니다.",
        )
        render_download_button(
            "전체 로그 내려받기",
            export_df,
            "playeat_request_logs.csv",
            "admin_analytics_log_download",
            width="content",
        )

    if not log_result.get("ok"):
        error_body = log_result.get("error") or {}
        render_error_state(
            error_body.get("message") or "요청 로그를 불러오지 못했습니다.",
            request_id=error_body.get("request_id"),
            next_action=get_error_next_action(error_body),
        )
        return
    if log_df.empty:
        render_empty_state("조건에 맞는 요청 로그가 없습니다.")
        return
    st.dataframe(log_df, hide_index=True)


def render_admin_analytics():
    initialize_admin_analytics_state()
    refresh_admin_analytics_if_needed()
    render_search_ratio_summary()
    result = st.session_state.get(ADMIN_ANALYTICS_KEYS["result"])
    if result is None:
        render_loading_state("처음 조회를 준비하고 있습니다.")
        return
    render_recent_request_logs(result.get("logs") or {})

