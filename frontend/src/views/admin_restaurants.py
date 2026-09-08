from uuid import uuid4

import pandas as pd
import streamlit as st

from src.common.api_client import (
    delete_json,
    get_json,
    list_resource_items,
    post_json,
)
from src.common.components import (
    render_empty_state,
    render_error_state,
    render_page_header,
    render_section_title,
)

DEFAULT_PAGE_SIZE = 20
RESTAURANT_STATE_KEYS = {
    "needs_fetch": "admin_restaurants_needs_fetch",
    "result": "admin_restaurants_result",
    "selected_id": "admin_restaurants_selected_id",
    "detail": "admin_restaurants_detail",
    "page": "admin_restaurants_page",
    "keyword": "admin_restaurants_keyword",
    "category_id": "admin_restaurants_category_id",
}


def get_access_token():
    return st.session_state.get("access_token")


def initialize_restaurant_state():
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["needs_fetch"], True)
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["result"], None)
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["selected_id"], None)
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["detail"], None)
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["page"], 1)
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["keyword"], "")
    st.session_state.setdefault(RESTAURANT_STATE_KEYS["category_id"], None)


def list_category_options(payload):
    items, _total_count = list_resource_items(payload)
    options = [{"id": None, "name": "전체"}]
    for item in items:
        options.append(
            {
                "id": item.get("id") or item.get("category_id"),
                "name": item.get("name") or item.get("category_name") or "이름 없음",
            }
        )
    return options


def fetch_restaurant_list():
    params = {
        "page": st.session_state[RESTAURANT_STATE_KEYS["page"]],
        "page_size": DEFAULT_PAGE_SIZE,
    }
    keyword = (st.session_state.get(RESTAURANT_STATE_KEYS["keyword"]) or "").strip()
    if keyword:
        params["name"] = keyword
    category_id = st.session_state.get(RESTAURANT_STATE_KEYS["category_id"])
    if category_id:
        params["category_id"] = category_id

    access_token = get_access_token()
    restaurant_result = get_json(
        "/restaurants",
        params=params,
        access_token=access_token,
    )
    category_result = get_json(
        "/restaurant-categories",
        access_token=access_token,
    )
    return {
        "restaurants": restaurant_result,
        "categories": category_result,
    }


def fetch_restaurant_detail(restaurant_id):
    return get_json(
        f"/restaurants/{restaurant_id}",
        access_token=get_access_token(),
    )


def refresh_restaurants_if_needed():
    if not st.session_state.get(RESTAURANT_STATE_KEYS["needs_fetch"]):
        return
    with st.spinner("식당 목록을 조회합니다."):
        st.session_state[RESTAURANT_STATE_KEYS["result"]] = fetch_restaurant_list()
    st.session_state[RESTAURANT_STATE_KEYS["needs_fetch"]] = False


def render_restaurant_filters(category_options):
    render_section_title("조회 조건")
    with st.form("admin_restaurant_filter_form"):
        keyword = st.text_input(
            "식당명",
            value=st.session_state.get(RESTAURANT_STATE_KEYS["keyword"]) or "",
            key="admin_restaurant_keyword_input",
        )
        category_names = [item["name"] for item in category_options]
        selected_name = st.selectbox(
            "음식 카테고리",
            options=category_names,
            key="admin_restaurant_category_input",
        )
        apply_clicked = st.form_submit_button("적용", type="primary")
        reset_clicked = st.form_submit_button("초기화")

    if apply_clicked:
        selected_category = next(
            (item for item in category_options if item["name"] == selected_name),
            {"id": None},
        )
        st.session_state[RESTAURANT_STATE_KEYS["keyword"]] = keyword
        st.session_state[RESTAURANT_STATE_KEYS["category_id"]] = selected_category["id"]
        st.session_state[RESTAURANT_STATE_KEYS["page"]] = 1
        st.session_state[RESTAURANT_STATE_KEYS["needs_fetch"]] = True
        st.rerun()

    if reset_clicked:
        st.session_state[RESTAURANT_STATE_KEYS["keyword"]] = ""
        st.session_state[RESTAURANT_STATE_KEYS["category_id"]] = None
        st.session_state[RESTAURANT_STATE_KEYS["page"]] = 1
        st.session_state[RESTAURANT_STATE_KEYS["needs_fetch"]] = True
        st.session_state.pop("admin_restaurant_keyword_input", None)
        st.session_state.pop("admin_restaurant_category_input", None)
        st.rerun()


def render_create_restaurant_form():
    render_section_title("식당 등록")
    with st.form("admin_restaurant_create_form"):
        restaurant_name = st.text_input("식당명")
        kakao_place_id = st.text_input("Kakao 장소 ID")
        address = st.text_input("주소")
        phone = st.text_input("전화번호")
        submitted = st.form_submit_button("등록", type="primary")

    if not submitted:
        return

    if not restaurant_name.strip() or not kakao_place_id.strip():
        render_error_state(
            "식당명과 Kakao 장소 ID는 필수입니다.",
            next_action="입력값을 확인한 뒤 다시 등록해 주세요.",
        )
        return

    result = post_json(
        "/admin/restaurants",
        json_body={
            "name": restaurant_name.strip(),
            "kakao_place_id": kakao_place_id.strip(),
            "address": address.strip() or None,
            "phone": phone.strip() or None,
        },
        access_token=get_access_token(),
        idempotency_key=str(uuid4()),
    )
    if result["ok"]:
        st.success("식당을 등록했습니다.")
        st.session_state[RESTAURANT_STATE_KEYS["needs_fetch"]] = True
        st.rerun()
        return

    error_body = result.get("error") or {}
    render_error_state(
        error_body.get("message") or "식당을 등록하지 못했습니다.",
        request_id=error_body.get("request_id"),
    )


def render_restaurant_table(items, total_count):
    render_section_title("식당 목록")
    if not items:
        render_empty_state("조건에 맞는 식당이 없습니다.")
        return

    table_rows = []
    for item in items:
        table_rows.append(
            {
                "식당 ID": item.get("id") or item.get("restaurant_id"),
                "식당명": item.get("name"),
                "주소": item.get("address")
                or item.get("road_address")
                or item.get("lot_address")
                or "-",
                "전화번호": item.get("phone") or "-",
                "사용 여부": "사용" if item.get("is_active", True) else "비활성",
            }
        )

    st.caption(f"전체 {total_count}건")
    selected = st.dataframe(
        pd.DataFrame(table_rows),
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="admin_restaurant_table",
        column_config={"식당 ID": None},
    )
    selected_rows = selected.selection.rows if selected and selected.selection else []
    if selected_rows:
        selected_id = table_rows[selected_rows[0]]["식당 ID"]
        st.session_state[RESTAURANT_STATE_KEYS["selected_id"]] = selected_id
        st.session_state[RESTAURANT_STATE_KEYS["detail"]] = fetch_restaurant_detail(
            selected_id
        )


def render_restaurant_detail():
    selected_id = st.session_state.get(RESTAURANT_STATE_KEYS["selected_id"])
    if not selected_id:
        st.caption("목록에서 식당을 선택하면 상세와 메뉴를 표시합니다.")
        return

    detail_result = st.session_state.get(RESTAURANT_STATE_KEYS["detail"])
    with st.container(border=True):
        st.subheader("식당 상세")
        if not detail_result:
            render_empty_state("선택한 식당 상세가 없습니다.")
            return
        if not detail_result.get("ok"):
            error_body = detail_result.get("error") or {}
            render_error_state(
                error_body.get("message") or "식당 상세를 불러오지 못했습니다.",
                request_id=error_body.get("request_id"),
            )
            return

        restaurant = detail_result.get("data") or {}
        st.write(
            {
                "restaurant_id": restaurant.get("id") or selected_id,
                "name": restaurant.get("name"),
                "address": restaurant.get("address")
                or restaurant.get("road_address"),
                "phone": restaurant.get("phone"),
                "kakao_place_id": restaurant.get("kakao_place_id"),
                "kakao_place_url": restaurant.get("kakao_place_url"),
                "is_active": restaurant.get("is_active", True),
            }
        )
        menus = restaurant.get("menus") or []
        if menus:
            st.dataframe(pd.DataFrame(menus), hide_index=True)
        else:
            st.caption("등록된 메뉴가 없습니다.")

        if st.button("추천에서 제외", type="primary", key="admin_deactivate_restaurant"):
            deactivate_result = delete_json(
                f"/admin/restaurants/{selected_id}",
                access_token=get_access_token(),
            )
            if deactivate_result["ok"]:
                st.success("식당을 비활성화했습니다. 과거 추천·평가는 유지됩니다.")
                st.session_state[RESTAURANT_STATE_KEYS["needs_fetch"]] = True
                st.rerun()
            else:
                error_body = deactivate_result.get("error") or {}
                render_error_state(
                    error_body.get("message") or "비활성화에 실패했습니다.",
                    request_id=error_body.get("request_id"),
                )


def render_admin_restaurants():
    initialize_restaurant_state()
    render_page_header(
        "식당정보",
        "식당·메뉴·카테고리를 조회하고, 신규 추천에서 제외할 식당은 비활성화합니다.",
    )
    refresh_restaurants_if_needed()
    result = st.session_state.get(RESTAURANT_STATE_KEYS["result"])
    if result is None:
        render_empty_state("식당 목록을 아직 조회하지 않았습니다.")
        return

    restaurant_result = result.get("restaurants") or {}
    category_result = result.get("categories") or {}
    category_options = list_category_options(
        category_result.get("data") if category_result.get("ok") else []
    )
    render_restaurant_filters(category_options)

    if not restaurant_result.get("ok"):
        error_body = restaurant_result.get("error") or {}
        render_error_state(
            error_body.get("message") or "식당 목록을 불러오지 못했습니다.",
            request_id=error_body.get("request_id"),
            next_action="FastAPI 식당 조회 API 연결 후 다시 확인해 주세요.",
        )
        render_create_restaurant_form()
        return

    items, total_count = list_resource_items(restaurant_result.get("data"))
    render_restaurant_table(items, total_count)
    render_restaurant_detail()
    render_create_restaurant_form()
