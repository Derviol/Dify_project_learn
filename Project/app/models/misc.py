"""排期 / 排队 / 会员 / 社区 / 安全 / 通知 模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, Float, Date, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, nullable=False, index=True)
    event_name = Column(String(100), nullable=False)
    event_type = Column(String(15), nullable=False)     # show/parade/workshop/special
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    location = Column(String(100))
    capacity = Column(Integer)
    enrolled_count = Column(Integer, default=0)
    theme = Column(String(100))
    description = Column(Text)
    notes = Column(Text)
    status = Column(String(15), default="normal")        # normal/cancelled/full
    created_at = Column(DateTime, server_default=func.now())


class QueueRecord(Base):
    __tablename__ = "queue_records"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    project_id = Column(BigInteger, nullable=False, index=True)
    queue_number = Column(Integer, nullable=False)
    queue_date = Column(Date, nullable=False)
    status = Column(String(15), default="waiting")       # waiting/called/serving/completed/cancelled/expired
    taken_at = Column(DateTime, server_default=func.now())
    called_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)


class Member(Base):
    __tablename__ = "members"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    member_no = Column(String(20), unique=True, nullable=False)
    level = Column(Integer, default=1)
    points = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    balance = Column(Float, default=0.0)
    card_type = Column(String(10), default="none")       # none/silver/gold/diamond
    card_expire = Column(Date)
    join_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PointRecord(Base):
    __tablename__ = "point_records"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    member_id = Column(BigInteger, nullable=False)
    points = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(String(200))
    related_order = Column(String(32))
    created_at = Column(DateTime, server_default=func.now())


class CommunityPost(Base):
    __tablename__ = "community_posts"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(JSON)
    post_type = Column(String(15), default="travelogue")  # travelogue/review/guide/question
    related_project = Column(BigInteger)
    tags = Column(JSON)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    status = Column(String(15), default="published")       # published/hidden/deleted
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PostReview(Base):
    __tablename__ = "post_reviews"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    parent_id = Column(BigInteger)
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    status = Column(String(15), default="visible")
    created_at = Column(DateTime, server_default=func.now())


class SafetyRule(Base):
    __tablename__ = "safety_rules"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    rule_code = Column(String(20), unique=True, nullable=False)
    project_type = Column(String(50))
    age_group = Column(String(20))
    weather = Column(String(20))
    rule_content = Column(Text, nullable=False)
    priority = Column(String(10), default="medium")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    type = Column(String(15), nullable=False)            # queue/ticket/schedule/system/promotion
    related_id = Column(String(50))
    is_read = Column(Boolean, default=False)
    channel = Column(String(10), default="app")
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class OperationLog(Base):
    __tablename__ = "operation_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    operator_id = Column(BigInteger, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50))
    target_id = Column(String(50))
    detail = Column(JSON)
    ip_address = Column(String(45))
    created_at = Column(DateTime, server_default=func.now())
