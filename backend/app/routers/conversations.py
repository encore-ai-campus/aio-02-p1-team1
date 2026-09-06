"""대화·메시지 API (실습 6·7).

메서드   주소                                  하는 일                성공 코드
POST     /conversations                        대화 생성               201
GET      /conversations?user_id=               사용자별 대화 목록       200
POST     /conversations/{id}/messages          메시지 저장             201
GET      /conversations/{id}/messages          메시지 목록             200
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import supabase

router = APIRouter(prefix="/conversations", tags=["conversations"])

# POST "" — 대화 생성
#   · insert 전에 users 에 그 user_id 가 있는지 확인한다.
#     DB의 외래키도 막아주지만 그대로 두면 500 이 난다. 먼저 확인해 404 로 알리는 편이 친절하다.
#   · 없으면 404 "사용자를 찾을 수 없습니다"

# GET "" — 사용자별 대화 목록
#   · user_id 는 주소 뒤 ?user_id=... 로 온다. 함수 인자에 그냥 적으면 된다.
#   · 기본값을 주지 않으면 필수가 되고, 빠뜨리면 FastAPI 가 422 로 막는다.
#   · 최신순 정렬

# POST "/{conversation_id}/messages" — 메시지 저장
#   · 대화가 없으면 404 "대화를 찾을 수 없습니다"

# GET "/{conversation_id}/messages" — 메시지 목록
#   · 대화가 없으면 404
#   · .order("created_at", desc=False)
