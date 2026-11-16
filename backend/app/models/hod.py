"""HOD table extending USER."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class HOD(Base):
    __tablename__ = "hods"

    hod_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    department = Column(String(100), nullable=True)

    user = relationship("User", back_populates="hod")
    subjects = relationship("Subject", back_populates="hod")
