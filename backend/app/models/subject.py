"""SUBJECT table."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id"), nullable=False)
    hod_id = Column(Integer, ForeignKey("hods.hod_id"), nullable=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=True)

    teacher = relationship("Teacher", back_populates="subjects")
    hod = relationship("HOD", back_populates="subjects")
    exams = relationship("Exam", back_populates="subject")
