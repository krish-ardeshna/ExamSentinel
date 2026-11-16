"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import LoginRequest, LoginResponse, UserResponse
from app.services.user_service import login

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login_endpoint(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate with email and password, return JWT token."""
    try:
        return login(db, credentials.email, credentials.password)
    except ValueError as e:
        msg = str(e)
        if "locked" in msg.lower():
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=msg)
        if "suspended" in msg.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/logout")
def logout_endpoint(current_user: User = Depends(get_current_user)):
    """Stateless JWT logout confirmation."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return the profile of the authenticated user."""
    return current_user
