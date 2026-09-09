from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends

from app.db import supabase, get_anon_client
from app.deps import get_current_user
from app.schemas.user import (
    CurrentUser,
    ResponseMeta,
    SignUpRequest,
    SignUpResponse,
    SuccessResponse,
    NicknameUpdateRequest,
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
    auth_client = get_anon_client()
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

# 현재 로그인한 사용자 정보 조회하기
@router.get("/me")
def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
):
    # 현재 사용자의 프로필 조회하기
    profile_result = (
        supabase
        .table("profiles")
        .select("profile_nickname")
        .eq("id", current_user.id)
        .single()
        .execute()
    )

    # 프로필이 없는 경우
    if not profile_result.data:
        raise create_error_response(
            404,
            "PROFILE_NOT_FOUND",
            "사용자 프로필을 찾을 수 없습니다.",
        )

    # 마이페이지에 필요한 사용자 정보 반환하기
    return {
        "email": current_user.email,
        "nickname": profile_result.data["profile_nickname"],
    }

# 자주 사용하는 태그 조회하기
@router.get("/me/tags")
def get_my_tags(
    current_user: CurrentUser = Depends(get_current_user),
):
    # 현재 사용자가 좋아요를 누른 식당 조회하기
    feedback_result = (
        supabase
        .table("feedback")
        .select("restaurant_id")
        .eq("profile_id", current_user.id)
        .eq("feedback_value", "3")
        .execute()
    )

    # 좋아요한 식당이 없으면 안내 문구 반환하기
    if not feedback_result.data:
        return {
            "tags": [],
            "message": "아직 사용한 태그가 없습니다."
        }

    restaurant_ids = [
        feedback["restaurant_id"]
        for feedback in feedback_result.data
    ]

    # 좋아요한 식당에 연결된 태그 조회하기
    tag_map_result = (
        supabase
        .table("restaurant_tag_map")
        .select("tag_id")
        .in_("restaurant_id", restaurant_ids)
        .execute()
    )

    # 연결된 태그가 없으면 안내 문구 반환하기
    if not tag_map_result.data:
        return {
            "tags": [],
            "message": "아직 사용한 태그가 없습니다."
        }

    # 태그별 등장 횟수 계산하기
    tag_counts = {}

    for tag_map in tag_map_result.data:
        tag_id = tag_map["tag_id"]

        if tag_id in tag_counts:
            tag_counts[tag_id] += 1
        else:
            tag_counts[tag_id] = 1

    # 많이 등장한 태그 순으로 정렬하기
    sorted_tags = sorted(
        tag_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    tags = []

    # 최대 3개의 태그만 조회하기
    for tag_id, _ in sorted_tags[:3]:
        tag_result = (
            supabase
            .table("restaurant_tags")
            .select("name")
            .eq("id", tag_id)
            .single()
            .execute()
        )

        if tag_result.data:
            tags.append(tag_result.data["name"])

    # 실제 존재하는 태그만 반환하기
    if tags:
        return {
            "tags": tags
        }

    # 최종적으로 조회된 태그가 하나도 없는 경우
    return {
        "tags": [],
        "message": "아직 사용한 태그가 없습니다."
    }

# 최근 좋아요 식당 조회하기
@router.get("/me/likes")
def get_my_likes(
    current_user: CurrentUser = Depends(get_current_user),
):
    # 현재 사용자가 좋아요를 누른 식당을 최근 순으로 조회하기
    feedback_result = (
        supabase
        .table("feedback")
        .select("restaurant_id")
        .eq("profile_id", current_user.id)
        .eq("feedback_value", "3")
        .order("created_at", desc=True)
        .limit(3)
        .execute()
    )

    # 좋아요한 식당이 없으면 빈 목록 반환하기
    if not feedback_result.data:
        return {
            "restaurants": []
        }

    restaurants = []

    # 좋아요한 식당의 정보 조회하기
    for feedback in feedback_result.data:
        restaurant_result = (
            supabase
            .table("restaurants")
            .select("id, name, address")
            .eq("id", feedback["restaurant_id"])
            .single()
            .execute()
        )

        if restaurant_result.data:
            restaurants.append(restaurant_result.data)

    # 최근 좋아요 식당 반환하기
    return {
        "restaurants": restaurants
    }

# 선호 음식 카테고리 비율 조회하기
@router.get("/me/categories")
def get_my_categories(
    current_user: CurrentUser = Depends(get_current_user),
):
    # 현재 사용자가 좋아요를 누른 식당 조회하기
    feedback_result = (
        supabase
        .table("feedback")
        .select("restaurant_id")
        .eq("profile_id", current_user.id)
        .eq("feedback_value", "3")
        .execute()
    )

    # 좋아요한 식당이 없으면 빈 목록 반환하기
    if not feedback_result.data:
        return {
            "categories": []
        }

    restaurant_ids = [
        feedback["restaurant_id"]
        for feedback in feedback_result.data
    ]

    # 좋아요한 식당들의 카테고리 조회하기
    restaurant_result = (
        supabase
        .table("restaurants")
        .select("category_id")
        .in_("id", restaurant_ids)
        .execute()
    )

    # 카테고리 정보가 없으면 빈 목록 반환하기
    if not restaurant_result.data:
        return {
            "categories": []
        }

    # 카테고리별 개수 계산하기
    category_counts = {}

    for restaurant in restaurant_result.data:
        category_id = restaurant["category_id"]

        if category_id in category_counts:
            category_counts[category_id] += 1
        else:
            category_counts[category_id] = 1

    total_count = len(restaurant_result.data)
    categories = []

    # 카테고리 이름과 비율 조회하기
    for category_id, count in category_counts.items():
        category_result = (
            supabase
            .table("restaurant_categories")
            .select("name")
            .eq("id", category_id)
            .single()
            .execute()
        )

        if category_result.data:
            categories.append({
                "name": category_result.data["name"],
                "percentage": round(count / total_count * 100)
            })

    # 비율이 높은 카테고리부터 정렬하기
    categories.sort(
        key=lambda category: category["percentage"],
        reverse=True,
    )

    return {
        "categories": categories
    }

# 닉네임 수정하기
@router.patch("/me")
def update_my_profile(
    request: NicknameUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    # 변경하려는 닉네임이 이미 사용 중인지 확인하기
    nickname_check = (
        supabase
        .table("profiles")
        .select("id")
        .eq("profile_nickname", request.nickname)
        .execute()
    )

    # 다른 사용자가 같은 닉네임을 사용하고 있으면 수정하지 않기
    if nickname_check.data:
        existing_user_id = str(nickname_check.data[0]["id"])

        if existing_user_id != current_user.id:
            raise create_error_response(
                409,
                "NICKNAME_CONFLICT",
                "이미 사용 중인 닉네임입니다.",
            )

    # 현재 사용자의 닉네임 수정하기
    profile_result = (
        supabase
        .table("profiles")
        .update({
            "profile_nickname": request.nickname,
            "profile_updated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", current_user.id)
        .execute()
    )

    # 사용자 프로필을 찾을 수 없는 경우
    if not profile_result.data:
        raise create_error_response(
            404,
            "PROFILE_NOT_FOUND",
            "사용자 프로필을 찾을 수 없습니다.",
        )

    # 수정된 닉네임 반환하기
    return {
        "nickname": request.nickname
    }