# PlayEAT

신대방 점심 맛집 추천 및 AI 서비스 로그 분석 대시보드

> 사용자에게는 조건 기반 맛집 추천을, 운영자에게는 API 로그와 추천 품질을 분석하는 대시보드를 제공하는 통합 서비스입니다.

---

## 목차

- [프로젝트 배경 및 목표](#프로젝트-배경-및-목표)
- [핵심 기능](#핵심-기능)
- [대시보드 기능](#대시보드-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시스템 아키텍처](#시스템-아키텍처)
- [데이터베이스 설계](#데이터베이스-설계)
- [설치 및 실행 방법](#설치-및-실행-방법)
- [팀 구성](#팀-구성)
- [문서](#문서)

---

## 프로젝트 배경 및 목표

점심시간마다 가격대·메뉴·상황(혼밥/회식 등)을 고려해 여러 식당을 일일이 비교하는 데 많은 시간이 드는 문제에서 출발했습니다. 동시에, 서비스를 운영하는 입장에서는 실제 API가 어떻게 쓰이고 있는지, 추천 품질이 실제로 괜찮은지를 정량적으로 확인할 방법이 마땅치 않다는 문제도 있습니다.

PlayEAT은 이 두 문제를 하나의 프로젝트에서 함께 다룹니다.

1. 사용자에게는 자연어 + 조건 선택을 결합한 맛집 추천을 제공한다.
2. 모든 API 요청/응답을 로그로 남기고, 이를 정제·집계해 운영 대시보드로 시각화한다.
3. LLM 기반 로그 요약과 정량 품질 평가를 통해 추천 개선 사이클을 실제로 한 번 돌려본다.

추천 근거는 DB에 실제로 존재하는 식당·메뉴 정보만 사용하며, 존재하지 않는 메뉴나 가격을 생성하지 않는 것을 핵심 원칙으로 합니다.

## 핵심 기능

### 사용자 기능

- 이메일 / 카카오 로그인, 역할 기반 접근 제어
- 조건 선택(카테고리·가격대·상황 태그) + 자연어 입력을 결합한 맛집 추천 (Gemini 기반)
- 52개 검증된 신대방 지역 식당 데이터 기반 추천
- 추천 결과에 대한 3단계 피드백(불만족/보통/만족)
- 대화(추천 세션) 이력 관리, 마이페이지·프로필 수정

### 관리자 기능

- 모든 API 요청/응답 로그를 PostgreSQL에 순차 적재
- 로그 정제 및 기본 통계(요청량, 응답 시간, 에러율) 산출
- 근거 로그를 함께 제시하는 LLM 기반 로그 요약
- 사전 정의된 테스트 케이스 대비 요약 품질 정량 평가
- 개선 전/후 비교 실험
- 식당 데이터 조회·관리

## 대시보드 기능

Streamlit 관리자 화면(`frontend/src/views/admin_*.py`)은 다음 영역으로 구성됩니다.

| 화면 | 내용 |
|---|---|
| 검색·이용 분석 (`admin_analytics`) | 카테고리별 검색 분석, 상황 태그 분석 |
| 로그 분석 (`admin_logs`) | API 요청량·응답시간·에러율 통계, LLM 로그 요약 및 품질 평가 결과 |
| 사용자 피드백 (`admin_feedback`) | 추천 결과에 대한 사용자 반응 및 코멘트 |
| 식당 관리 (`admin_restaurants`) | 식당·메뉴 데이터 조회 |

## 기술 스택

| 구분 | 내용 |
|---|---|
| 백엔드 | FastAPI — 요청 로깅 미들웨어(`app/middleware/request_log.py`)로 모든 API 호출 기록 |
| 프론트엔드 | Streamlit |
| 데이터베이스 | PostgreSQL (Supabase) |
| 캐시 | Redis |
| 외부 API | Google Gemini API (추천·요약), 카카오 로그인 |
| 패키지 관리 | uv |

## 프로젝트 구조

```
.
├── backend/
│   └── app/
│       ├── main.py                # FastAPI 엔트리포인트
│       ├── db.py, cache.py        # Supabase / Redis 클라이언트
│       ├── middleware/
│       │   └── request_log.py     # 전체 API 요청 로깅
│       ├── routers/
│       │   ├── auth.py            # 회원가입/로그인
│       │   ├── users.py           # 사용자 프로필
│       │   ├── chat.py            # 자연어 대화
│       │   ├── conversations.py   # 추천 세션 관리
│       │   ├── recommendations.py # 추천 로직
│       │   ├── feedback.py        # 추천 피드백
│       │   ├── restaurants.py     # 식당/메뉴 데이터
│       │   ├── search_stats.py    # 검색 통계
│       │   └── admin_logs.py      # 관리자 로그·통계
│       ├── schemas/               # Pydantic 모델
│       └── services/
│           ├── api_statistics.py
│           ├── log_cleaning.py
│           ├── log_summary.py
│           ├── summary_evaluation.py
│           └── improvement_experiments.py
├── frontend/
│   ├── streamlit_app.py           # Streamlit 엔트리포인트
│   └── src/
│       ├── views/                 # 화면별 페이지 (로그인/회원가입/홈/마이페이지/관리자)
│       ├── components/, common/   # 공통 UI, API 클라이언트
│       └── styles/                # 화면별 CSS
└── docs/
    ├── PRD_개정본.md
    ├── API명세서.md
    ├── design.md
    └── 신대방챗봇_DB정의서.html
```

## 시스템 아키텍처

```
[사용자] → Streamlit 프론트엔드 → FastAPI 백엔드 → Supabase(PostgreSQL) / Redis
                                          ↓
                                   Gemini API (추천/요약)
                                          ↓
                         요청 로깅 미들웨어 → 로그 정제·통계 → 관리자 대시보드
```

모든 API 요청/응답은 `request_log` 미들웨어에서 기록되어 Supabase에 적재됩니다. 이 로그는 `log_cleaning`으로 정제되고, `api_statistics`·`log_summary`·`summary_evaluation` 서비스를 거쳐 관리자 대시보드와 LLM 요약의 입력으로 쓰입니다. 비밀번호·토큰·API 키 등 민감 정보는 로그에 남기지 않습니다.

## 데이터베이스 설계

핵심 테이블은 다음과 같이 구성됩니다.

- `restaurant_categories` — 음식 카테고리 (한식/중식/일식/양식/기타)
- `restaurants` — 식당 기본 정보 (52개)
- `menus` — 식당별 대표 메뉴 (식당당 3개 기준)
- `tag_categories` / `restaurant_tags` / `restaurant_tag_map` — 상황 태그 및 매핑

가격대는 식당별 1인당 평균 가격 기준 상(2만원 이상)/중(1만원 초과~2만원 이하)/하(1만원 이하) 3단계로 분류합니다. 상세 ERD와 테이블 정의는 [`docs/신대방챗봇_DB정의서.html`](./docs/신대방챗봇_DB정의서.html)를 참고하세요.

## 설치 및 실행 방법

### 사전 요구사항

- Python (버전은 `backend/.python-version`, `frontend/.python-version` 참고)
- [uv](https://docs.astral.sh/uv/) 패키지 매니저
- Supabase 프로젝트 (PostgreSQL) 및 Redis 인스턴스
- Google Gemini API 키

### 1. 저장소 클론

```bash
git clone https://github.com/encore-ai-campus/aio-02-p1-team1.git
cd aio-02-p1-team1
```

### 2. 환경 변수 설정

`backend/.env.example`을 복사해 `backend/.env`를 만들고 값을 채웁니다. (`.env`는 커밋하지 않습니다.)

```bash
cp backend/.env.example backend/.env
```

```
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SERVICE_ROLE_KEY=
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
GEMINI_API_KEY=
```

### 3. 백엔드 실행

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

### 4. 프론트엔드 실행

```bash
cd frontend
uv sync
uv run streamlit run streamlit_app.py
```

백엔드는 기본적으로 `http://localhost:8000`, 프론트엔드는 `http://localhost:8501`에서 확인할 수 있습니다.

## 팀 구성

| 역할 | 담당 영역 |
|---|---|
| 개발 리더 | 초기 세팅(브랜치 전략, 컨벤션, DB 설계 총괄), 메인 화면·챗봇, 백엔드 총괄 |
| 프론트엔드 | 로그인 화면 |
| 프론트엔드 | 회원가입 화면 |
| 프론트엔드 | 마이페이지 화면 |
| 대시보드 · DB · 일정관리 | 관리자 대시보드, DB 정의서, 식당 자료조사, 일정·산출물 관리, 팀 발표 |
| 디자인 | 전체 화면 디자인 |

> 실명 대신 역할 기준으로 표기했습니다. 팀원별 상세 담당은 커밋/PR 이력에서 확인할 수 있습니다.

## 문서

- [PRD](./docs/PRD_개정본.md)
- [API 명세서](./docs/API명세서.md)
- [화면 설계서](./docs/design.md)
- [DB 정의서](./docs/신대방챗봇_DB정의서.html)

---

Encore AI 캠퍼스 단위 프로젝트 (AIO-02 Project 1, Team 1)
