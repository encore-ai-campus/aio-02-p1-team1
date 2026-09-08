from pydantic import BaseModel

# ── 채팅용 클래스 ────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    content: str ##타이틀
    # 화면에서 고른 값. 안 보내면 None 이고, gemini_client 가 기본값으로 바꾼다.
    # 주의: 여기에 기본 문자열을 적지 않는다. 적으면 선택지 목록이 두 파일에 나뉘어
    #      한쪽만 고쳤을 때 어긋난다. 선택지는 gemini_client.py 한 곳에만 둔다.
    tone: str | None = None
    length: str | None = None   


# ── 다시 생성 만들기 ────────────────────────────────────────────────────────
class RegenerateRequest(BaseModel):
    # 주의: ChatRequest 를 재사용하면 안 된다. 거기에는 content 가 필수라서,
    #      질문을 다시 보내지 않는 이 요청은 422 로 거부당한다.
    tone: str | None = None
    length: str | None = None