"""项目路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.common import ok
from app.services.project_service import ProjectService
from app.services.queue_service import QueueService

router = APIRouter()


@router.get("")
async def list_projects(
    zone: str = Query(None), category: str = Query(None),
    suitable_age: str = Query(None), status: str = Query("open"),
    db: AsyncSession = Depends(get_db),
):
    svc = ProjectService(db)
    projects = await svc.list_projects(zone=zone, category=category, suitable_age=suitable_age, status=status)
    items = []
    for p in projects:
        item = {
            "id": p.id, "project_code": p.project_code, "name": p.name,
            "zone": p.zone, "category": p.category, "suitable_age": p.suitable_age,
            "min_height": p.min_height, "intensity": p.intensity,
            "is_indoor": p.is_indoor, "stroller_friendly": p.stroller_friendly,
            "duration_minutes": p.duration_minutes, "cover_image": p.cover_image,
            "status": p.status,
        }
        # 附加排队信息
        if p.queue_enabled:
            try:
                qi = await QueueService(db).get_queue_info(p.id)
                item["queue_info"] = {"queue_time": qi["estimated_wait"], "crowd_level": qi["crowd_level"]}
            except Exception:
                item["queue_info"] = None
        items.append(item)
    return ok({"total": len(items), "items": items})


@router.get("/recommend")
async def recommend_projects(
    age: str = Query(None), interests: str = Query(None),
    indoor: bool = Query(None), db: AsyncSession = Depends(get_db),
):
    projects = await ProjectService(db).recommend(age=age, interests=interests, indoor=indoor)
    items = []
    for p in projects[:10]:
        items.append({
            "project": {
                "id": p.id, "name": p.name, "zone": p.zone,
                "suitable_age": p.suitable_age, "duration_minutes": p.duration_minutes,
                "cover_image": p.cover_image, "status": p.status,
            },
            "match_score": 90,
            "match_reasons": [f"适合{p.suitable_age}"] + (["室内项目"] if p.is_indoor else []),
            "safety_tips": p.safety_notes,
        })
    return ok({"recommendations": items})


@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    p = await ProjectService(db).get_project(project_id)
    if not p:
        return fail(40401, "项目不存在")
    queue_info = None
    if p.queue_enabled:
        try:
            qi = await QueueService(db).get_queue_info(p.id)
            queue_info = {"queue_time": qi["estimated_wait"], "crowd_level": qi["crowd_level"], "current_number": qi["current_number"]}
        except Exception:
            pass
    return ok({
        "id": p.id, "project_code": p.project_code, "name": p.name,
        "zone": p.zone, "category": p.category, "description": p.description,
        "suitable_age": p.suitable_age, "min_height": p.min_height,
        "intensity": p.intensity, "is_indoor": p.is_indoor, "has_ac": p.has_ac,
        "stroller_friendly": p.stroller_friendly, "duration_minutes": p.duration_minutes,
        "capacity": p.capacity, "fast_pass": p.fast_pass, "fast_pass_price": p.fast_pass_price,
        "queue_enabled": p.queue_enabled, "location_desc": p.location_desc,
        "tips": p.tips, "safety_notes": p.safety_notes, "status": p.status,
        "queue_info": queue_info,
    })
