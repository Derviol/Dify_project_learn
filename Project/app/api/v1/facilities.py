"""设施路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.common import ok
from app.services.misc_service import FacilityService

router = APIRouter()


@router.get("")
async def list_facilities(
    type: str = Query(None), zone: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    facilities = await FacilityService(db).list_facilities(facility_type=type, zone=zone)
    items = [{
        "id": f.id, "name": f.name, "type": f.type, "zone": f.zone,
        "location_desc": f.location_desc, "open_time": f.open_time,
        "close_time": f.close_time, "features": f.features,
        "price_info": f.price_info, "status": f.status,
    } for f in facilities]
    return ok(items)
