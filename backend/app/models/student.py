"""STUDENT table extending USER."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    parent_id = Column(Integer, ForeignKey("parents.parent_id"), nullable=True)
    enrollment_no = Column(String(30), unique=True, nullable=True)
    program = Column(String(100), nullable=True)
    semester = Column(Integer, nullable=True)

    user = relationship("User", back_populates="student")
    parent = relationship("Parent", back_populates="children")
    attempts = relationship("ExamAttempt", back_populates="student")
    ai_help_requests = relationship("AIHelpRequest", back_populates="student")
