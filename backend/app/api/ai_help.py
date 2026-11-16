"""AI Concept Help endpoints (M7)."""

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.user import User
from app.models.ai_help import AIHelpRequest
from app.services.ai_service import request_ai_concept_help

router = APIRouter(prefix="/ai-help", tags=["AI Concept Help"])


class AIHelpRequestIn(BaseModel):
    attempt_id: int
    question_id: int


@router.post("")
async def ask_ai_concept_help(
    payload: AIHelpRequestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """Student requests plain-language AI explanation for a wrongly answered question."""
    try:
        return await request_ai_concept_help(
            db=db,
            student_user_id=current_user.user_id,
            attempt_id=payload.attempt_id,
            question_id=payload.question_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/history")
def get_ai_help_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """View past AI concept explanations for the logged in student."""
    if not current_user.student:
        return []
    requests = (
        db.query(AIHelpRequest)
        .filter(AIHelpRequest.student_id == current_user.student.student_id)
        .order_by(AIHelpRequest.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "help_id": r.help_id,
            "question_id": r.question_id,
            "prompt": r.prompt,
            "ai_response": r.ai_response,
            "created_at": r.created_at.isoformat(),
        }
        for r in requests
    ]
