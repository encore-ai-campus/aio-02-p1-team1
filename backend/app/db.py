import os

from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.client import ClientOptions

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# 회원가입·로그인 요청에 사용할 새 연결 객체 만들기
def create_auth_client() -> Client:
    return create_client(
        SUPABASE_URL,
        os.environ["SUPABASE_PUBLISHABLE_KEY"],
        options=ClientOptions(
            persist_session=False,
            auto_refresh_token=False,
        ),
    )