"""Exam management endpoints (M2)."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles, get_current_user
from app.models.user import User
from app.models.exam import Exam
from app.models.subject import Subject
from app.schemas.exam import (
    ExamCreate,
    ExamResponse,
    QuestionCreate,
    QuestionResponse,
    AnswerKeyCreate,
)
from app.services.exam_service import (
    validate_and_create_exam,
    get_exam,
    get_exams,
    get_teacher_exams,
    add_question,
    edit_question,
    submit_answer_key,
    publish_exam,
    get_exam_paper,
)

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam_endpoint(
    exam_in: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Teacher schedules a new exam for their own subject."""
    try:
        return validate_and_create_exam(db, exam_in, current_user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[ExamResponse])
def list_exams_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List exams depending on user role."""
    if current_user.role == "Teacher":
        exams = get_teacher_exams(db, current_user.user_id)
    elif current_user.role in ["Student", "Parent"]:
        exams = db.query(Exam).filter(Exam.status == "Published").all()
    else:  # Admin, HOD
        exams = get_exams(db)

    results = []
    for ex in exams:
        results.append(
            ExamResponse(
                exam_id=ex.exam_id,
                subject_id=ex.subject_id,
                title=ex.title,
                start_time=ex.start_time,
                end_time=ex.end_time,
                duration_min=ex.duration_min,
                total_marks=ex.total_marks,
                status=ex.status,
                question_count=len(ex.questions) if ex.questions else 0,
            )
        )
    return results


@router.get("/subjects/list")
def list_subjects_for_teacher(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List subjects assigned to current teacher (or all subjects for admin/hod)."""
    if current_user.role == "Teacher":
        if not current_user.teacher:
            return []
        subjects = db.query(Subject).filter(Subject.teacher_id == current_user.teacher.teacher_id).all()
    else:
        subjects = db.query(Subject).all()

    return [
        {
            "subject_id": s.subject_id,
            "code": s.code,
            "name": s.name,
            "semester": s.semester,
        }
        for s in subjects
    ]


@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam_details(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get exam details."""
    ex = get_exam(db, exam_id)
    if not ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found")
    return ExamResponse(
        exam_id=ex.exam_id,
        subject_id=ex.subject_id,
        title=ex.title,
        start_time=ex.start_time,
        end_time=ex.end_time,
        duration_min=ex.duration_min,
        total_marks=ex.total_marks,
        status=ex.status,
        question_count=len(ex.questions) if ex.questions else 0,
    )


@router.post("/{exam_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question_endpoint(
    exam_id: int,
    q_in: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Add a question to an exam."""
    try:
        return add_question(
            db,
            exam_id=exam_id,
            text=q_in.text,
            options=q_in.options,
            marks=q_in.marks,
            teacher_user_id=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/questions/{question_id}", response_model=QuestionResponse)
def edit_question_endpoint(
    question_id: int,
    q_in: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Edit question before start time."""
    try:
        return edit_question(
            db,
            question_id=question_id,
            teacher_user_id=current_user.user_id,
            text=q_in.text,
            options=q_in.options,
            marks=q_in.marks,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{exam_id}/answer-key")
def submit_answer_key_endpoint(
    exam_id: int,
    key_in: AnswerKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Submit or update official answer key for exam."""
    try:
        keys = submit_answer_key(db, exam_id, key_in.answers, current_user.user_id)
        return {"message": f"Answer key saved successfully for {len(keys)} questions"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{exam_id}/publish", response_model=ExamResponse)
def publish_exam_endpoint(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["Teacher"])),
):
    """Publish exam to students/parents. Checks question count and total marks sum."""
    try:
        ex = publish_exam(db, exam_id, current_user.user_id)
        return ExamResponse(
            exam_id=ex.exam_id,
            subject_id=ex.subject_id,
            title=ex.title,
            start_time=ex.start_time,
            end_time=ex.end_time,
            duration_min=ex.duration_min,
            total_marks=ex.total_marks,
            status=ex.status,
            question_count=len(ex.questions),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{exam_id}/paper", response_model=List[QuestionResponse])
def get_exam_paper_endpoint(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get exam questions without answer keys."""
    questions = get_exam_paper(db, exam_id)
    return questions
