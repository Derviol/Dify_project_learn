"""会员路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ok
from app.services.misc_service import MemberService

router = APIRouter()


@router.get("/info")
async def member_info(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    info = await MemberService(db).get_member_info(user.id)
    return ok(info)


@router.post("/checkin")
async def checkin(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await MemberService(db).checkin(user.id)
    return ok(result)
