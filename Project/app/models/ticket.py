"""票务模型"""
from sqlalchemy import Column, BigInteger, Integer, String, Text, Float, Date, DateTime, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class TicketType(Base):
    __tablename__ = "ticket_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    category = Column(String(10), nullable=False)     # adult/child/family/senior/annual
    price = Column(Float, nullable=False)
    discount_price = Column(Float)
    description = Column(Text)
    includes = Column(JSON)
    valid_days = Column(Integer, default=1)
    usage_limit = Column(Integer, default=1)
    status = Column(String(10), default="active")
    created_at = Column(DateTime, server_default=func.now())


class TicketOrder(Base):
    __tablename__ = "ticket_orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(32), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    pay_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    pay_method = Column(String(10), default="wechat")
    pay_status = Column(String(15), default="unpaid")   # unpaid/paid/refunding/refunded
    visit_date = Column(Date, nullable=False, index=True)
    status = Column(String(15), default="pending")       # pending/confirmed/used/cancelled/expired
    qr_code = Column(String(500))
    used_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    refund_amount = Column(Float)
    refund_reason = Column(String(200))
    remark = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class TicketItem(Base):
    __tablename__ = "ticket_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, nullable=False, index=True)
    ticket_type_id = Column(BigInteger, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    visitor_name = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
