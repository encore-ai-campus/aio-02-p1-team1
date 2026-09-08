import os

import httpx

DEFAULT_FASTAPI_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 10.0


def get_fastapi_base_url():
    return os.getenv("FASTAPI_BASE_URL", DEFAULT_FASTAPI_BASE_URL)


def _build_error_body(status_code, payload):
    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error_body = payload["error"]
        return {
            "status": error_body.get("status", status_code),
            "code": error_body.get("code", "UNKNOWN_ERROR"),
            "message": error_body.get("message", "요청을 처리하지 못했습니다."),
            "request_id": error_body.get("request_id"),
        }

    return {
        "status": status_code,
        "code": "UNKNOWN_ERROR",
        "message": "요청을 처리하지 못했습니다.",
        "request_id": None,
    }


def fetch_json(
    method,
    path,
    params=None,
    json_body=None,
    access_token=None,
):
    headers = {"Accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    url = f"{get_fastapi_base_url()}{path}"

    try:
        response = httpx.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except httpx.RequestError:
        return {
            "ok": False,
            "status_code": 0,
            "data": None,
            "error": {
                "status": 0,
                "code": "NETWORK_ERROR",
                "message": "FastAPI 서버에 연결하지 못했습니다.",
                "request_id": None,
            },
        }

    payload = None
    if response.content:
        try:
            payload = response.json()
        except ValueError:
            payload = None

    if response.is_success:
        if isinstance(payload, dict) and "data" in payload:
            data = payload["data"]
        else:
            data = payload
        return {
            "ok": True,
            "status_code": response.status_code,
            "data": data,
            "error": None,
        }

    return {
        "ok": False,
        "status_code": response.status_code,
        "data": None,
        "error": _build_error_body(response.status_code, payload),
    }


def get_json(path, params=None, access_token=None):
    return fetch_json(
        "GET",
        path,
        params=params,
        access_token=access_token,
    )
