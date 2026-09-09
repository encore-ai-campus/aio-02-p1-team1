from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, users


from app.middleware.request_log import ApiRequestLogMiddleware
from app.routers.admin_logs import router as admin_logs_router
from app.routers.feedback import router as feedback_router
from app.routers.restaurants import router as restaurants_router
from app.routers.search_stats import router as search_stats_router
from app.routers.conversations import conversation_router

app = FastAPI(title="PlayEAT", version="0.2.0")

app.add_middleware(ApiRequestLogMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(restaurants_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(search_stats_router, prefix="/api/v1")
app.include_router(admin_logs_router, prefix="/api/v1")

app.include_router(users.auth_router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(conversation_router,prefix="/api/v1",)


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router,prefix="/api/v1")
# app.include_router(users.router,prefix="/api/v1")