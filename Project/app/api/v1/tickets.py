"""票务路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ok, fail, page
from app.schemas.ticket import CreateOrderReq
from app.services.ticket_service import TicketService

router = APIRouter()


@router.get("/prices")
async def get_prices(db: AsyncSession = Depends(get_db)):
    types = await TicketService(db).get_prices()
    items = [{
        "id": t.id, "name": t.name, "code": t.code, "category": t.category,
        "price": t.price, "discount_price": t.discount_price,
        "description": t.description, "includes": t.includes,
    } for t in types]
    return ok(items)


@router.post("/orders")
async def create_order(req: CreateOrderReq, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await TicketService(db).create_order(
        user_id=user.id, visit_date=req.visit_date.isoformat(),
        items=[i.model_dump() for i in req.items], coupon_code=req.coupon_code,
    )
    return ok(result)


@router.get("/orders")
async def list_orders(
    p: int = Query(1, alias="page"), ps: int = Query(10, alias="page_size"),
    user=Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    orders, total = await TicketService(db).get_my_orders(user.id, page=p, size=ps)
    items = [{
        "order_no": o.order_no, "visit_date": str(o.visit_date),
        "total_amount": o.total_amount, "pay_amount": o.pay_amount,
        "status": o.status, "pay_status": o.pay_status, "qr_code": o.qr_code,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    } for o in orders]
    return page(items, total)


@router.get("/orders/{order_no}")
async def get_order(order_no: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await TicketService(db).get_order_detail(order_no, user.id)
    return ok({
        "order_no": order.order_no, "visit_date": str(order.visit_date),
        "total_amount": order.total_amount, "pay_amount": order.pay_amount,
        "discount_amount": order.discount_amount, "status": order.status,
        "pay_status": order.pay_status, "qr_code": order.qr_code,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    })


@router.post("/orders/{order_no}/pay")
async def pay_order(order_no: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await TicketService(db).pay_order(order_no, user.id)
    return ok(result)


@router.post("/orders/{order_no}/cancel")
async def cancel_order(order_no: str, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await TicketService(db).cancel_order(order_no, user.id)
    return ok(result)


@router.get("/my-tickets")
async def my_active_tickets(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取当前用户所有未过期的有效票据（Redis 缓存中仍在有效期内的）"""
    tickets = await TicketService(db).get_user_active_tickets(user.id)
    return ok({"valid": len(tickets) > 0, "tickets": tickets})
