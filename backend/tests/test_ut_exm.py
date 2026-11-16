"""Unit tests for Exam module (UT-EXM 01 to 24) matching OEPMS_Unit_Testing_Experiment.docx."""

import pytest
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.models.teacher import Teacher
from app.models.subject import Subject
from app.models.exam import Exam
from app.models.question import Question
from app.services.user_service import save_user
from app.services.exam_service import save_exam, publish_exam, edit_question


def setup_teacher_and_subject(db):
    """Helper to create a teacher and subject."""
    t_user = save_user(
        db,
        name="Rajesh Sharma",
        email="rajesh.t@amity.edu",
        password="Teach@1234",
        role="Teacher",
        status="Active",
    )
    subject = Subject(
        teacher_id=t_user.teacher.teacher_id,
        code="CS501",
        name="Data Structures",
        semester=5,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return t_user, subject


def get_future_datetimes():
    """Helper generating valid future start and end times."""
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end = start + timedelta(minutes=60)
    return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")


def get_valid_exam_data(subject_id, overrides=None):
    """Helper returning a dict of valid Exam fields."""
    st, et = get_future_datetimes()
    data = {
        "subject_id": subject_id,
        "title": "Data Structures Unit Test 1",
        "start_time": st,
        "end_time": et,
        "duration_min": 60,
        "total_marks": 20,
        "status": "Draft",
    }
    if overrides:
        data.update(overrides)
    return data


# 1. Validate field: subject_id - Rule: Must exist in Subject and belong to the logged-in Teacher

def test_UT_EXM_01_subject_id_accepts_own_subject(db_session):
    """Check subject_id accepts: Own subject (Data Structures)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id)
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.exam_id is not None
    assert exam.subject_id == subject.subject_id


def test_UT_EXM_02_subject_id_rejects_non_existent(db_session):
    """Check subject_id rejects: subject_id 9999 (does not exist)"""
    t_user, _ = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(9999)
    with pytest.raises(ValueError, match="subject_id: Must exist in Subject and belong to the logged-in Teacher"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_03_subject_id_rejects_other_teacher_subject(db_session):
    """Check subject_id rejects: Subject of another teacher"""
    t_user1, subject1 = setup_teacher_and_subject(db_session)
    t_user2 = save_user(
        db_session,
        name="Other Teacher",
        email="other.t@amity.edu",
        password="Teach@1234",
        role="Teacher",
        status="Active",
    )
    data = get_valid_exam_data(subject1.subject_id)
    with pytest.raises(ValueError, match="subject_id: Must exist in Subject and belong to the logged-in Teacher"):
        save_exam(db_session, t_user2.user_id, **data)


# 2. Validate field: title - Rule: Required, max 150 characters

def test_UT_EXM_04_title_accepts_valid(db_session):
    """Check title accepts: Data Structures Unit Test 1"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"title": "Data Structures Unit Test 1"})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.title == "Data Structures Unit Test 1"


def test_UT_EXM_05_title_rejects_empty(db_session):
    """Check title rejects: (empty)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"title": ""})
    with pytest.raises(ValueError, match="title: Required, max 150 characters"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_06_title_rejects_max_plus_one(db_session):
    """Check title rejects: 151-character text (max+1)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"title": "A" * 151})
    with pytest.raises(ValueError, match="title: Required, max 150 characters"):
        save_exam(db_session, t_user.user_id, **data)


# 3. Validate field: start_time - Rule: Valid datetime (YYYY-MM-DD HH:MM:SS), must be in the future

def test_UT_EXM_07_start_time_accepts_tomorrow(db_session):
    """Check start_time accepts: Tomorrow 10:00:00"""
    t_user, subject = setup_teacher_and_subject(db_session)
    st, et = get_future_datetimes()
    data = get_valid_exam_data(subject.subject_id, {"start_time": st, "end_time": et})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.exam_id is not None


def test_UT_EXM_08_start_time_rejects_yesterday(db_session):
    """Check start_time rejects: Yesterday 10:00:00"""
    t_user, subject = setup_teacher_and_subject(db_session)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
    _, et = get_future_datetimes()
    data = get_valid_exam_data(subject.subject_id, {"start_time": yesterday, "end_time": et})
    with pytest.raises(ValueError, match="start_time: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), must be in the future"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_09_start_time_rejects_invalid_date(db_session):
    """Check start_time rejects: 2026-13-45 10:00:00"""
    t_user, subject = setup_teacher_and_subject(db_session)
    _, et = get_future_datetimes()
    data = get_valid_exam_data(subject.subject_id, {"start_time": "2026-13-45 10:00:00", "end_time": et})
    with pytest.raises(ValueError, match="start_time: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), must be in the future"):
        save_exam(db_session, t_user.user_id, **data)


# 4. Validate field: end_time - Rule: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_time

def test_UT_EXM_10_end_time_accepts_valid(db_session):
    """Check end_time accepts: start_time + 60 minutes"""
    t_user, subject = setup_teacher_and_subject(db_session)
    st, et = get_future_datetimes()
    data = get_valid_exam_data(subject.subject_id, {"start_time": st, "end_time": et})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.exam_id is not None


def test_UT_EXM_11_end_time_rejects_earlier_than_start(db_session):
    """Check end_time rejects: Earlier than start_time"""
    t_user, subject = setup_teacher_and_subject(db_session)
    st, _ = get_future_datetimes()
    earlier = (datetime.strptime(st, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    data = get_valid_exam_data(subject.subject_id, {"start_time": st, "end_time": earlier})
    with pytest.raises(ValueError, match="end_time: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), after start_time"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_12_end_time_rejects_invalid_calendar_date(db_session):
    """Check end_time rejects: 2026-02-30 11:00:00"""
    t_user, subject = setup_teacher_and_subject(db_session)
    st, _ = get_future_datetimes()
    data = get_valid_exam_data(subject.subject_id, {"start_time": st, "end_time": "2026-02-30 11:00:00"})
    with pytest.raises(ValueError, match="end_time: Valid datetime \\(YYYY-MM-DD HH:MM:SS\\), after start_time"):
        save_exam(db_session, t_user.user_id, **data)


# 5. Validate field: duration_min - Rule: Integer from 1 to 180 (assumed)

def test_UT_EXM_13_duration_min_accepts_60(db_session):
    """Check duration_min accepts: 60"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"duration_min": 60})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.duration_min == 60


def test_UT_EXM_14_duration_min_rejects_0(db_session):
    """Check duration_min rejects: 0"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"duration_min": 0})
    with pytest.raises(ValueError, match="duration_min: Integer from 1 to 180 \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_15_duration_min_rejects_181(db_session):
    """Check duration_min rejects: 181 (max+1)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"duration_min": 181})
    with pytest.raises(ValueError, match="duration_min: Integer from 1 to 180 \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


# 6. Validate field: total_marks - Rule: Integer from 1 to 100 (assumed)

def test_UT_EXM_16_total_marks_accepts_20(db_session):
    """Check total_marks accepts: 20"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"total_marks": 20})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.total_marks == 20


def test_UT_EXM_17_total_marks_rejects_0(db_session):
    """Check total_marks rejects: 0"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"total_marks": 0})
    with pytest.raises(ValueError, match="total_marks: Integer from 1 to 100 \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_18_total_marks_rejects_101(db_session):
    """Check total_marks rejects: 101 (max+1)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"total_marks": 101})
    with pytest.raises(ValueError, match="total_marks: Integer from 1 to 100 \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


# 7. Validate field: status - Rule: One of: Draft, Published, Completed (assumed)

def test_UT_EXM_19_status_accepts_Draft(db_session):
    """Check status accepts: Draft"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"status": "Draft"})
    exam = save_exam(db_session, t_user.user_id, **data)
    assert exam.status == "Draft"


def test_UT_EXM_20_status_rejects_blank(db_session):
    """Check status rejects: (blank)"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"status": ""})
    with pytest.raises(ValueError, match="status: One of: Draft, Published, Completed \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


def test_UT_EXM_21_status_rejects_Cancelled(db_session):
    """Check status rejects: Cancelled"""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"status": "Cancelled"})
    with pytest.raises(ValueError, match="status: One of: Draft, Published, Completed \\(assumed\\)"):
        save_exam(db_session, t_user.user_id, **data)


# 8. Business logic and relationships

def test_UT_EXM_22_exam_with_no_questions_cannot_be_published(db_session):
    """Check exam with no questions cannot be published."""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id)
    exam = save_exam(db_session, t_user.user_id, **data)

    with pytest.raises(ValueError, match="Add at least one question"):
        publish_exam(db_session, exam.exam_id, t_user.user_id)

    db_session.refresh(exam)
    assert exam.status == "Draft"


def test_UT_EXM_23_total_marks_must_equal_sum_of_question_marks(db_session):
    """Check total_marks must equal the sum of question marks."""
    t_user, subject = setup_teacher_and_subject(db_session)
    data = get_valid_exam_data(subject.subject_id, {"total_marks": 20})
    exam = save_exam(db_session, t_user.user_id, **data)

    # Add questions totaling 18 marks (not 20)
    q1 = Question(exam_id=exam.exam_id, text="Q1", options={"A": "1", "B": "2"}, marks=10)
    q2 = Question(exam_id=exam.exam_id, text="Q2", options={"A": "1", "B": "2"}, marks=8)
    db_session.add_all([q1, q2])
    db_session.commit()

    with pytest.raises(ValueError, match="total_marks must equal the sum of question marks"):
        publish_exam(db_session, exam.exam_id, t_user.user_id)


def test_UT_EXM_24_paper_cannot_be_edited_after_exam_start(db_session):
    """Check paper cannot be edited after exam start."""
    t_user, subject = setup_teacher_and_subject(db_session)
    # Create exam whose start_time has passed
    now = datetime.now(timezone.utc)
    exam = Exam(
        subject_id=subject.subject_id,
        title="Started Exam",
        start_time=now - timedelta(minutes=10),
        end_time=now + timedelta(minutes=50),
        duration_min=60,
        total_marks=10,
        status="Published",
    )
    db_session.add(exam)
    db_session.flush()

    q = Question(exam_id=exam.exam_id, text="Q1 Original", options={"A": "1", "B": "2"}, marks=10)
    db_session.add(q)
    db_session.commit()

    with pytest.raises(ValueError, match="Edit rejected; the paper is locked after start_time"):
        edit_question(db_session, q.question_id, t_user.user_id, text="Q1 Modified")
