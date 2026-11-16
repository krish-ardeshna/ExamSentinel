"""M2: Exam Management service.

Handles exam scheduling, question management, answer key submission,
and publishing. Teacher can only manage exams for their own subjects.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from app.models.exam import Exam
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.exam import ExamCreate


def validate_and_create_exam(db: Session, data: ExamCreate, teacher_user_id: int) -> Exam:
    """Validate input and create an exam. This is the save/validate method for UT-EXM.

    - subject_id must exist and belong to the logged-in Teacher
    - All field validations are done by the Pydantic schema
    """
    # Verify teacher
    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    if not teacher:
        raise ValueError("subject_id: Must exist in Subject and belong to the logged-in Teacher")

    # Verify subject ownership
    subject = (
        db.query(Subject)
        .filter(Subject.subject_id == data.subject_id, Subject.teacher_id == teacher.teacher_id)
        .first()
    )
    if not subject:
        raise ValueError("subject_id: Must exist in Subject and belong to the logged-in Teacher")

    start_dt = datetime.strptime(data.start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(data.end_time, "%Y-%m-%d %H:%M:%S")

    exam = Exam(
        subject_id=data.subject_id,
        title=data.title,
        start_time=start_dt,
        end_time=end_dt,
        duration_min=data.duration_min,
        total_marks=data.total_marks,
        status=data.status,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def save_exam(db: Session, teacher_user_id: int, **kwargs) -> Exam:
    """Save/validate method for Exam module per UT-EXM requirements.

    Validates inputs and saves record. If invalid, raises ValueError("<field>: <rule>")
    and ensures nothing is saved.
    """
    try:
        data = ExamCreate(**kwargs)
    except Exception as e:
        msg = str(e)
        if hasattr(e, "errors"):
            msg = e.errors()[0]["msg"]
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
        raise ValueError(msg)
    return validate_and_create_exam(db, data, teacher_user_id)



def get_exam(db: Session, exam_id: int) -> Optional[Exam]:
    """Get an exam by ID."""
    return db.query(Exam).filter(Exam.exam_id == exam_id).first()


def get_exams(db: Session, skip: int = 0, limit: int = 100) -> List[Exam]:
    """Get all exams with pagination."""
    return db.query(Exam).offset(skip).limit(limit).all()


def get_teacher_exams(db: Session, teacher_user_id: int) -> List[Exam]:
    """Get all exams for a teacher's subjects."""
    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    if not teacher:
        return []
    subject_ids = [s.subject_id for s in teacher.subjects]
    return db.query(Exam).filter(Exam.subject_id.in_(subject_ids)).all()


def add_question(db: Session, exam_id: int, text: str, options: dict, marks: int, teacher_user_id: int) -> Question:
    """Add a question to an exam. Paper cannot be edited after start_time."""
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise ValueError("Exam not found")

    # Check ownership
    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    subject = db.query(Subject).filter(Subject.subject_id == exam.subject_id).first()
    if not teacher or not subject or subject.teacher_id != teacher.teacher_id:
        raise ValueError("Not authorized to edit this exam")

    # Check if exam has started
    st = exam.start_time
    if st.tzinfo is None:
        st = st.replace(tzinfo=timezone.utc)
    if st <= datetime.now(timezone.utc):
        raise ValueError("Edit rejected; the paper is locked after start_time")


    question = Question(exam_id=exam_id, text=text, options=options, marks=marks)
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def edit_question(db: Session, question_id: int, teacher_user_id: int, **kwargs) -> Question:
    """Edit a question. Paper cannot be edited after start_time."""
    question = db.query(Question).filter(Question.question_id == question_id).first()
    if not question:
        raise ValueError("Question not found")

    exam = question.exam
    st = exam.start_time
    if st.tzinfo is None:
        st = st.replace(tzinfo=timezone.utc)
    if st <= datetime.now(timezone.utc):
        raise ValueError("Edit rejected; the paper is locked after start_time")


    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    subject = db.query(Subject).filter(Subject.subject_id == exam.subject_id).first()
    if not teacher or not subject or subject.teacher_id != teacher.teacher_id:
        raise ValueError("Not authorized to edit this exam")

    for key, value in kwargs.items():
        if hasattr(question, key):
            setattr(question, key, value)

    db.commit()
    db.refresh(question)
    return question


def submit_answer_key(db: Session, exam_id: int, answers: Dict[int, str], teacher_user_id: int) -> List[AnswerKey]:
    """Submit answer key for an exam. Only the exam owner can submit."""
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise ValueError("Exam not found")

    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    subject = db.query(Subject).filter(Subject.subject_id == exam.subject_id).first()
    if not teacher or not subject or subject.teacher_id != teacher.teacher_id:
        raise ValueError("Not authorized")

    # Check all questions are covered
    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    question_ids = {q.question_id for q in questions}
    if set(answers.keys()) != question_ids:
        raise ValueError("Key must cover all questions of the exam")

    result_keys = []
    for q_id, correct_option in answers.items():
        existing = db.query(AnswerKey).filter(AnswerKey.question_id == q_id).first()
        if existing:
            existing.correct_option = correct_option
            result_keys.append(existing)
        else:
            ak = AnswerKey(question_id=q_id, correct_option=correct_option)
            db.add(ak)
            result_keys.append(ak)

    db.commit()
    return result_keys


def publish_exam(db: Session, exam_id: int, teacher_user_id: int) -> Exam:
    """Publish an exam. Rules:
    - Must have at least one question
    - total_marks must equal sum of question marks
    """
    exam = db.query(Exam).filter(Exam.exam_id == exam_id).first()
    if not exam:
        raise ValueError("Exam not found")

    teacher = db.query(Teacher).filter(Teacher.user_id == teacher_user_id).first()
    subject = db.query(Subject).filter(Subject.subject_id == exam.subject_id).first()
    if not teacher or not subject or subject.teacher_id != teacher.teacher_id:
        raise ValueError("Not authorized")

    questions = db.query(Question).filter(Question.exam_id == exam_id).all()
    if not questions:
        raise ValueError("Add at least one question")

    total_question_marks = sum(q.marks for q in questions)
    if exam.total_marks != total_question_marks:
        raise ValueError("total_marks must equal the sum of question marks")

    exam.status = "Published"
    db.commit()
    db.refresh(exam)
    return exam


def get_exam_paper(db: Session, exam_id: int) -> List[Question]:
    """Get the question paper for an exam (no answer keys)."""
    return db.query(Question).filter(Question.exam_id == exam_id).all()
