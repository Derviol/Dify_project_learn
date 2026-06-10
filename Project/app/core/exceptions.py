"""全局异常处理"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
from loguru import logger


class BizError(Exception):
    """业务异常"""
    def __init__(self, code: int = 40001, message: str = "业务错误"):
        self.code = code
        self.message = message


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(BizError)
    async def biz_error_handler(request: Request, exc: BizError):
        return JSONResponse(
            status_code=200,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        msg = "; ".join([f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()])
        return JSONResponse(
            status_code=200,
            content={"code": 40001, "message": f"参数错误: {msg}", "data": None},
        )

    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        logger.error(f"未处理异常: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"code": 50001, "message": "服务器内部错误", "data": None},
        )
