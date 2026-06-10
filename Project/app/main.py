"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router
from app.api.ws.chat_ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"🎠 {settings.APP_NAME} 启动中...")
    # 连接 Redis
    try:
        from app.core.redis import get_redis, close_redis
        r = await get_redis()
        print(f"   Redis: 已连接 ({settings.REDIS_URL})")
    except Exception as e:
        print(f"   Redis: 连接失败 ({e})，排队功能将不可用")
        close_redis = None

    print(f"   API 文档: http://localhost:8000/docs")
    print(f"   前端页面: http://localhost:8000/")
    yield

    if close_redis:
        await close_redis()
    print(f"🎠 {settings.APP_NAME} 已停止")


app = FastAPI(
    title=settings.APP_NAME,
    description="乐乐亲子乐园智能服务系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")

# 注册异常处理
register_exception_handlers(app)

# 静态文件：挂载 web/ 目录，让 /web/index.html 可访问
web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
if os.path.isdir(web_dir):
    app.mount("/web", StaticFiles(directory=web_dir, html=True), name="web")


@app.get("/")
async def root():
    """根路径重定向到前端页面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/web/index.html")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
