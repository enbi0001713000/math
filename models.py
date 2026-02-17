from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Integer, String, UniqueConstraint

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


class UnitTestAttempt(Base):
    __tablename__ = "unit_test_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)
    score_percent = Column(Float, nullable=False)
    is_passed = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ReviewAttempt(Base):
    __tablename__ = "review_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    unit_id = Column(String, nullable=False, index=True)
    review_set_id = Column(String, nullable=False)
    correct_count = Column(Integer, nullable=False)
    is_cleared = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DailyLearningLog(Base):
    __tablename__ = "daily_learning_logs"
    __table_args__ = (UniqueConstraint("user_id", "learning_date", name="uq_daily_learning"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    learning_date = Column(Date, default=date.today, nullable=False)
    answered_count = Column(Integer, default=0, nullable=False)


class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    question_id = Column(String, nullable=False)
    recommended_date = Column(Date, default=date.today, nullable=False)
    source = Column(String, default="random", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True)
    badge_id = Column(String, nullable=False)
    badge_name = Column(String, nullable=False)
    badge_type = Column(String, nullable=False)
    condition_value = Column(Integer, nullable=True)
    awarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
