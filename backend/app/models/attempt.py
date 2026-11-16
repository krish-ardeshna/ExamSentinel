"""EXAM_ATTEMPT table."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    attempt_id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.exam_id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=False)
    submit_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="In Progress")  # In Progress, Submitted, Auto-Locked
    flagged = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
    )

    exam = relationship("Exam", back_populates="attempts")
    student = relationship("Student", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")
    violations = relationship("ViolationLog", back_populates="attempt", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="attempt", uselist=False)
