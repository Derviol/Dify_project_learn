"""社区路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.schemas.common import ok, page
from app.services.misc_service import CommunityService

router = APIRouter()


@router.get("/posts")
async def list_posts(
    type: str = Query(None), p: int = Query(1, alias="page"),
    ps: int = Query(10, alias="page_size"), db: AsyncSession = Depends(get_db),
):
    posts, total = await CommunityService(db).list_posts(post_type=type, page=p, size=ps)
    items = [{
        "id": post.id, "title": post.title, "content": post.content[:200] + "..." if len(post.content or "") > 200 else post.content,
        "post_type": post.post_type, "view_count": post.view_count,
        "like_count": post.like_count, "comment_count": post.comment_count,
        "created_at": post.created_at.isoformat() if post.created_at else None,
    } for post in posts]
    return page(items, total)


@router.post("/posts")
async def create_post(data: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await CommunityService(db).create_post(
        user_id=user.id, title=data.get("title", ""), content=data.get("content", ""),
        post_type=data.get("post_type", "travelogue"), tags=data.get("tags"),
    )
    return ok(result)


@router.post("/posts/{post_id}/like")
async def like_post(post_id: int, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await CommunityService(db).toggle_like(post_id, user.id)
    return ok(result)


@router.post("/posts/{post_id}/comments")
async def add_comment(post_id: int, data: dict, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await CommunityService(db).add_comment(
        post_id=post_id, user_id=user.id, content=data.get("content", ""),
        parent_id=data.get("parent_id"),
    )
    return ok(result)
