"""认证服务"""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserProfile
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import BizError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, phone: str, password: str, nickname: str) -> dict:
        existing = await self.db.execute(select(User).where(User.phone == phone))
        if existing.scalar_one_or_none():
            raise BizError(40001, "该手机号已注册")

        user = User(
            phone=phone,
            password_hash=hash_password(password),
            nickname=nickname,
            role="user",
        )
        self.db.add(user)
        await self.db.flush()
        self.db.add(UserProfile(user_id=user.id))
        await self.db.commit()
        await self.db.refresh(user)

        return self._build_token_resp(user)

    async def login(self, phone: str, password: str) -> dict:
        result = await self.db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        if not user or not user.password_hash or not verify_password(password, user.password_hash):
            raise BizError(40101, "手机号或密码错误")
        if user.status != "active":
            raise BizError(40301, "账号已被禁用")

        user.last_login_at = datetime.utcnow()
        await self.db.commit()
        return self._build_token_resp(user)

    async def change_password(self, user_id: int, old_password: str, new_password: str, confirm_password: str) -> None:
        if new_password != confirm_password:
            raise BizError(40002, "两次输入的新密码不一致")
        if new_password == old_password:
            raise BizError(40003, "新密码不能与旧密码相同")

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise BizError(40401, "用户不存在")
        if not user.password_hash or not verify_password(old_password, user.password_hash):
            raise BizError(40101, "旧密码错误")

        user.password_hash = hash_password(new_password)
        await self.db.commit()

    async def wechat_login(self, code: str) -> dict:
        # 学习项目：模拟微信登录，直接用 code 作为 openid
        openid = f"wx_mock_{code}"

        result = await self.db.execute(select(User).where(User.wechat_openid == openid))
        user = result.scalar_one_or_none()
        is_new = False

        if not user:
            user = User(wechat_openid=openid, nickname=f"游客{openid[-6:]}", role="user")
            self.db.add(user)
            await self.db.flush()
            self.db.add(UserProfile(user_id=user.id))
            await self.db.commit()
            await self.db.refresh(user)
            is_new = True

        resp = self._build_token_resp(user)
        resp["is_new_user"] = is_new
        return resp

    def _build_token_resp(self, user: User) -> dict:
        from app.core.config import settings
        return {
            "user_id": user.id,
            "access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id),
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
