"""Platform settings endpoints for Admin (UC-A2)."""

from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.models.settings import PlatformSetting

router = APIRouter(prefix="/settings", tags=["Platform Settings"])


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.get("")
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"])),
):
    """Admin reads all platform settings."""
    settings = db.query(PlatformSetting).all()
    return [{"key": s.key, "value": s.value, "updated_at": s.updated_at} for s in settings]


@router.put("")
def update_platform_setting(
    payload: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Admin"])),
):
    """Admin updates a platform setting (e.g. AI_HELP_DAILY_LIMIT).

    Validation:
    - Numeric settings must be integers > 0.
    """
    # If setting is integer parameter
    if payload.key in ["AI_HELP_DAILY_LIMIT", "MAX_EXAM_DURATION_MIN", "SESSION_TIMEOUT_MIN"]:
        try:
            val = int(payload.value)
            if val <= 0:
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Numeric values must be integers greater than 0",
            )

    setting = db.query(PlatformSetting).filter(PlatformSetting.key == payload.key).first()
    if setting:
        setting.value = payload.value
        setting.updated_at = datetime.now(timezone.utc)
        setting.updated_by = current_user.user_id
    else:
        setting = PlatformSetting(
            key=payload.key,
            value=payload.value,
            updated_at=datetime.now(timezone.utc),
            updated_by=current_user.user_id,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return {"key": setting.key, "value": setting.value, "message": "Setting updated successfully"}
