"""M1: User & Access Management service.

Handles user CRUD, login/logout, role assignment, password hashing,
account lockout (5 failed logins = 15 min lock), and deletion rules.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.hod import HOD
from app.models.attempt import ExamAttempt
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token

# Constants
MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def validate_and_create_user(db: Session, data: UserCreate) -> User:
    """Validate input and create a user. Raises ValueError on validation failure.

    This is the save/validate method referenced by the unit tests.
    """
    # Check email uniqueness
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise ValueError("email: Valid email format, unique, max 100 characters")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        status=data.status,
    )
    db.add(user)
    db.flush()

    # Create role-specific record
    _create_role_record(db, user)

    db.commit()
    db.refresh(user)
    return user


def save_user(db: Session, **kwargs) -> User:
    """Save/validate method for User module per UT-USR requirements.

    Validates inputs and saves record. If invalid, raises ValueError("<field>: <rule>")
    and ensures nothing is saved.
    """
    try:
        data = UserCreate(**kwargs)
    except Exception as e:
        msg = str(e)
        if hasattr(e, "errors"):
            msg = e.errors()[0]["msg"]
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
        raise ValueError(msg)
    return validate_and_create_user(db, data)



def _create_role_record(db: Session, user: User):
    """Create the role-specific table entry for a user."""
    if user.role == "Student":
        student = Student(user_id=user.user_id)
        db.add(student)
    elif user.role == "Teacher":
        teacher = Teacher(user_id=user.user_id)
        db.add(teacher)
    elif user.role == "Parent":
        parent = Parent(user_id=user.user_id)
        db.add(parent)
    elif user.role == "HOD":
        hod = HOD(user_id=user.user_id)
        db.add(hod)
    # Admin has no separate table


def login(db: Session, email: str, password: str) -> dict:
    """Authenticate a user and return JWT token.

    Business rules:
    - Suspended users cannot log in
    - 5 failed logins lock the account for 15 minutes
    - Successful login returns JWT with role
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Invalid credentials")

    # Check if account is suspended
    if user.status == "Suspended":
        raise ValueError("Account suspended")

    # Check if account is locked
    if user.locked_until:
        locked_until = user.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        if locked_until > datetime.now(timezone.utc):
            raise ValueError("Account is locked for 15 minutes")


    # Verify password
    if not verify_password(password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
        db.commit()
        raise ValueError("Invalid credentials")

    # Successful login - reset failed count
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()

    token = create_access_token(data={"sub": str(user.user_id), "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.user_id,
        "name": user.name,
    }


def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.user_id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    """Update a user's fields."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email, User.user_id != user_id).first()
        if existing:
            raise ValueError("email: Valid email format, unique, max 100 characters")
        user.email = data.email
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        user.role = data.role
    if data.status is not None:
        user.status = data.status

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user with business rule checks.

    - Cannot delete user with an active attempt (In Progress)
    - Cannot remove the last Admin
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Check if this is the last admin
    if user.role == "Admin":
        admin_count = db.query(User).filter(User.role == "Admin").count()
        if admin_count <= 1:
            raise ValueError("Deletion rejected; at least one Admin must remain")

    # Check if user has an active attempt
    if user.role == "Student" and user.student:
        active_attempt = (
            db.query(ExamAttempt)
            .filter(
                ExamAttempt.student_id == user.student.student_id,
                ExamAttempt.status == "In Progress",
            )
            .first()
        )
        if active_attempt:
            raise ValueError("Deletion rejected; the user can only be Suspended")

    db.delete(user)
    db.commit()
    return True
