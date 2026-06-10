"""票务 Schema"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class TicketPriceResp(BaseModel):
    id: int
    name: str
    code: str
    category: str
    price: float
    discount_price: Optional[float] = None
    description: Optional[str] = None
    includes: Optional[list] = None

    class Config:
        from_attributes = True


class OrderItemReq(BaseModel):
    ticket_type_id: int
    quantity: int = Field(ge=1, le=10)


class CreateOrderReq(BaseModel):
    visit_date: date
    items: list[OrderItemReq]
    coupon_code: Optional[str] = None


class OrderResp(BaseModel):
    id: int
    order_no: str
    visit_date: date
    total_amount: float
    pay_amount: float
    discount_amount: float = 0
    status: str
    pay_status: str
    qr_code: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
