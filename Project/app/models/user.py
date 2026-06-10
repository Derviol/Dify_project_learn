"""用户模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, Date, DateTime, Enum, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, index=True)
    email = Column(String(100), unique=True)
    password_hash = Column(String(255))
    nickname = Column(String(50), nullable=False, default="游客")
    avatar_url = Column(String(500))
    wechat_openid = Column(String(100), unique=True, index=True)
    wechat_unionid = Column(String(100))
    role = Column(String(10), default="user")       # user / admin / staff
    status = Column(String(10), default="active")    # active / banned / deleted
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    child_age = Column(String(20))
    child_gender = Column(String(10), default="unknown")
    interests = Column(JSON)                         # ["动物","表演","冒险"]
    visit_count = Column(Integer, default=0)
    special_needs = Column(Text)
    preferred_zones = Column(JSON)
    last_visit_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
