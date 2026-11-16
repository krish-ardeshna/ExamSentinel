"""Unit tests for Exam Attempt module (UT-ATT 01 to 24) matching OEPMS_Unit_Testing_Experiment.docx."""

import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.exam import Exam
from app.models.question import Question
from app.models.answer_key import AnswerKey
from app.models.attempt import ExamAttempt
from app.models.answer import Answer
from app.models.violation import ViolationLog
from app.models.result import Result
from app.services.user_service import save_user
from app.services.attempt_service import (
    save_attempt,
    save_answers,
    on_event,
    evaluate,
)


def setup_exam_and_student(db, exam_status="Published", active_window=True):
    """Helper to set up a published exam and student."""
    # Teacher & Subject
    t_user = save_user(
        db,
        name="Rajesh Sharma",
        email=f"t_{datetime.now().timestamp()}@amity.edu",
        password="Teach@1234",
        role="Teacher",
        status="Active",
    )
    subject = Subject(
        teacher_id=t_user.teacher.teacher_id,
        code=f"CS_{int(datetime.now().timestamp() * 1000) % 100000}",
        name="Data Structures",
        semester=5,
    )
    db.add(subject)
    db.commit()

    # Exam
    now = datetime.now()
    if active_window:
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=2)
    else:
        start_time = now + timedelta(days=1)
        end_time = now + timedelta(days=1, hours=2)

    exam = Exam(
        subject_id=subject.subject_id,
        title="Data Structures Unit Test 1",
        start_time=start_time,
        end_time=end_time,
        duration_min=60,
        total_marks=20,
        status=exam_status,
    )
    db.add(exam)
    db.commit()

    # Student
    s_user = save_user(
        db,
        name="Riya Sharma",
        email=f"riya_{datetime.now().timestamp()}@amity.edu",
        password="Stud@1234",
        role="Student",
        status="Active",
    )
    db.commit()

    return exam, s_user.student


def get_valid_attempt_data(exam, student, overrides=None):
    """Helper returning a dict of valid ExamAttempt fields."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "exam_id": exam.exam_id,
        "student_id": student.student_id,
        "start_at": now_str,
        "submit_at": None,
        "status": "In Progress",
        "flagged": False,
    }
    if overrides:
        data.update(overrides)
    return data


# 1. Validate field: exam_id - Rule: Must exist in Exam and be Published

def test_UT_ATT_01_exam_id_accepts_published_exam(db_session):
    """Check exam_id accepts: Published exam (Data Structures Unit Test 1)"""
    exam, student = setup_exam_and_student(db_session, exam_status="Published")
    data = get_valid_attempt_data(exam, student)
    att = save_attempt(db_session, **data)
    assert att.attempt_id is not None
    assert att.exam_id == exam.exam_id


def test_UT_ATT_02_exam_id_rejects_non_existent(db_session):
    """Check exam_id rejects: exam_id 9999 (does not exist)"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"exam_id": 9999})
    with pytest.raises(ValueError, match="exam_id: Must exist in Exam and be Published"):
        save_attempt(db_session, **data)


def test_UT_ATT_03_exam_id_rejects_draft_exam(db_session):
    """Check exam_id rejects: Exam in Draft status"""
    exam, student = setup_exam_and_student(db_session, exam_status="Draft")
    data = get_valid_attempt_data(exam, student)
    with pytest.raises(ValueError, match="exam_id: Must exist in Exam and be Published"):
        save_attempt(db_session, **data)


# 2. Validate field: student_id - Rule: Must exist in Student; one attempt per exam per student

def test_UT_ATT_04_student_id_accepts_valid(db_session):
    """Check student_id accepts: Existing student (Riya Sharma)"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student)
    att = save_attempt(db_session, **data)
    assert att.student_id == student.student_id


def test_UT_ATT_05_student_id_rejects_non_existent(db_session):
    """Check student_id rejects: student_id 9999 (does not exist)"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"student_id": 9999})
    with pytest.raises(ValueError, match="student_id: Must exist in Student; one attempt per exam per student"):
        save_attempt(db_session, **data)


def test_UT_ATT_06_student_id_rejects_already_submitted(db_session):
    """Check student_id rejects: Student who already submitted this exam"""
    exam, student = setup_exam_and_student(db_session)
    data1 = get_valid_attempt_data(exam, student)
    save_attempt(db_session, **data1)

    data2 = get_valid_attempt_data(exam, student)
    with pytest.raises(ValueError, match="student_id: Must exist in Student; one attempt per exam per student"):
        save_attempt(db_session, **data2)


# 3. Validate field: start_at - Rule: Valid datetime (YYYY-MM-DD HH:MM:SS), inside the exam window, not in the future

def test_UT_ATT_07_start_at_accepts_current_time(db_session):
    """Check start_at accepts: Current date and time (inside the exam window)"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student)
    att = save_attempt(db_session, **data)
    assert att.attempt_id is not None


def test_UT_ATT_08_start_at_rejects_before_start_time(db_session):
    """Check start_at rejects: Time before the exam start_time"""
    exam, student = setup_exam_and_student(db_session)
    before_start = (exam.start_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    data = get_valid_attempt_data(exam, student, {"start_at": before_start})
    with pytest.raises(ValueError, match="start_at: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), inside the exam window, not in the future"):
        save_attempt(db_session, **data)


def test_UT_ATT_09_start_at_rejects_invalid_date(db_session):
    """Check start_at rejects: 2026-13-45 10:00:00"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"start_at": "2026-13-45 10:00:00"})
    with pytest.raises(ValueError, match="start_at: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), inside the exam window, not in the future"):
        save_attempt(db_session, **data)


# 4. Validate field: submit_at - Rule: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_at, not after exam end_time

def test_UT_ATT_10_submit_at_accepts_inside_window(db_session):
    """Check submit_at accepts: start_at + 45 minutes (inside the exam window)"""
    exam, student = setup_exam_and_student(db_session)
    start_dt = datetime.now() - timedelta(minutes=45)
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    submit_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = get_valid_attempt_data(exam, student, {"start_at": start_str, "submit_at": submit_str})
    att = save_attempt(db_session, **data)
    assert att.submit_at is not None


def test_UT_ATT_11_submit_at_rejects_earlier_than_start(db_session):
    """Check submit_at rejects: Earlier than start_at"""
    exam, student = setup_exam_and_student(db_session)
    start_dt = datetime.now()
    earlier = (start_dt - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    data = get_valid_attempt_data(exam, student, {"start_at": start_dt.strftime("%Y-%m-%d %H:%M:%S"), "submit_at": earlier})
    with pytest.raises(ValueError, match="submit_at: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), after start_at, not after exam end_time"):
        save_attempt(db_session, **data)


def test_UT_ATT_12_submit_at_rejects_after_exam_end(db_session):
    """Check submit_at rejects: Time after the exam end_time"""
    exam, student = setup_exam_and_student(db_session)
    start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    after_end = (exam.end_time + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    data = get_valid_attempt_data(exam, student, {"start_at": start_str, "submit_at": after_end})
    with pytest.raises(ValueError, match="submit_at: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), after start_at, not after exam end_time"):
        save_attempt(db_session, **data)


# 5. Validate field: status - Rule: One of: In Progress, Submitted, Auto-Locked

def test_UT_ATT_13_status_accepts_in_progress(db_session):
    """Check status accepts: In Progress"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"status": "In Progress"})
    att = save_attempt(db_session, **data)
    assert att.status == "In Progress"


def test_UT_ATT_14_status_rejects_blank(db_session):
    """Check status rejects: (blank)"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"status": ""})
    with pytest.raises(ValueError, match="status: One of: In Progress, Submitted, Auto-Locked"):
        save_attempt(db_session, **data)


def test_UT_ATT_15_status_rejects_paused(db_session):
    """Check status rejects: Paused"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"status": "Paused"})
    with pytest.raises(ValueError, match="status: One of: In Progress, Submitted, Auto-Locked"):
        save_attempt(db_session, **data)


# 6. Validate field: flagged - Rule: Boolean, default false

def test_UT_ATT_16_flagged_accepts_true(db_session):
    """Check flagged accepts: true"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"flagged": True})
    att = save_attempt(db_session, **data)
    assert att.flagged is True


def test_UT_ATT_17_flagged_rejects_yes(db_session):
    """Check flagged rejects: yes"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"flagged": "yes"})
    with pytest.raises(ValueError, match="flagged: Boolean, default false"):
        save_attempt(db_session, **data)


def test_UT_ATT_18_flagged_rejects_null(db_session):
    """Check flagged rejects: null"""
    exam, student = setup_exam_and_student(db_session)
    data = get_valid_attempt_data(exam, student, {"flagged": None})
    with pytest.raises(ValueError, match="flagged: Boolean, default false"):
        save_attempt(db_session, **data)


# 7. Business logic and relationships

def test_UT_ATT_19_tab_switch_locks_attempt(db_session):
    """Check tab switch locks the attempt."""
    exam, student = setup_exam_and_student(db_session)
    att = save_attempt(db_session, **get_valid_attempt_data(exam, student))

    now_iso = datetime.now(timezone.utc).isoformat()
    on_event(db_session, att.attempt_id, "TAB_SWITCH", now_iso)

    db_session.refresh(att)
    v_log = db_session.query(ViolationLog).filter(ViolationLog.attempt_id == att.attempt_id).first()

    assert v_log is not None
    assert v_log.type == "TAB_SWITCH"
    assert att.flagged is True
    assert att.status == "Auto-Locked"


def test_UT_ATT_20_fullscreen_exit_locks_attempt(db_session):
    """Check fullscreen exit locks the attempt."""
    exam, student = setup_exam_and_student(db_session)
    att = save_attempt(db_session, **get_valid_attempt_data(exam, student))

    now_iso = datetime.now(timezone.utc).isoformat()
    on_event(db_session, att.attempt_id, "FULLSCREEN_EXIT", now_iso)

    db_session.refresh(att)
    v_log = db_session.query(ViolationLog).filter(ViolationLog.attempt_id == att.attempt_id).first()

    assert v_log is not None
    assert v_log.type == "FULLSCREEN_EXIT"
    assert att.flagged is True
    assert att.status == "Auto-Locked"


def test_UT_ATT_21_event_for_submitted_attempt_ignored(db_session):
    """Check event for a submitted attempt is ignored."""
    exam, student = setup_exam_and_student(db_session)
    att = save_attempt(db_session, **get_valid_attempt_data(exam, student, {"status": "Submitted"}))

    now_iso = datetime.now(timezone.utc).isoformat()
    res = on_event(db_session, att.attempt_id, "TAB_SWITCH", now_iso)

    db_session.refresh(att)
    v_count = db_session.query(ViolationLog).filter(ViolationLog.attempt_id == att.attempt_id).count()

    assert res is None
    assert v_count == 0
    assert att.status == "Submitted"


def test_UT_ATT_22_evaluation_calculates_score(db_session):
    """Check evaluation calculates the score (20 questions of 1 mark each, 17 correct)."""
    exam, student = setup_exam_and_student(db_session)
    exam.total_marks = 20
    db_session.commit()

    # Create 20 questions of 1 mark each with answer keys
    questions = []
    for i in range(20):
        q = Question(exam_id=exam.exam_id, text=f"Q{i+1}", options={"A": "1", "B": "2", "C": "3", "D": "4"}, marks=1)
        db_session.add(q)
        db_session.flush()
        ak = AnswerKey(question_id=q.question_id, correct_option="A")
        db_session.add(ak)
        questions.append(q)
    db_session.commit()

    # Attempt
    att = save_attempt(db_session, **get_valid_attempt_data(exam, student))

    # Save 17 correct answers and 3 wrong answers
    answers_dict = {}
    for i in range(20):
        answers_dict[questions[i].question_id] = "A" if i < 17 else "B"
    save_answers(db_session, att.attempt_id, answers_dict)

    # Evaluate
    result = evaluate(db_session, att.attempt_id)

    assert result is not None
    assert float(result.score) == 17.0
    assert float(result.percentage) == 85.0


def test_UT_ATT_23_locked_attempt_evaluated_on_saved_answers(db_session):
    """Check locked attempt is evaluated on saved answers (10 answers saved, 8 correct)."""
    exam, student = setup_exam_and_student(db_session)
    exam.total_marks = 10
    db_session.commit()

    questions = []
    for i in range(10):
        q = Question(exam_id=exam.exam_id, text=f"Q{i+1}", options={"A": "1", "B": "2"}, marks=1)
        db_session.add(q)
        db_session.flush()
        ak = AnswerKey(question_id=q.question_id, correct_option="A")
        db_session.add(ak)
        questions.append(q)
    db_session.commit()

    att = save_attempt(db_session, **get_valid_attempt_data(exam, student))

    # 10 answers saved: 8 correct ('A'), 2 wrong ('B')
    answers_dict = {}
    for i in range(10):
        answers_dict[questions[i].question_id] = "A" if i < 8 else "B"
    save_answers(db_session, att.attempt_id, answers_dict)

    # Lock attempt via event
    now_iso = datetime.now(timezone.utc).isoformat()
    on_event(db_session, att.attempt_id, "TAB_SWITCH", now_iso)

    db_session.refresh(att)
    assert att.status == "Auto-Locked"

    result = db_session.query(Result).filter(Result.attempt_id == att.attempt_id).first()
    assert result is not None
    assert float(result.score) == 8.0


def test_UT_ATT_24_repeated_evaluation_creates_one_result(db_session):
    """Check repeated evaluation creates one result."""
    exam, student = setup_exam_and_student(db_session)
    q = Question(exam_id=exam.exam_id, text="Q1", options={"A": "1", "B": "2"}, marks=20)
    db_session.add(q)
    db_session.flush()
    ak = AnswerKey(question_id=q.question_id, correct_option="A")
    db_session.add(ak)
    db_session.commit()

    att = save_attempt(db_session, **get_valid_attempt_data(exam, student))
    save_answers(db_session, att.attempt_id, {q.question_id: "A"})

    # Evaluate first time
    res1 = evaluate(db_session, att.attempt_id)
    # Evaluate second time
    res2 = evaluate(db_session, att.attempt_id)

    results = db_session.query(Result).filter(Result.attempt_id == att.attempt_id).all()
    assert len(results) == 1
    assert float(res1.score) == float(res2.score) == 20.0
