"""排期 / 设施 / 天气 / 用户 服务"""
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.misc import Schedule, Member, PointRecord, CommunityPost, PostReview
from app.models.project import Facility
from app.models.user import User, UserProfile
from app.models.ticket import TicketOrder
from app.core.exceptions import BizError


class ScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_schedules(self, event_date: str = None, event_type: str = None) -> list[Schedule]:
        q = select(Schedule)
        if event_date:
            q = q.where(Schedule.event_date == date.fromisoformat(event_date))
        else:
            q = q.where(Schedule.event_date >= date.today())
        if event_type:
            q = q.where(Schedule.event_type == event_type)
        q = q.order_by(Schedule.event_date, Schedule.start_time)
        result = await self.db.execute(q)
        return list(result.scalars().all())


class FacilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_facilities(self, facility_type: str = None, zone: str = None) -> list[Facility]:
        q = select(Facility)
        if facility_type:
            q = q.where(Facility.type == facility_type)
        if zone:
            q = q.where(Facility.zone == zone)
        result = await self.db.execute(q)
        return list(result.scalars().all())


class WeatherService:
    """天气服务（学习项目使用模拟数据）"""

    async def get_weather(self) -> dict:
        now = datetime.now()
        return {
            "temperature": 28,
            "humidity": 65,
            "weather": "多云",
            "wind_level": 2,
            "uv_index": 5,
            "aqi": 45,
            "suggestion": "天气晴好，适合户外游玩，建议涂抹防晒霜，多补充水分。",
            "updated_at": now.isoformat(),
        }


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_info(self, user_id: int) -> dict:
        user = await self.db.get(User, user_id)
        if not user:
            raise BizError(40401, "用户不存在")

        # 获取画像
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()

        # 获取会员
        result2 = await self.db.execute(select(Member).where(Member.user_id == user_id))
        member = result2.scalar_one_or_none()

        return {
            "id": user.id,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "phone": f"{user.phone[:3]}****{user.phone[-4:]}" if user.phone else None,
            "profile": {
                "child_age": profile.child_age if profile else None,
                "interests": profile.interests if profile else [],
                "visit_count": profile.visit_count if profile else 0,
            } if profile else None,
            "member": {
                "level": member.level if member else 0,
                "points": member.points if member else 0,
                "balance": member.balance if member else 0,
            } if member else None,
            "tickets": await self._get_user_tickets(user_id),
        }

    async def update_profile(self, user_id: int, data: dict) -> None:
        result = await self.db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if not profile:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)

        for k, v in data.items():
            if hasattr(profile, k) and v is not None:
                setattr(profile, k, v)
        await self.db.commit()

    async def update_user_basic(self, user_id: int, data: dict) -> None:
        """更新用户基本信息（昵称、头像）"""
        user = await self.db.get(User, user_id)
        if not user:
            raise BizError(40401, "用户不存在")

        if "nickname" in data and data["nickname"]:
            user.nickname = data["nickname"]
        if "avatar_url" in data:
            user.avatar_url = data["avatar_url"]

        await self.db.commit()

    async def _get_user_tickets(self, user_id: int) -> list[dict]:
        """获取用户票据列表（含 Redis 活跃状态）"""
        result = await self.db.execute(
            select(TicketOrder)
            .where(TicketOrder.user_id == user_id)
            .order_by(desc(TicketOrder.created_at))
            .limit(20)
        )
        orders = list(result.scalars().all())
        if not orders:
            return []

        # 检查 Redis 中哪些票据仍有效
        ticket_list = []
        try:
            from app.core.redis import get_redis
            r = await get_redis()
            for o in orders:
                active = await r.exists(f"ticket:active:{o.order_no}")
                ticket_list.append({
                    "order_no": o.order_no,
                    "visit_date": str(o.visit_date),
                    "total_amount": o.total_amount,
                    "pay_amount": o.pay_amount,
                    "discount_amount": o.discount_amount,
                    "status": o.status,
                    "pay_status": o.pay_status,
                    "qr_code": o.qr_code,
                    "active": bool(active),
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                })
        except Exception:
            # Redis 不可用时，仅返回 MySQL 数据
            for o in orders:
                ticket_list.append({
                    "order_no": o.order_no,
                    "visit_date": str(o.visit_date),
                    "total_amount": o.total_amount,
                    "pay_amount": o.pay_amount,
                    "discount_amount": o.discount_amount,
                    "status": o.status,
                    "pay_status": o.pay_status,
                    "qr_code": o.qr_code,
                    "active": o.pay_status == "paid" and o.status == "confirmed",
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                })

        return ticket_list


class MemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_member_info(self, user_id: int) -> dict:
        result = await self.db.execute(select(Member).where(Member.user_id == user_id))
        member = result.scalar_one_or_none()
        if not member:
            # 自动创建会员
            import uuid
            member = Member(
                user_id=user_id,
                member_no=f"M{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}",
                level=1, points=100, total_points=100,
            )
            self.db.add(member)
            await self.db.commit()
            await self.db.refresh(member)

        level_names = {1: "普通会员", 2: "银卡会员", 3: "金卡会员", 4: "钻石会员"}
        return {
            "member_no": member.member_no,
            "level": member.level,
            "level_name": level_names.get(member.level, "普通会员"),
            "points": member.points,
            "total_points": member.total_points,
            "balance": member.balance,
            "card_type": member.card_type,
            "join_date": str(member.join_date) if member.join_date else None,
        }

    async def checkin(self, user_id: int) -> dict:
        result = await self.db.execute(select(Member).where(Member.user_id == user_id))
        member = result.scalar_one_or_none()
        if not member:
            raise BizError(40401, "请先注册会员")

        member.points += 5
        member.total_points += 5
        self.db.add(PointRecord(
            user_id=user_id, member_id=member.id,
            points=5, balance_after=member.points,
            type="earn_checkin", description="每日签到",
        ))
        await self.db.commit()
        return {"points_earned": 5, "total_points": member.points}


class CommunityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_posts(self, post_type: str = None, page: int = 1, size: int = 10) -> tuple[list, int]:
        from sqlalchemy import func as sqlfunc
        q = select(CommunityPost).where(CommunityPost.status == "published")
        if post_type:
            q = q.where(CommunityPost.post_type == post_type)

        count_q = select(sqlfunc.count()).select_from(CommunityPost).where(CommunityPost.status == "published")
        if post_type:
            count_q = count_q.where(CommunityPost.post_type == post_type)
        total = (await self.db.execute(count_q)).scalar() or 0

        q = q.order_by(CommunityPost.created_at.desc()).offset((page - 1) * size).limit(size)
        result = await self.db.execute(q)
        return list(result.scalars().all()), total

    async def create_post(self, user_id: int, title: str, content: str, post_type: str = "travelogue", tags: list = None) -> dict:
        post = CommunityPost(
            user_id=user_id, title=title, content=content,
            post_type=post_type, tags=tags, status="published",
        )
        self.db.add(post)
        await self.db.commit()
        await self.db.refresh(post)
        return {"id": post.id, "message": "发布成功"}

    async def toggle_like(self, post_id: int, user_id: int) -> dict:
        post = await self.db.get(CommunityPost, post_id)
        if not post:
            raise BizError(40401, "帖子不存在")
        post.like_count = (post.like_count or 0) + 1
        await self.db.commit()
        return {"liked": True, "like_count": post.like_count}

    async def add_comment(self, post_id: int, user_id: int, content: str, parent_id: int = None) -> dict:
        post = await self.db.get(CommunityPost, post_id)
        if not post:
            raise BizError(40401, "帖子不存在")
        review = PostReview(post_id=post_id, user_id=user_id, content=content, parent_id=parent_id)
        self.db.add(review)
        post.comment_count = (post.comment_count or 0) + 1
        await self.db.commit()
        await self.db.refresh(review)
        return {"id": review.id, "message": "评论成功"}
