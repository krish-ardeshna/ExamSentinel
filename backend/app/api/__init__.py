"""API package with main API router combining all endpoint modules."""

from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.exams import router as exams_router
from app.api.attempts import router as attempts_router
from app.api.results import router as results_router
from app.api.dashboard import router as dashboard_router
from app.api.ai_help import router as ai_help_router
from app.api.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(exams_router)
api_router.include_router(attempts_router)
api_router.include_router(results_router)
api_router.include_router(dashboard_router)
api_router.include_router(ai_help_router)
api_router.include_router(settings_router)
