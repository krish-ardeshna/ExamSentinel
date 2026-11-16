"""RESULT table."""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base


class Result(Base):
    __tablename__ = "results"

    result_id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.attempt_id"), nullable=False, unique=True)
    score = Column(Numeric(6, 2), nullable=False)
    percentage = Column(Numeric(5, 2), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    attempt = relationship("ExamAttempt", back_populates="result")
