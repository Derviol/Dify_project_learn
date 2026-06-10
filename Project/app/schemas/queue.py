"""排队 Schema"""
from pydantic import BaseModel
from typing import Optional


class TakeNumberReq(BaseModel):
    project_id: int


class QueueInfoResp(BaseModel):
    project_id: int
    queue_number: int
    current_number: int
    ahead_count: int
    estimated_wait: int
    project_name: Optional[str] = None
    crowd_level: str = "适中"
    status: str = "waiting"
