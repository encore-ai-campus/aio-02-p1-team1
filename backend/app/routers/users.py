from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, HTTPException, status

from app.db import supabase, create_auth_client
from app.schemas.user import (
    ResponseMeta,
    SignUpRequest,
    SignUpResponse,
    SuccessResponse,
)

router = APIRouter(prefix="/users", tags=["users"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# 표준 에러 응답 포맷 생성 함수
def create_error_response(status_code: int, code: str, message: str, details: list = None):
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "status": status_code,
                "code": code,
                "message": message,
                "details": details or [],
                "request_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    )

@auth_router.post(
    "/signups",
    response_model=SuccessResponse[SignUpResponse],
    status_code=status.HTTP_201_CREATED
)
def create_user(request: SignUpRequest):
    # 1. 닉네임 중복 확인 (profiles 테이블)
    nickname_check = supabase.table("profiles").select("id").eq("profile_nickname", request.nickname).execute()
    if nickname_check.data:
        raise create_error_response(409, "NICKNAME_CONFLICT", "이미 사용 중인 닉네임입니다.")

    # 2. 인증 요청용 auth_client 생성
    auth_client = create_auth_client()
    new_user_id = None

    try:
        # 3. Supabase Auth에 계정 생성
        auth_response = auth_client.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })

        if not auth_response.user:
            raise create_error_response(409, "EMAIL_CONFLICT", "이미 등록된 이메일입니다.")
        
        new_user_id = auth_response.user.id

        # 4. profiles 테이블에 사용자 정보 저장
        profile_data = {
            "id": new_user_id,
            "profile_nickname": request.nickname,
            "profile_type": "1",  # 1: 일반 사용자
            "profile_status": "1" # 1: 활성 상태
        }
        profile_result = supabase.table("profiles").insert(profile_data).execute()
        
        if not profile_result.data:
            raise Exception("프로필 저장에 실패했습니다.")

        # 5. user_consents 테이블에 약관 동의 이력 저장 (버전: terms-v1.0, privacy-v1.0)
        consents_data = [
            {
                "profile_id": new_user_id,
                "consent_type": "terms",
                "consent_version": "terms-v1.0",
                "is_agreed": request.terms_agreed
            },
            {
                "profile_id": new_user_id,
                "consent_type": "privacy",
                "consent_version": "privacy-v1.0",
                "is_agreed": request.privacy_agreed
            }
        ]
        supabase.table("user_consents").insert(consents_data).execute()

        # 6. 성공 결과 반환
        return SuccessResponse(
            data=SignUpResponse(
                user_id=new_user_id,
                email=request.email,
                nickname=request.nickname,
                created_at=profile_result.data[0]["profile_created_at"]
            ),
            meta=ResponseMeta(
                request_id=uuid.uuid4(),
                timestamp=datetime.now(timezone.utc)
            )
        )

    except Exception as e:
        # 에러 발생 시 Supabase Auth에 생성된 계정 롤백(삭제) 처리
        if new_user_id:
            try:
                supabase.auth.admin.delete_user(new_user_id)
            except Exception:
                pass

        if isinstance(e, HTTPException):
            raise e
            
        raise create_error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="회원가입 처리 중 오류가 발생했습니다.",
            details=[{"field": "server", "reason": str(e)}]
        )