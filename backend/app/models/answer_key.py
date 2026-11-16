"""ANSWER_KEY table."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class AnswerKey(Base):
    __tablename__ = "answer_keys"

    key_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.question_id"), nullable=False, unique=True)
    correct_option = Column(String(5), nullable=False)

    question = relationship("Question", back_populates="answer_key")
