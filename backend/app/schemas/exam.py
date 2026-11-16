"""Pydantic schemas for Exam module with exact validation rules from UT-EXM."""

from typing import Optional, List, Dict
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime


VALID_EXAM_STATUSES = {"Draft", "Published", "Completed"}


class ExamCreate(BaseModel):
    """Schema for creating an exam. Validates all fields per UT-EXM rules."""
    subject_id: int
    title: str
    start_time: str  # Accept as string, parse to datetime
    end_time: str
    duration_min: int
    total_marks: int
    status: str = "Draft"

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip() or len(v) > 150:
            raise ValueError("title: Required, max 150 characters")
        return v

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, v: str) -> str:
        try:
            dt = datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            raise ValueError("start_time: Valid datetime (YYYY-MM-DD HH:MM:SS), must be in the future")
        if dt <= datetime.now():
            raise ValueError("start_time: Valid datetime (YYYY-MM-DD HH:MM:SS), must be in the future")
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            raise ValueError("end_time: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_time")
        return v

    @field_validator("duration_min")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 1 or v > 180:
            raise ValueError("duration_min: Integer from 1 to 180 (assumed)")
        return v

    @field_validator("total_marks")
    @classmethod
    def validate_total_marks(cls, v: int) -> int:
        if v < 1 or v > 100:
            raise ValueError("total_marks: Integer from 1 to 100 (assumed)")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_EXAM_STATUSES:
            raise ValueError("status: One of: Draft, Published, Completed (assumed)")
        return v

    @model_validator(mode="after")
    def validate_end_after_start(self):
        try:
            st = datetime.strptime(self.start_time, "%Y-%m-%d %H:%M:%S")
            et = datetime.strptime(self.end_time, "%Y-%m-%d %H:%M:%S")
            if et <= st:
                raise ValueError("end_time: Valid datetime (YYYY-MM-DD HH:MM:SS), after start_time")
        except ValueError as e:
            if "end_time" in str(e):
                raise
        return self


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""
    title: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_min: Optional[int] = None
    total_marks: Optional[int] = None
    status: Optional[str] = None


class ExamResponse(BaseModel):
    """Schema for exam response."""
    exam_id: int
    subject_id: int
    title: str
    start_time: datetime
    end_time: datetime
    duration_min: int
    total_marks: int
    status: str
    question_count: Optional[int] = 0

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    """Schema for creating a question."""
    text: str
    options: Dict[str, str]
    marks: int


class QuestionResponse(BaseModel):
    """Schema for question response."""
    question_id: int
    exam_id: int
    text: str
    options: Dict[str, str]
    marks: int

    class Config:
        from_attributes = True


class AnswerKeyCreate(BaseModel):
    """Schema for submitting answer key."""
    answers: Dict[int, str]  # {question_id: correct_option}


class AnswerKeyResponse(BaseModel):
    """Schema for answer key response."""
    question_id: int
    correct_option: str

    class Config:
        from_attributes = True
