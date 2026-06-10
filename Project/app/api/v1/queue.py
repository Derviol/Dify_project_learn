"""排队路由（Redis 版）"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ok, fail
from app.schemas.queue import TakeNumberReq
from app.services.queue_service import QueueService

router = APIRouter()


@router.post("/take")
async def take_number(req: TakeNumberReq, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await QueueService(db).take_number(req.project_id, user.id)
        return ok(result)
    except Exception as e:
        logger.error(f"排队取号异常: {e}")
        if "已在排队" in str(e):
            return fail(40001, str(e))
        return fail(50001, f"取号失败: {str(e)}")


@router.get("/my")
async def my_queues(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        queues = await QueueService(db).get_my_queues(user.id)
        return ok(queues)
    except Exception as e:
        logger.error(f"查询排队异常: {e}")
        return ok([])


@router.get("/{project_id}")
async def get_queue(project_id: int, db: AsyncSession = Depends(get_db)):
    try:
        info = await QueueService(db).get_queue_info(project_id)
        return ok(info)
    except Exception as e:
        logger.error(f"查询排队状态异常: {e}")
        return fail(50001, "查询失败")


@router.delete("/{project_id}/cancel")
async def cancel_queue(project_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        result = await QueueService(db).cancel_queue(project_id, user.id)
        return ok(result)
    except Exception as e:
        logger.error(f"取消排队异常: {e}")
        return fail(50001, f"取消失败: {str(e)}")


@router.post("/{project_id}/call-next")
async def call_next(project_id: int, db: AsyncSession = Depends(get_db)):
    """叫号（运营端）"""
    try:
        result = await QueueService(db).call_next(project_id)
        if result:
            return ok(result)
        return ok({"message": "没有等待的用户"})
    except Exception as e:
        logger.error(f"叫号异常: {e}")
        return fail(50001, "叫号失败")
