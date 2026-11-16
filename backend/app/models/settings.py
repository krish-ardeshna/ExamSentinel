"""Platform settings table for admin-configurable parameters."""

from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class PlatformSetting(Base):
    __tablename__ = "platform_settings"

    setting_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    updated_by = Column(Integer, nullable=True)  # user_id of admin
