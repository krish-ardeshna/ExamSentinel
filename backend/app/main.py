"""Main FastAPI application entrypoint for OEPMS."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, engine
from app.api import api_router
from app.models import *  # ensure all models are registered

# Create database tables automatically if not already existing
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Online Exam Proctoring & Management System (OEPMS)",
    description=(
        "Full-lifecycle web exam platform featuring role-based access, automated screen proctoring, "
        "auto-evaluation, dashboards, and AI concept help via Google Gemini."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom error handler to extract exact '<field>: <rule>' error messages."""
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        msg = first_err.get("msg", "")
        # Remove pydantic's 'Value error, ' prefix if present
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": msg},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Validation error"},
    )


app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "OEPMS Backend", "version": "1.0.0"}
