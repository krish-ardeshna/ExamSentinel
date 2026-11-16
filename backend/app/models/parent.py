"""PARENT table extending USER."""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Parent(Base):
    __tablename__ = "parents"

    parent_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    phone = Column(String(15), nullable=True)

    user = relationship("User", back_populates="parent")
    children = relationship("Student", back_populates="parent")
