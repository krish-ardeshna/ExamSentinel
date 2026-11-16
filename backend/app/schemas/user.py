"""Pydantic schemas for User module with exact validation rules from UT-USR."""

import re
from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


VALID_ROLES = {"Admin", "Teacher", "Student", "Parent", "HOD"}
VALID_STATUSES = {"Active", "Suspended"}

# Password regex: 8-20 chars, upper, lower, digit, special char, no spaces
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~])[^\s]{8,20}$'
)
NAME_PATTERN = re.compile(r'^[A-Za-z ]{2,100}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


class UserCreate(BaseModel):
    """Schema for creating a user. Validates all fields per UT-USR rules."""
    name: str
    email: str
    password: str
    role: str
    status: str = "Active"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not NAME_PATTERN.match(v):
            raise ValueError("name: Letters and spaces only, 2-100 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not v or len(v) > 100 or not EMAIL_PATTERN.match(v):
            raise ValueError("email: Valid email format, unique, max 100 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "password: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash"
            )
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError("role: One of: Admin, Teacher, Student, Parent, HOD")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError("status: One of: Active, Suspended")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and not NAME_PATTERN.match(v):
            raise ValueError("name: Letters and spaces only, 2-100 characters")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v is not None and (len(v) > 100 or not EMAIL_PATTERN.match(v)):
            raise ValueError("email: Valid email format, unique, max 100 characters")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if v is not None and not PASSWORD_PATTERN.match(v):
            raise ValueError(
                "password: 8-20 characters with upper case, lower case, digit and special character; no spaces; stored as password_hash"
            )
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is not None and v not in VALID_ROLES:
            raise ValueError("role: One of: Admin, Teacher, Student, Parent, HOD")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in VALID_STATUSES:
            raise ValueError("status: One of: Active, Suspended")
        return v


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    user_id: int
    name: str
    email: str
    role: str
    status: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Schema for login."""
    email: str
    password: str


class LoginResponse(BaseModel):
    """Schema for login response."""
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str
