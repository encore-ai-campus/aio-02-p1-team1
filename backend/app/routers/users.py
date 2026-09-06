"""사용자 정보 관리 API 

메서드   주소                하는 일              성공 코드
POST     /users              사용자 등록           201
GET      /users              사용자 목록(최신순)    200
GET      /users/{user_id}    사용자 한 명 조회      200
PATCH    /users/{user_id}    username 수정         200
DELETE   /users/{user_id}    사용자 삭제           204
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db import supabase

router = APIRouter(prefix="/users", tags=["users"])

# POST "" — 사용자 등록
#   · @router.post("", response_model=UserOut, status_code=201)
#   · insert 하기 전에 select 로 같은 email 이 있는지 먼저 본다
#   · 있으면 raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다")
#   · 반환은 result.data[0]

# GET "" — 사용자 목록
#   · response_model=list[UserOut]
#   · .order("created_at", desc=True) 로 최신 가입순


# GET "/{user_id}" — 한 명 조회. 없으면 404 "사용자를 찾을 수 없습니다"

# PATCH "/{user_id}" — username 수정. 없으면 404

# DELETE "/{user_id}" — 삭제. status_code=204 이므로 아무것도 반환하지 않는다