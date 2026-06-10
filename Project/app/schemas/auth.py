"""认证相关 Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class RegisterReq(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    password: str = Field(..., min_length=6, max_length=32)
    nickname: str = Field(default="游客", max_length=50)


class LoginReq(BaseModel):
    phone: str
    password: str


class WechatLoginReq(BaseModel):
    code: str


class ChangePasswordReq(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=32)
    new_password: str = Field(..., min_length=6, max_length=32)
    confirm_password: str = Field(..., min_length=6, max_length=32)


class RefreshReq(BaseModel):
    refresh_token: str


class TokenResp(BaseModel):
    user_id: int
    access_token: str
    refresh_token: str
    expires_in: int
