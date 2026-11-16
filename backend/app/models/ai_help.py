"""AI_HELP_REQUEST table."""

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class AIHelpRequest(Base):
    __tablename__ = "ai_help_requests"

    help_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False)
    prompt = Column(Text, nullable=True)
    ai_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False)

    student = relationship("Student", back_populates="ai_help_requests")
    question = relationship("Question")
