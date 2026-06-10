"""项目与设施模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, Boolean, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    zone = Column(String(50), nullable=False, index=True)
    category = Column(String(10), nullable=False, index=True)  # ride/venue/show/water
    description = Column(Text)
    suitable_age = Column(String(50))
    min_height = Column(Float)
    max_height = Column(Float)
    intensity = Column(String(10), default="low")     # low/medium/high
    is_indoor = Column(Boolean, default=False)
    has_ac = Column(Boolean, default=False)
    stroller_friendly = Column(Boolean, default=True)
    duration_minutes = Column(Integer)
    capacity = Column(Integer)
    fast_pass = Column(Boolean, default=False)
    fast_pass_price = Column(Float)
    queue_enabled = Column(Boolean, default=True)
    cover_image = Column(String(500))
    location_desc = Column(String(200))
    tips = Column(Text)
    safety_notes = Column(Text)
    status = Column(String(15), default="open", index=True)  # open/closed/maintenance
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False, index=True)
    zone = Column(String(50), index=True)
    location_desc = Column(String(200))
    open_time = Column(String(10))
    close_time = Column(String(10))
    features = Column(JSON)
    price_info = Column(String(200))
    contact_phone = Column(String(20))
    status = Column(String(15), default="open")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
