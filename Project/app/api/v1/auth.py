"""认证路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decode_token, create_access_token
from app.schemas.auth import RegisterReq, LoginReq, WechatLoginReq, RefreshReq, ChangePasswordReq
from app.schemas.common import ok, fail
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register")
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await AuthService(db).register(req.phone, req.password, req.nickname)
        return ok(result)
    except Exception as e:
        return fail(40001, str(e))


@router.post("/login")
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    try:
        result = await AuthService(db).login(req.phone, req.password)
        return ok(result)
    except Exception as e:
        return fail(40101, str(e))


@router.post("/wechat/login")
async def wechat_login(req: WechatLoginReq, db: AsyncSession = Depends(get_db)):
    result = await AuthService(db).wechat_login(req.code)
    return ok(result)


@router.put("/password")
async def change_password(req: ChangePasswordReq, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """修改密码"""
    try:
        await AuthService(db).change_password(user.id, req.old_password, req.new_password, req.confirm_password)
        return ok(None, "密码修改成功")
    except Exception as e:
        return fail(40001, str(e))


@router.post("/refresh")
async def refresh_token(req: RefreshReq):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        return fail(40102, "Refresh Token 无效或已过期")
    new_token = create_access_token(payload["user_id"])
    return ok({"access_token": new_token, "expires_in": 7200})
