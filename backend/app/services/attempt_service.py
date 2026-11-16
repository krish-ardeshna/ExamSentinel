"""M3: Exam Attempt, M4: Proctoring, M5: Evaluation services.

Handles exam attempts, proctoring events, answer saving, and auto-evaluation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.attempt import ExamAttempt
from app.models.answer import Answer
from app.models.exam import Exam
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.violation import ViolationLog
from app.models.result import Result
from app.models.student import Student
from app.schemas.attempt import AttemptCreate

VALID_ATTEMPT_STATUSES = {"In Progress", "Submitted", "Auto-Locked"}


def validate_and_create_attempt(db: Session, exam_id: int, student_id: int,
                                 start_at: str, submit_at: Optional[str] = None,
                                 status: str = "In Progress",
                                 flagged: bool = False) -> ExamAttempt:
    """Validate and create an exam attempt. This is the save/validate method for UT-ATT.

    Rules:
    - exam_id must exist and be Published
    - student_id must exist; one attempt per exam per student
    - start_at must be inside the exam window, not in the future
    - submit_at must be after start_at and not after exam end_time
    - status must be one of: In Progress, Submitted, Auto-Locked
    - flagged must be boolean, default false
    """
    # Validate status and flagged
    if not status or status not in VALID_ATTEMPT_STATUSES:
        raise ValueError("status: One of: In Progress, Submitted, Auto-Locked")

    if flagged is None or not isinstance(flagged, bool):
        raise ValueError("flagged: Boolean, default false")

    # Validate exam_id
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam or exam.status != "Published":
        raise ValueError("exam_id: Must exist in Exam and be Published")

    # Validate student_id
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise ValueError("student_id: Must exist in Student; one attempt per exam per student")

    # Check one attempt per exam per student
    existing = (
        db.query(ExamAttempt)
        .filter(ExamAttempt.exam_id == exam_id, ExamAttempt.student_id == student_id)
        .first()
    )
    if existing:
        raise ValueError("student_id: Must exist in Student; one attempt per exam per student")

    # Validate start_at
    try:
        start_dt = datetime.strptime(start_at, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        raise ValueError("start_at: Valid datetime (YYYY-MM-DD HH:MM:SS), inside the exam window, not in the future")

    # Check start_at is inside exam window and not in the future
    exam_start = exam.start_time.replace(tzinfo=None) if exam.start_time.tzinfo else exam.start_time
    exam_end = exam.end_time.replace(tzinfo=None) if exam.end_time.tzinfo else exam.end_time

    if start_dt < exam_start or start_dt > exam_end:
        raise ValueError("start_at: Valid datetime (YYYY-MM-DD HH:MM:SS), inside the exam window, not in the future")

    if start_dt > datetime.now():
        raise ValueError("start_at: Valid datetime (YYYY-MM-DD HH:MM:SS), inside the exam window, not in the future")

    # Validate submit_at if provided
    submit_dt = None
    if submit_at:
        try:
            submit_dt = datetime.strptime(submit_at, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            raise ValueError("submit_at: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_at, not after exam end_time")

        if submit_dt <= start_dt:
            raise ValueError("submit_at: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_at, not after exam end_time")

        if submit_dt > exam_end:
            raise ValueError("submit_at: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_at, not after exam end_time")

    attempt = ExamAttempt(
        exam_id=exam_id,
        student_id=student_id,
        start_at=start_dt,
        submit_at=submit_dt,
        status=status,
        flagged=flagged,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def save_attempt(db: Session, **kwargs) -> ExamAttempt:
    """Save/validate method for Exam Attempt module per UT-ATT requirements.

    Validates inputs and saves record. If invalid, raises ValueError("<field>: <rule>")
    and ensures nothing is saved.
    """
    try:
        data = AttemptCreate(**kwargs)
    except Exception as e:
        msg = str(e)
        if hasattr(e, "errors"):
            msg = e.errors()[0]["msg"]
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
        raise ValueError(msg)

    return validate_and_create_attempt(
        db=db,
        exam_id=data.exam_id,
        student_id=data.student_id,
        start_at=data.start_at,
        submit_at=data.submit_at,
        status=data.status,
        flagged=data.flagged,
    )



def save_answers(db: Session, attempt_id: int, answers: Dict[int, str]) -> List[Answer]:
    """Autosave answers for an attempt. Only if attempt is In Progress."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not attempt:
        raise ValueError("Attempt not found")
    if attempt.status != "In Progress":
        raise ValueError("Cannot modify answers for this attempt")

    saved = []
    for q_id, selected in answers.items():
        existing = (
            db.query(Answer)
            .filter(Answer.attempt_id == attempt_id, Answer.question_id == q_id)
            .first()
        )
        if existing:
            existing.selected_option = selected
            saved.append(existing)
        else:
            ans = Answer(attempt_id=attempt_id, question_id=q_id, selected_option=selected)
            db.add(ans)
            saved.append(ans)

    db.commit()
    return saved


def submit_attempt(db: Session, attempt_id: int) -> ExamAttempt:
    """Submit an attempt and trigger evaluation."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not attempt:
        raise ValueError("Attempt not found")
    if attempt.status != "In Progress":
        raise ValueError("Attempt cannot be submitted")

    attempt.status = "Submitted"
    attempt.submit_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger evaluation
    evaluate(db, attempt_id)

    db.refresh(attempt)
    return attempt


# ── M4: Proctoring ──────────────────────────────────────────────────────────

def on_event(db: Session, attempt_id: int, event_type: str, timestamp: str) -> Optional[ViolationLog]:
    """Handle a proctoring event (tab switch or fullscreen exit).

    Rules:
    - Attempt must be In Progress; events for other statuses are ignored
    - Duplicate events within 1 second are merged
    - Writes VIOLATION_LOG, sets flagged=true, status=Auto-Locked
    - Saves partial answers and triggers evaluation
    """
    attempt = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not attempt:
        return None

    # Ignore events for non-In-Progress attempts
    if attempt.status != "In Progress":
        return None

    try:
        ts = datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        ts = datetime.now(timezone.utc)

    # Check for duplicate within 1 second
    recent = (
        db.query(ViolationLog)
        .filter(
            ViolationLog.attempt_id == attempt_id,
            ViolationLog.type == event_type,
        )
        .order_by(ViolationLog.occurred_at.desc())
        .first()
    )
    if recent:
        recent_ts = recent.occurred_at
        if recent_ts.tzinfo is None:
            recent_ts = recent_ts.replace(tzinfo=timezone.utc)
        ts_aware = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        if abs((ts_aware - recent_ts).total_seconds()) < 1:
            return None  # Duplicate, ignore

    # Log the violation
    violation = ViolationLog(
        attempt_id=attempt_id,
        type=event_type,
        occurred_at=ts,
    )
    db.add(violation)

    # Flag and lock the attempt
    attempt.flagged = True
    attempt.status = "Auto-Locked"
    attempt.submit_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger evaluation on the saved partial answers
    evaluate(db, attempt_id)

    db.refresh(violation)
    return violation


# ── M5: Evaluation & Results ────────────────────────────────────────────────

def evaluate(db: Session, attempt_id: int) -> Optional[Result]:
    """Auto-evaluate an attempt against the answer key.

    Rules:
    - Correct answer gets full question marks, wrong/blank gets 0
    - Computes score and percentage
    - Creates exactly one RESULT per attempt (idempotent)
    - Locked attempts are evaluated on saved answers
    """
    attempt = db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()
    if not attempt:
        return None

    # Check if result already exists (idempotent)
    existing_result = db.query(Result).filter(Result.attempt_id == attempt_id).first()
    if existing_result:
        return existing_result

    exam = db.query(Exam).filter(Exam.exam_id == attempt.exam_id).first()
    if not exam:
        return None

    # Get all questions and answer keys
    questions = db.query(Question).filter(Question.exam_id == exam.exam_id).all()
    if not questions:
        return None

    # Build answer key map
    answer_key_map = {}
    for q in questions:
        ak = db.query(AnswerKey).filter(AnswerKey.question_id == q.question_id).first()
        if ak:
            answer_key_map[q.question_id] = ak.correct_option

    if not answer_key_map:
        return None  # No answer key, can't evaluate

    # Get student answers
    student_answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    answer_map = {a.question_id: a for a in student_answers}

    score = Decimal("0")
    for q in questions:
        correct = answer_key_map.get(q.question_id)
        student_ans = answer_map.get(q.question_id)
        if student_ans and student_ans.selected_option == correct:
            student_ans.is_correct = True
            score += Decimal(str(q.marks))
        elif student_ans:
            student_ans.is_correct = False

    # Calculate percentage
    total = Decimal(str(exam.total_marks)) if exam.total_marks > 0 else Decimal("1")
    percentage = (score * Decimal("100")) / total

    result = Result(
        attempt_id=attempt_id,
        score=score,
        percentage=percentage,
        published_at=datetime.now(timezone.utc),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def get_attempt(db: Session, attempt_id: int) -> Optional[ExamAttempt]:
    """Get an attempt by ID."""
    return db.query(ExamAttempt).filter(ExamAttempt.attempt_id == attempt_id).first()


def get_student_attempts(db: Session, student_id: int) -> List[ExamAttempt]:
    """Get all attempts for a student."""
    return db.query(ExamAttempt).filter(ExamAttempt.student_id == student_id).all()
