"""用户路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ok, fail
from app.services.misc_service import UserService

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    info = await UserService(db).get_user_info(user.id)
    return ok(info)


@router.put("/me")
async def update_me(data: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新用户基本信息（昵称、头像）"""
    try:
        await UserService(db).update_user_basic(user.id, data)
        info = await UserService(db).get_user_info(user.id)
        return ok(info)
    except Exception as e:
        logger.error(f"更新用户信息失败: {e}")
        return fail(50001, "更新失败")


@router.put("/me/profile")
async def update_profile(data: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """更新用户画像（孩子年龄、兴趣等）"""
    try:
        await UserService(db).update_profile(user.id, data)
        info = await UserService(db).get_user_info(user.id)
        return ok(info)
    except Exception as e:
        logger.error(f"更新画像失败: {e}")
        return fail(50001, "更新失败")
