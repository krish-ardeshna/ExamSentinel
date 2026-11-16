"""Pydantic schemas for Exam Attempt module with exact validation rules from UT-ATT."""

from typing import Optional, Dict
from pydantic import BaseModel, field_validator


VALID_ATTEMPT_STATUSES = {"In Progress", "Submitted", "Auto-Locked"}


class AttemptCreate(BaseModel):
    """Schema for creating an exam attempt. Validates per UT-ATT rules."""
    exam_id: int
    student_id: int
    start_at: str  # YYYY-MM-DD HH:MM:SS
    submit_at: Optional[str] = None
    status: str = "In Progress"
    flagged: bool = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_ATTEMPT_STATUSES:
            raise ValueError("status: One of: In Progress, Submitted, Auto-Locked")
        return v

    @field_validator("flagged", mode="before")
    @classmethod
    def validate_flagged(cls, v):
        if v is None:
            raise ValueError("flagged: Boolean, default false")
        if not isinstance(v, bool):
            raise ValueError("flagged: Boolean, default false")
        return v


class AttemptResponse(BaseModel):
    """Schema for attempt response."""
    attempt_id: int
    exam_id: int
    student_id: int
    start_at: Optional[str] = None
    submit_at: Optional[str] = None
    status: str
    flagged: bool

    class Config:
        from_attributes = True


class AnswerSave(BaseModel):
    """Schema for saving/autosaving answers."""
    answers: Dict[int, str]  # {question_id: selected_option}


class EventCreate(BaseModel):
    """Schema for proctoring event."""
    event_type: str  # TAB_SWITCH, FULLSCREEN_EXIT
    timestamp: str  # ISO format


class SubmitResponse(BaseModel):
    """Schema for submit response."""
    attempt_id: int
    status: str
    message: str


class AIHelpRequestSchema(BaseModel):
    """Schema for AI help request."""
    question_id: int


class AIHelpResponse(BaseModel):
    """Schema for AI help response."""
    question_id: int
    explanation: str
    question_text: Optional[str] = None
    student_answer: Optional[str] = None
    correct_answer: Optional[str] = None
