import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from supabase import create_client

from app.db import supabase


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(login_info: LoginRequest):
    auth_client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_PUBLISHABLE_KEY"],
    )

    try:
        result = auth_client.auth.sign_in_with_password(
            {
                "email": login_info.email,
                "password": login_info.password,
            }
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if result.user is None or result.session is None:
        raise HTTPException(
            status_code=401,
            detail="로그인에 실패했습니다.",
        )

    profile_result = (
        supabase.table("profiles")
        .select(
            "id, profile_nickname, profile_status, profile_type"
        )
        .eq("id", str(result.user.id))
        .execute()
    )

    if not profile_result.data:
        raise HTTPException(
            status_code=404,
            detail="사용자 프로필을 찾을 수 없습니다.",
        )

    profile = profile_result.data[0]

    if profile["profile_status"] != "1":
        raise HTTPException(
            status_code=403,
            detail="사용할 수 없는 계정입니다.",
        )

    return {
        "access_token": result.session.access_token,
        "token_type": "bearer",
        "user": {
            "id": str(result.user.id),
            "email": result.user.email,
            "nickname": profile["profile_nickname"],
            "profile_type": profile["profile_type"],
        },
    }