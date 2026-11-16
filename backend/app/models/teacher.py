"""TEACHER table extending USER."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)

    user = relationship("User", back_populates="teacher")
    subjects = relationship("Subject", back_populates="teacher")
