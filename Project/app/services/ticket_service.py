"""票务服务"""
import uuid
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import and_
from app.models.ticket import TicketType, TicketOrder, TicketItem
from app.core.exceptions import BizError
from app.core.redis import get_redis

# Redis 票据缓存 TTL: 12 小时
TICKET_REDIS_TTL = 12 * 3600  # 43200 秒
TICKET_REDIS_PREFIX = "ticket:active:"


class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_prices(self) -> list[TicketType]:
        result = await self.db.execute(
            select(TicketType).where(TicketType.status == "active").order_by(TicketType.id)
        )
        return list(result.scalars().all())

    async def create_order(self, user_id: int, visit_date: str, items: list[dict], coupon_code: str = None) -> dict:
        vd = date.fromisoformat(visit_date)
        if vd < date.today():
            raise BizError(40001, "游玩日期不能早于今天")

        total = 0.0
        order_items = []
        for item in items:
            tt = await self.db.get(TicketType, item["ticket_type_id"])
            if not tt or tt.status != "active":
                raise BizError(40001, f"票种不存在或已下架")
            price = tt.discount_price or tt.price
            subtotal = price * item["quantity"]
            total += subtotal
            order_items.append({
                "ticket_type_id": tt.id,
                "quantity": item["quantity"],
                "unit_price": price,
                "subtotal": subtotal,
            })

        discount = 0.0
        if coupon_code == "SUMMER2026":
            discount = 20.0

        order_no = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        order = TicketOrder(
            order_no=order_no, user_id=user_id,
            total_amount=total, pay_amount=total - discount,
            discount_amount=discount, visit_date=vd,
            status="pending", pay_status="unpaid",
        )
        self.db.add(order)
        await self.db.flush()

        for oi in order_items:
            self.db.add(TicketItem(order_id=order.id, **oi))

        await self.db.commit()
        await self.db.refresh(order)

        return {
            "order_no": order.order_no,
            "total_amount": order.total_amount,
            "discount_amount": order.discount_amount,
            "pay_amount": order.pay_amount,
            "status": order.status,
        }

    async def pay_order(self, order_no: str, user_id: int) -> dict:
        # SELECT FOR UPDATE 行锁，防止并发重复支付
        result = await self.db.execute(
            select(TicketOrder)
            .where(TicketOrder.order_no == order_no, TicketOrder.user_id == user_id)
            .with_for_update()
        )
        order = result.scalar_one_or_none()
        if not order:
            raise BizError(40401, "订单不存在")
        if order.pay_status == "paid":
            raise BizError(40001, "订单已支付")

        order.pay_status = "paid"
        order.status = "confirmed"
        order.qr_code = f"LELE-{order_no}-{uuid.uuid4().hex[:8]}"
        await self.db.commit()

        # 写入 Redis 缓存，12 小时自动过期
        try:
            r = await get_redis()
            await r.set(f"{TICKET_REDIS_PREFIX}{order_no}", user_id, ex=TICKET_REDIS_TTL)
        except Exception:
            pass  # Redis 不可用不影响主流程，MySQL 已持久化

        return {"order_no": order_no, "qr_code": order.qr_code, "status": "confirmed"}

    async def get_my_orders(self, user_id: int, page: int = 1, size: int = 10) -> tuple[list, int]:
        from sqlalchemy import func as sqlfunc
        count_q = select(sqlfunc.count()).select_from(TicketOrder).where(TicketOrder.user_id == user_id)
        total = (await self.db.execute(count_q)).scalar() or 0

        q = (
            select(TicketOrder)
            .where(TicketOrder.user_id == user_id)
            .order_by(TicketOrder.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def get_order_detail(self, order_no: str, user_id: int) -> TicketOrder:
        result = await self.db.execute(
            select(TicketOrder).where(TicketOrder.order_no == order_no, TicketOrder.user_id == user_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise BizError(40401, "订单不存在")
        return order

    async def cancel_order(self, order_no: str, user_id: int) -> dict:
        order = await self.get_order_detail(order_no, user_id)
        if order.status not in ("pending", "confirmed"):
            raise BizError(40001, f"当前状态({order.status})不可取消")

        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()
        if order.pay_status == "paid":
            order.pay_status = "refunding"
            order.refund_amount = order.pay_amount
        await self.db.commit()

        # 取消订单时删除 Redis 中的票据缓存
        try:
            r = await get_redis()
            await r.delete(f"{TICKET_REDIS_PREFIX}{order_no}")
        except Exception:
            pass

        return {"order_no": order_no, "status": "cancelled"}

    async def check_user_has_active_ticket(self, user_id: int) -> bool:
        """
        检查用户是否有 Redis 中未过期的有效票据。
        查询 MySQL 中已支付的订单，逐一校验 Redis key 是否仍在有效期内。
        """
        # 1. 查 MySQL 获取用户已支付的订单
        result = await self.db.execute(
            select(TicketOrder).where(
                and_(
                    TicketOrder.user_id == user_id,
                    TicketOrder.pay_status == "paid",
                    TicketOrder.status == "confirmed",
                )
            )
        )
        orders = list(result.scalars().all())
        if not orders:
            return False

        # 2. 挨个检查 Redis 中对应 key 是否存活
        try:
            r = await get_redis()
            for order in orders:
                exists = await r.exists(f"{TICKET_REDIS_PREFIX}{order.order_no}")
                if exists:
                    return True
        except Exception:
            # Redis 不可用时，回退到 MySQL 的 visit_date 判断（宽松模式）
            today = date.today()
            for order in orders:
                if order.visit_date >= today:
                    return True

        return False

    async def get_user_active_tickets(self, user_id: int) -> list[dict]:
        """
        获取用户当前有效的票据列表（Redis 中未过期的）。
        返回每个票据的 order_no、visit_date、创建时间。
        """
        result = await self.db.execute(
            select(TicketOrder).where(
                and_(
                    TicketOrder.user_id == user_id,
                    TicketOrder.pay_status == "paid",
                    TicketOrder.status == "confirmed",
                )
            ).order_by(TicketOrder.created_at.desc())
        )
        orders = list(result.scalars().all())
        if not orders:
            return []

        active = []
        try:
            r = await get_redis()
            for order in orders:
                exists = await r.exists(f"{TICKET_REDIS_PREFIX}{order.order_no}")
                if exists:
                    active.append({
                        "order_no": order.order_no,
                        "visit_date": str(order.visit_date),
                        "total_amount": order.total_amount,
                        "pay_amount": order.pay_amount,
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                    })
        except Exception:
            # Redis 不可用时，返回已支付订单
            for order in orders:
                active.append({
                    "order_no": order.order_no,
                    "visit_date": str(order.visit_date),
                    "total_amount": order.total_amount,
                    "pay_amount": order.pay_amount,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                })

        return active
