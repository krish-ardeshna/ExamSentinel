"""Result & Grading endpoints (M5)."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.result import Result
from app.models.attempt import ExamAttempt
from app.models.exam import Exam
from app.models.question import Question
from app.models.answer import Answer
from app.models.answer_key import AnswerKey

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("")
def list_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List results accessible to the current user."""
    query = (
        db.query(Result, ExamAttempt, Exam)
        .join(ExamAttempt, Result.attempt_id == ExamAttempt.attempt_id)
        .join(Exam, ExamAttempt.exam_id == Exam.exam_id)
        .filter(Result.published_at.isnot(None))
    )

    if current_user.role == "Student":
        if not current_user.student:
            return []
        query = query.filter(ExamAttempt.student_id == current_user.student.student_id)
    elif current_user.role == "Parent":
        if not current_user.parent:
            return []
        child_ids = [c.student_id for c in current_user.parent.children]
        query = query.filter(ExamAttempt.student_id.in_(child_ids))
    elif current_user.role == "Teacher":
        if not current_user.teacher:
            return []
        subject_ids = [s.subject_id for s in current_user.teacher.subjects]
        query = query.filter(Exam.subject_id.in_(subject_ids))

    results = query.all()
    out = []
    for res, att, ex in results:
        status_label = "Terminated (violation)" if att.status == "Auto-Locked" else att.status
        out.append({
            "result_id": res.result_id,
            "attempt_id": att.attempt_id,
            "exam_id": ex.exam_id,
            "exam_title": ex.title,
            "score": float(res.score),
            "total_marks": ex.total_marks,
            "percentage": float(res.percentage),
            "status": status_label,
            "flagged": att.flagged,
            "published_at": res.published_at.isoformat() if res.published_at else None,
        })
    return out


@router.get("/attempt/{attempt_id}")
def get_attempt_result(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed result for a single attempt, including question review."""
    att = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

    # Access check
    if current_user.role == "Student":
        if not current_user.student or current_user.student.student_id != att.student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    res = db.query(Result).filter(Result.attempt_id == attempt_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not ready or not published")

    exam = att.exam
    questions = db.query(Question).filter(Question.exam_id == exam.exam_id).all()
    answers = {
        a.question_id: a
        for a in db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    }
    answer_keys = {
        ak.question_id: ak.correct_option
        for ak in db.query(AnswerKey).filter(AnswerKey.question_id.in_([q.question_id for q in questions])).all()
    }

    breakdown = []
    for q in questions:
        ans = answers.get(q.question_id)
        selected = ans.selected_option if ans else None
        is_correct = ans.is_correct if ans else False
        breakdown.append({
            "question_id": q.question_id,
            "text": q.text,
            "options": q.options,
            "marks": q.marks,
            "selected_option": selected,
            "correct_option": answer_keys.get(q.question_id),
            "is_correct": is_correct,
        })

    status_label = "Terminated (violation)" if att.status == "Auto-Locked" else att.status
    return {
        "result_id": res.result_id,
        "attempt_id": att.attempt_id,
        "exam_title": exam.title,
        "score": float(res.score),
        "total_marks": exam.total_marks,
        "percentage": float(res.percentage),
        "status": status_label,
        "flagged": att.flagged,
        "published_at": res.published_at.isoformat() if res.published_at else None,
        "questions": breakdown,
    }
