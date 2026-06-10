"""API 路由聚合"""
from fastapi import APIRouter
from app.api.v1 import auth, users, projects, tickets, chat, queue, schedules, facilities, member, community, weather

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["票务"])
api_router.include_router(chat.router, prefix="/chat", tags=["AI对话"])
api_router.include_router(queue.router, prefix="/queue", tags=["排队"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["排期"])
api_router.include_router(facilities.router, prefix="/facilities", tags=["设施"])
api_router.include_router(member.router, prefix="/member", tags=["会员"])
api_router.include_router(community.router, prefix="/community", tags=["社区"])
api_router.include_router(weather.router, prefix="/weather", tags=["天气"])
