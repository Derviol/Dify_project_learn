"""天气路由"""
from fastapi import APIRouter
from app.schemas.common import ok
from app.services.misc_service import WeatherService

router = APIRouter()


@router.get("")
async def get_weather():
    weather = await WeatherService().get_weather()
    return ok(weather)
