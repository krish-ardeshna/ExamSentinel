"""Unit tests for User module (UT-USR 01 to 24) matching OEPMS_Unit_Testing_Experiment.docx."""

import pytest
from app.models.user import User
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.exam import Exam
from app.models.attempt import ExamAttempt
from app.services.user_service import save_user, login, delete_user
from app.core.security import decode_access_token
from datetime import datetime, timedelta, timezone


def get_valid_user_data(overrides=None):
    """Helper returning a dict of valid User fields."""
    data = {
        "name": "Riya Sharma",
        "email": "riya.valid@amity.edu",
        "password": "Stud@1234",
        "role": "Student",
        "status": "Active",
    }
    if overrides:
        data.update(overrides)
    return data


# 1. Validate field: name - Rule: Letters and spaces only, 2-100 characters

def test_UT_USR_01_name_accepts_valid(db_session):
    """Check name accepts: Riya Sharma"""
    data = get_valid_user_data({"name": "Riya Sharma"})
    user = save_user(db_session, **data)
    assert user.user_id is not None
    assert user.name == "Riya Sharma"


def test_UT_USR_02_name_rejects_digits(db_session):
    """Check name rejects: Riya123"""
    data = get_valid_user_data({"name": "Riya123"})
    with pytest.raises(ValueError, match="name: Letters and spaces only, 2-100 characters"):
        save_user(db_session, **data)
    assert db_session.query(User).filter(User.name == "Riya123").first() is None


def test_UT_USR_03_name_rejects_empty(db_session):
    """Check name rejects: (empty)"""
    data = get_valid_user_data({"name": ""})
    with pytest.raises(ValueError, match="name: Letters and spaces only, 2-100 characters"):
        save_user(db_session, **data)


def test_UT_USR_04_name_rejects_max_plus_one(db_session):
    """Check name rejects: 101-character text (max+1)"""
    data = get_valid_user_data({"name": "A" * 101})
    with pytest.raises(ValueError, match="name: Letters and spaces only, 2-100 characters"):
        save_user(db_session, **data)


# 2. Validate field: email - Rule: Valid email format, unique, max 100 characters

def test_UT_USR_05_email_accepts_valid(db_session):
    """Check email accepts: riya@amity.edu"""
    data = get_valid_user_data({"email": "riya@amity.edu"})
    user = save_user(db_session, **data)
    assert user.email == "riya@amity.edu"


def test_UT_USR_06_email_rejects_invalid_format(db_session):
    """Check email rejects: riya.amity.edu"""
    data = get_valid_user_data({"email": "riya.amity.edu"})
    with pytest.raises(ValueError, match="email: Valid email format, unique, max 100 characters"):
        save_user(db_session, **data)


def test_UT_USR_07_email_rejects_duplicate(db_session):
    """Check email rejects: riya@amity.edu (duplicate)"""
    data1 = get_valid_user_data({"email": "riya@amity.edu"})
    save_user(db_session, **data1)

    data2 = get_valid_user_data({"name": "Another User", "email": "riya@amity.edu"})
    with pytest.raises(ValueError, match="email: Valid email format, unique, max 100 characters"):
        save_user(db_session, **data2)


def test_UT_USR_08_email_rejects_max_plus_one(db_session):
    """Check email rejects: 101-character email (max+1)"""
    long_prefix = "a" * 92  # 92 + @amity.edu (10) = 102 chars
    data = get_valid_user_data({"email": f"{long_prefix}@amity.edu"})
    with pytest.raises(ValueError, match="email: Valid email format, unique, max 100 characters"):
        save_user(db_session, **data)


# 3. Validate field: password - Rule: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash

def test_UT_USR_09_password_accepts_valid(db_session):
    """Check password accepts: Stud@1234"""
    data = get_valid_user_data({"password": "Stud@1234"})
    user = save_user(db_session, **data)
    assert user.user_id is not None


def test_UT_USR_10_password_rejects_too_short(db_session):
    """Check password rejects: Ab1@ (too short)"""
    data = get_valid_user_data({"password": "Ab1@"})
    with pytest.raises(ValueError, match="password: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash"):
        save_user(db_session, **data)


def test_UT_USR_11_password_rejects_no_special(db_session):
    """Check password rejects: Student1234 (no special character)"""
    data = get_valid_user_data({"password": "Student1234"})
    with pytest.raises(ValueError, match="password: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash"):
        save_user(db_session, **data)


def test_UT_USR_12_password_rejects_max_plus_one(db_session):
    """Check password rejects: 21-character password (max+1)"""
    data = get_valid_user_data({"password": "Student@1234567890123"})
    with pytest.raises(ValueError, match="password: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash"):
        save_user(db_session, **data)


# 4. Validate field: role - Rule: One of: Admin, Teacher, Student, Parent, HOD

def test_UT_USR_13_role_accepts_valid(db_session):
    """Check role accepts: Student"""
    data = get_valid_user_data({"role": "Student"})
    user = save_user(db_session, **data)
    assert user.role == "Student"


def test_UT_USR_14_role_rejects_blank(db_session):
    """Check role rejects: (blank)"""
    data = get_valid_user_data({"role": ""})
    with pytest.raises(ValueError, match="role: One of: Admin, Teacher, Student, Parent, HOD"):
        save_user(db_session, **data)


def test_UT_USR_15_role_rejects_invalid_role(db_session):
    """Check role rejects: Principal"""
    data = get_valid_user_data({"role": "Principal"})
    with pytest.raises(ValueError, match="role: One of: Admin, Teacher, Student, Parent, HOD"):
        save_user(db_session, **data)


# 5. Validate field: status - Rule: One of: Active, Suspended

def test_UT_USR_16_status_accepts_valid(db_session):
    """Check status accepts: Active"""
    data = get_valid_user_data({"status": "Active"})
    user = save_user(db_session, **data)
    assert user.status == "Active"


def test_UT_USR_17_status_rejects_blank(db_session):
    """Check status rejects: (blank)"""
    data = get_valid_user_data({"status": ""})
    with pytest.raises(ValueError, match="status: One of: Active, Suspended"):
        save_user(db_session, **data)


def test_UT_USR_18_status_rejects_deleted(db_session):
    """Check status rejects: Deleted"""
    data = get_valid_user_data({"status": "Deleted"})
    with pytest.raises(ValueError, match="status: One of: Active, Suspended"):
        save_user(db_session, **data)


# 6. Business logic and relationships

def test_UT_USR_19_password_is_stored_hashed(db_session):
    """Check password is stored hashed."""
    plain_password = "Stud@1234"
    data = get_valid_user_data({"password": plain_password})
    user = save_user(db_session, **data)
    assert user.password_hash != plain_password
    assert len(user.password_hash) > 20


def test_UT_USR_20_suspended_user_cannot_login(db_session):
    """Check suspended user cannot login."""
    data = get_valid_user_data({"email": "suspended@amity.edu", "status": "Suspended"})
    save_user(db_session, **data)
    with pytest.raises(ValueError, match="Account suspended"):
        login(db_session, "suspended@amity.edu", "Stud@1234")


def test_UT_USR_21_five_failed_logins_lock_account(db_session):
    """Check 5 failed logins lock the account."""
    data = get_valid_user_data({"email": "locktest@amity.edu", "password": "Stud@1234"})
    save_user(db_session, **data)

    # 5 failed logins
    for _ in range(5):
        with pytest.raises(ValueError, match="Invalid credentials"):
            login(db_session, "locktest@amity.edu", "WrongPass@1")

    # 6th attempt with correct password should be rejected as locked
    with pytest.raises(ValueError, match="Account is locked for 15 minutes"):
        login(db_session, "locktest@amity.edu", "Stud@1234")


def test_UT_USR_22_successful_login_returns_role_token(db_session):
    """Check successful login returns a role token."""
    data = get_valid_user_data({"email": "student01@amity.edu", "role": "Student"})
    save_user(db_session, **data)

    res = login(db_session, "student01@amity.edu", "Stud@1234")
    assert "access_token" in res
    assert res["role"] == "Student"

    payload = decode_access_token(res["access_token"])
    assert payload is not None
    assert payload.get("role") == "Student"


def test_UT_USR_23_user_with_active_attempt_cannot_be_deleted(db_session):
    """Check user with an active attempt cannot be deleted."""
    # Create student
    user = save_user(db_session, **get_valid_user_data({"email": "active.student@amity.edu"}))
    student = user.student

    # Create teacher & subject
    t_user = save_user(db_session, **get_valid_user_data({"name": "Teacher User", "email": "t@amity.edu", "role": "Teacher"}))
    subject = Subject(teacher_id=t_user.teacher.teacher_id, code="CS101", name="CS")
    db_session.add(subject)
    db_session.flush()

    # Create exam
    now = datetime.now(timezone.utc)
    exam = Exam(
        subject_id=subject.subject_id,
        title="Test Exam",
        start_time=now - timedelta(hours=1),
        end_time=now + timedelta(hours=1),
        duration_min=60,
        total_marks=20,
        status="Published",
    )
    db_session.add(exam)
    db_session.flush()

    # Create In Progress attempt
    attempt = ExamAttempt(
        exam_id=exam.exam_id,
        student_id=student.student_id,
        start_at=now,
        status="In Progress",
        flagged=False,
    )
    db_session.add(attempt)
    db_session.commit()

    with pytest.raises(ValueError, match="Deletion rejected; the user can only be Suspended"):
        delete_user(db_session, user.user_id)


def test_UT_USR_24_last_admin_cannot_be_removed(db_session):
    """Check last Admin cannot be removed."""
    admin = save_user(db_session, **get_valid_user_data({"name": "Main Admin", "email": "admin@amity.edu", "role": "Admin"}))
    with pytest.raises(ValueError, match="Deletion rejected; at least one Admin must remain"):
        delete_user(db_session, admin.user_id)
