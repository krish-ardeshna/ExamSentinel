"""VIOLATION_LOG table."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class ViolationLog(Base):
    __tablename__ = "violation_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.attempt_id"), nullable=False)
    type = Column(String(30), nullable=False)  # TAB_SWITCH, FULLSCREEN_EXIT
    occurred_at = Column(DateTime(timezone=True), nullable=False)

    attempt = relationship("ExamAttempt", back_populates="violations")
