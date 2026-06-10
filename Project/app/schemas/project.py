"""项目相关 Schema"""
from pydantic import BaseModel
from typing import Optional


class ProjectBrief(BaseModel):
    id: int
    project_code: str
    name: str
    zone: str
    category: str
    suitable_age: Optional[str] = None
    min_height: Optional[float] = None
    intensity: str = "low"
    is_indoor: bool = False
    stroller_friendly: bool = True
    duration_minutes: Optional[int] = None
    cover_image: Optional[str] = None
    status: str = "open"
    queue_info: Optional[dict] = None

    class Config:
        from_attributes = True


class ProjectDetail(ProjectBrief):
    description: Optional[str] = None
    has_ac: bool = False
    capacity: Optional[int] = None
    fast_pass: bool = False
    fast_pass_price: Optional[float] = None
    queue_enabled: bool = True
    location_desc: Optional[str] = None
    tips: Optional[str] = None
    safety_notes: Optional[str] = None


class RecommendReq(BaseModel):
    age: Optional[str] = None
    interests: Optional[str] = None
    indoor: Optional[bool] = None
