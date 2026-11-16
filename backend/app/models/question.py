"""QUESTION table."""

from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    exam_id = Column(Integer, ForeignKey("exams.exam_id"), nullable=False)
    text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    marks = Column(Integer, nullable=False)

    exam = relationship("Exam", back_populates="questions")
    answer_key = relationship("AnswerKey", back_populates="question", uselist=False)
    answers = relationship("Answer", back_populates="question")
