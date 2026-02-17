from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserUnitProgress(Base):
    __tablename__ = "user_unit_progress"
    __table_args__ = (UniqueConstraint("user_id", "unit_id", name="uq_user_unit"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="not_started")
    current_step_order = Column(Integer, nullable=False, default=1)
    current_step_type = Column(String, nullable=False, default="intro")
    completed_at = Column(DateTime, nullable=True)
