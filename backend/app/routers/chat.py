"""음식점 추천 챗봇 응답을 만드는 라우터.

주요 역할

1. 음식점 추천 카테고리 옵션 제공
2. 이전 대화 내역 구성
3. Gemini 스트리밍 응답 생성
4. 사용자/AI 메시지 저장
5. 답변 다시 생성
6. 대화 맥락 초기화
7. 사용량 로그 및 피드백 저장
"""

import datetime
import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from google.genai import types

from app.deps import require_own_conversation
from app.db import supabase
from app.gemini_client import (
    GEMINI_MODEL,
    MENU_TYPES,
    PRICE_LEVELS,
    RESTAURANT_CATEGORIES,
    build_system_prompt,
    client,
)
from app.redis_client import r

# 메시지 생성 / 조회
from app.routers.conversations import (
    create_message,
    list_messages,
)

from app.schemas import (
    ChatRequest,
    FeedbackRequest,
    MessageCreate,
    MessageOut,
    RegenerateRequest,
)


# =========================================================
# 기본 설정
# =========================================================

# Gemini에게 전달할 최근 메시지 개수
MAX_HISTORY_MESSAGES = 20


# 맥락 초기화 표시
CONTEXT_RESET_MARKER = (
    "[맥락 초기화] 이 지점 이전의 대화는 "
    "음식점 추천에 사용하지 않습니다."
)


# 우리 DB role → Gemini role
_ROLE_MAP = {
    "user": "user",
    "assistant": "model",
}


# Redis 사용량 로그 최대 개수
MAX_USAGE_LOGS = 50


# =========================================================
# Router
# =========================================================

router = APIRouter(
    prefix="/conversations",
    tags=["chat"],
)


options_router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# =========================================================
# 1. 추천 옵션
# =========================================================

@options_router.get("/options")
def chat_options():
    """
    음식점 추천 화면에서 사용할 선택지를 반환한다.

    restaurant_categories
        한식 / 중식 / 일식 / 양식 / 기타

    menu_types
        매운거 / 든든한거 / 국물여부

    price_levels
        인당가격_하 / 인당가격_중 / 인당가격_상
    """

    return {
        "restaurant_categories": RESTAURANT_CATEGORIES,
        "menu_types": MENU_TYPES,
        "price_levels": PRICE_LEVELS,
        "max_history_messages": MAX_HISTORY_MESSAGES,
    }


# =========================================================
# 2. Gemini에 전달할 이전 대화 구성
# =========================================================

def _build_history(
    conversation_id: UUID,
) -> list[dict]:
    """
    Gemini에게 전달할 이전 대화를 만든다.

    가장 최근 context reset 이후의 대화만 사용한다.
    """

    messages = list_messages(conversation_id)

    # -----------------------------------------------------
    # 마지막 system 메시지 이후의 대화만 사용
    # -----------------------------------------------------

    for index in range(
        len(messages) - 1,
        -1,
        -1,
    ):
        if messages[index]["role"] == "system":
            messages = messages[index + 1:]
            break

    # -----------------------------------------------------
    # user / assistant 메시지만 Gemini에게 전달
    # -----------------------------------------------------

    usable = [
        message
        for message in messages
        if message["role"] in _ROLE_MAP
    ]

    # 최근 메시지만 사용
    recent = usable[-MAX_HISTORY_MESSAGES:]

    return [
        {
            "role": _ROLE_MAP[message["role"]],
            "parts": [
                {
                    "text": message["content"],
                }
            ],
        }
        for message in recent
    ]


# =========================================================
# 3. Redis 로그
# =========================================================

def _usage_log_key(
    conversation_id: UUID,
) -> str:
    return f"usage_log:{conversation_id}"


def _feedback_key(
    conversation_id: UUID,
) -> str:
    return f"feedback:{conversation_id}"


def _log_usage(
    conversation_id: UUID,
    started_at: float,
    usage,
) -> None:
    """
    Gemini 요청 시간과 토큰 사용량을 Redis에 기록한다.
    """

    entry = {
        "requested_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),

        "latency_ms": round(
            (
                time.monotonic()
                - started_at
            )
            * 1000
        ),

        "prompt_tokens": getattr(
            usage,
            "prompt_token_count",
            None,
        ),

        "response_tokens": getattr(
            usage,
            "candidates_token_count",
            None,
        ),

        "total_tokens": getattr(
            usage,
            "total_token_count",
            None,
        ),
    }

    key = _usage_log_key(
        conversation_id
    )

    r.lpush(
        key,
        json.dumps(entry),
    )

    r.ltrim(
        key,
        0,
        MAX_USAGE_LOGS - 1,
    )


# =========================================================
# 4. 피드백
# =========================================================

@router.post(
    "/{conversation_id}/feedback"
)
def save_feedback(
    payload: FeedbackRequest,
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):
    """
    AI 추천 답변에 대한 피드백을 저장한다.
    """

    key = _feedback_key(
        conversation_id
    )

    if payload.value is None:

        r.hdel(
            key,
            str(payload.message_id),
        )

    else:

        r.hset(
            key,
            str(payload.message_id),
            payload.value,
        )

    return {
        "message_id": str(
            payload.message_id
        ),
        "value": payload.value,
    }


@router.get(
    "/{conversation_id}/feedback"
)
def read_feedback(
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):
    """
    현재 대화방의 피드백 상태를 반환한다.
    """

    return r.hgetall(
        _feedback_key(
            conversation_id
        )
    )


# =========================================================
# 5. 사용량 로그
# =========================================================

@router.get(
    "/{conversation_id}/usage-logs"
)
def usage_logs(
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):

    raw = r.lrange(
        _usage_log_key(
            conversation_id
        ),
        0,
        MAX_USAGE_LOGS - 1,
    )

    return [
        json.loads(item)
        for item in raw
    ]


# =========================================================
# 6. 맥락 초기화
# =========================================================

@router.post(
    "/{conversation_id}/reset-context",
    response_model=MessageOut,
)
def reset_context(
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):
    """
    이전 음식 추천 맥락을 초기화한다.

    DB의 기존 메시지를 삭제하지 않고
    이 지점 이후의 메시지만 Gemini에게 전달한다.
    """

    return create_message(
        conversation_id,
        MessageCreate(
            role="system",
            content=CONTEXT_RESET_MARKER,
        ),
    )


# =========================================================
# 7. Gemini 스트리밍 응답
# =========================================================

def _stream_answer(
    conversation_id: UUID,
    contents: list,
):
    """
    Gemini 음식점 추천 응답을 스트리밍한다.

    응답이 끝나면 전체 답변을 DB에 저장한다.
    """

    def event_stream():

        started_at = time.monotonic()

        full_text = ""

        last_usage = None

        try:

            # =============================================
            # Gemini 호출
            # =============================================

            for chunk in (
                client.models
                .generate_content_stream(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            build_system_prompt()
                        )
                    ),
                )
            ):

                if chunk.text:

                    full_text += chunk.text

                    yield (
                        "data: "
                        + json.dumps(
                            {
                                "text": chunk.text
                            }
                        )
                        + "\n\n"
                    )

                if chunk.usage_metadata:

                    last_usage = (
                        chunk.usage_metadata
                    )

            # =============================================
            # 빈 응답
            # =============================================

            if not full_text:

                yield (
                    "data: "
                    + json.dumps(
                        {
                            "error": (
                                "모델이 빈 응답을 "
                                "돌려주었습니다."
                            )
                        }
                    )
                    + "\n\n"
                )

                return

            # =============================================
            # Assistant 메시지 저장
            # =============================================

            saved = create_message(
                conversation_id,
                MessageCreate(
                    role="assistant",
                    content=full_text,
                ),
            )

            # =============================================
            # 사용량 기록
            # =============================================

            _log_usage(
                conversation_id,
                started_at,
                last_usage,
            )

            # =============================================
            # 스트리밍 완료
            # =============================================

            yield (
                "data: "
                + json.dumps(
                    {
                        "done": True,
                        "message_id": str(
                            saved["id"]
                        ),
                    }
                )
                + "\n\n"
            )

        except Exception as e:

            yield (
                "data: "
                + json.dumps(
                    {
                        "error": (
                            f"{type(e).__name__}: "
                            f"{e}"
                        )
                    }
                )
                + "\n\n"
            )

            return

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )


# =========================================================
# 8. 답변 다시 생성
# =========================================================

@router.post(
    "/{conversation_id}/regenerate"
)
def regenerate(
    payload: RegenerateRequest,
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):
    """
    마지막 AI 추천 답변을 삭제하고 다시 생성한다.

    사용자 질문은 유지하고
    마지막 assistant 메시지만 삭제한다.
    """

    messages = list_messages(
        conversation_id
    )

    if (
        not messages
        or messages[-1]["role"]
        != "assistant"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "다시 생성할 "
                "답변이 없습니다."
            ),
        )

    # -----------------------------------------------------
    # 마지막 assistant 메시지 삭제
    # -----------------------------------------------------

    supabase.table(
        "messages"
    ).delete().eq(
        "id",
        messages[-1]["id"],
    ).execute()

    # Redis 캐시 삭제
    r.delete(
        f"messages:{conversation_id}"
    )

    # 삭제 후의 대화 내역
    history = _build_history(
        conversation_id
    )

    if not history:
        raise HTTPException(
            status_code=400,
            detail=(
                "다시 생성할 "
                "질문이 없습니다."
            ),
        )

    return _stream_answer(
        conversation_id,
        history,
    )


# =========================================================
# 9. 채팅
# =========================================================

@router.post(
    "/{conversation_id}/chat"
)
def chat(
    payload: ChatRequest,
    conversation_id: UUID = Depends(
        require_own_conversation
    ),
):
    """
    사용자의 음식 관련 질문을 저장하고
    Gemini 음식 추천 응답을 스트리밍한다.
    """

    # -----------------------------------------------------
    # 기존 대화
    # -----------------------------------------------------

    history = _build_history(
        conversation_id
    )

    # -----------------------------------------------------
    # 사용자 메시지 DB 저장
    # -----------------------------------------------------

    create_message(
        conversation_id,
        MessageCreate(
            role="user",
            content=payload.content,
        ),
    )

    # -----------------------------------------------------
    # Gemini에게 전달할 전체 대화
    # -----------------------------------------------------

    contents = history + [
        {
            "role": "user",
            "parts": [
                {
                    "text": payload.content
                }
            ],
        }
    ]

    # -----------------------------------------------------
    # Gemini 스트리밍 응답
    # -----------------------------------------------------

    return _stream_answer(
        conversation_id,
        contents,
    )