"""通用响应模型"""
from pydantic import BaseModel
from typing import Any, Optional


class Resp(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None


class PageResp(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict = {}


def ok(data=None, message="success"):
    return {"code": 200, "message": message, "data": data}


def fail(code=40001, message="错误"):
    return {"code": code, "message": message, "data": None}


def page(items: list, total: int):
    return {"code": 200, "message": "success", "data": {"items": items, "total": total}}
