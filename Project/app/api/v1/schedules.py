"""排期路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.common import ok
from app.services.misc_service import ScheduleService

router = APIRouter()


@router.get("")
async def list_schedules(
    date: str = Query(None, alias="date"), type: str = Query(None, alias="type"),
    db: AsyncSession = Depends(get_db),
):
    schedules = await ScheduleService(db).list_schedules(event_date=date, event_type=type)
    items = [{
        "id": s.id, "event_name": s.event_name, "event_type": s.event_type,
        "start_time": s.start_time, "end_time": s.end_time,
        "location": s.location, "capacity": s.capacity,
        "enrolled_count": s.enrolled_count, "theme": s.theme,
        "status": s.status,
    } for s in schedules]
    return ok(items)
