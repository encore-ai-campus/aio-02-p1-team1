from pathlib import Path
import os

from dotenv import load_dotenv
from supabase import Client, create_client
from supabase.client import ClientOptions

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "backend/.env에 SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY를 넣으세요."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_key():
    return os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""


def create_auth_client() -> Client:
    anon_key = get_supabase_anon_key()
    if not anon_key:
        raise RuntimeError(
            "backend/.env에 SUPABASE_PUBLISHABLE_KEY를 넣으세요."
        )
    return create_client(
        SUPABASE_URL,
        anon_key,
        options=ClientOptions(
            persist_session=False,
            auto_refresh_token=False,
        ),
    )


def get_anon_client() -> Client:
    return create_auth_client()
