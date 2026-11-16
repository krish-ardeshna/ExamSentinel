"""Exam Attempt & Proctoring endpoints (M3, M4, M5)."""

from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles, get_current_user
from app.models.user import User
from app.models.attempt import ExamAttempt
from app.models.answer import Answer
from app.schemas.attempt import (
    AttemptResponse,
    AnswerSave,
    EventCreate,
    SubmitResponse,
)
from app.services.attempt_service import (
    validate_and_create_attempt,
    save_answers,
    submit_attempt,
    on_event,
    get_attempt,
)

router = APIRouter(prefix="/attempts", tags=["Exam Attempts"])


@router.post("", response_model=AttemptResponse, status_code=status.HTTP_201_CREATED)
def start_attempt_endpoint(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """Student starts a new attempt for a published exam inside its window."""
    if not current_user.student:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student profile not found")

    student_id = current_user.student.student_id
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        att = validate_and_create_attempt(
            db=db,
            exam_id=exam_id,
            student_id=student_id,
            start_at=now_str,
            status="In Progress",
            flagged=False,
        )
        return AttemptResponse(
            attempt_id=att.attempt_id,
            exam_id=att.exam_id,
            student_id=att.student_id,
            start_at=att.start_at.isoformat() if att.start_at else None,
            submit_at=att.submit_at.isoformat() if att.submit_at else None,
            status=att.status,
            flagged=att.flagged,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{attempt_id}")
def get_attempt_endpoint(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get attempt details and saved answers."""
    att = get_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    # Security check: Student can only view own attempt
    if current_user.role == "Student":
        if not current_user.student or current_user.student.student_id != att.student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    saved_answers = {
        a.question_id: a.selected_option
        for a in db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    }

    return {
        "attempt_id": att.attempt_id,
        "exam_id": att.exam_id,
        "student_id": att.student_id,
        "start_at": att.start_at.isoformat() if att.start_at else None,
        "submit_at": att.submit_at.isoformat() if att.submit_at else None,
        "status": att.status,
        "flagged": att.flagged,
        "answers": saved_answers,
        "exam_title": att.exam.title if att.exam else "",
        "duration_min": att.exam.duration_min if att.exam else 0,
        "total_marks": att.exam.total_marks if att.exam else 0,
    }


@router.put("/{attempt_id}/answers")
def autosave_answers_endpoint(
    attempt_id: int,
    payload: AnswerSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """Autosave student answers. Fails if attempt is locked or submitted."""
    att = get_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if not current_user.student or current_user.student.student_id != att.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        saved = save_answers(db, attempt_id, payload.answers)
        return {"message": f"Successfully autosaved {len(saved)} answers", "saved_count": len(saved)}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{attempt_id}/events")
def proctoring_event_endpoint(
    attempt_id: int,
    event: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Receive proctoring violation event (TAB_SWITCH, FULLSCREEN_EXIT).

    If attempt is In Progress, logs violation, sets flagged=true, status=Auto-Locked,
    and automatically evaluates saved partial answers.
    """
    violation = on_event(db, attempt_id, event.event_type, event.timestamp)
    att = get_attempt(db, attempt_id)
    status_str = att.status if att else "Unknown"
    is_locked = att.status == "Auto-Locked" if att else False

    return {
        "logged": violation is not None,
        "status": status_str,
        "locked": is_locked,
        "message": "Attempt auto-locked due to proctoring violation" if is_locked else "Event received",
    }


@router.post("/{attempt_id}/submit", response_model=SubmitResponse)
def submit_attempt_endpoint(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Student"])),
):
    """Submit attempt and calculate evaluation results."""
    att = get_attempt(db, attempt_id)
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")
    if not current_user.student or current_user.student.student_id != att.student_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        updated = submit_attempt(db, attempt_id)
        return SubmitResponse(
            attempt_id=updated.attempt_id,
            status=updated.status,
            message="Exam submitted and evaluated successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
