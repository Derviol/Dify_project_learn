"""排队服务（Redis 存储，自动过期）"""
from datetime import date
from loguru import logger
from app.core.exceptions import BizError
from app.core.redis import get_redis

# Redis Key 设计：
# queue:{pid}:{date}:counter      → 自增计数器（当日排队号码）
# queue:{pid}:{date}:current      → 当前叫号
# queue:{pid}:{date}:user:{uid}   → 用户的排队号码
# queue:{pid}:{date}:num:{num}    → 号码对应的用户ID
# 所有 Key TTL = 12 小时（自动清理）

TTL_SECONDS = 12 * 3600  # 12 小时


def _today() -> str:
    return date.today().isoformat()


def _key_counter(pid: int) -> str:
    return f"queue:{pid}:{_today()}:counter"

def _key_current(pid: int) -> str:
    return f"queue:{pid}:{_today()}:current"

def _key_user(pid: int, uid: int) -> str:
    return f"queue:{pid}:{_today()}:user:{uid}"

def _key_num(pid: int, num: int) -> str:
    return f"queue:{pid}:{_today()}:num:{num}"

def _key_cancelled(pid: int) -> str:
    return f"queue:{pid}:{_today()}:cancelled"


# 项目名缓存
_project_names: dict[int, str] = {}


class QueueService:
    def __init__(self, db=None):
        self.db = db  # 仅用于查询项目名，不用于排队数据

    async def _get_project_name(self, pid: int) -> str:
        if pid in _project_names:
            return _project_names[pid]
        if self.db:
            try:
                from app.models.project import Project
                proj = await self.db.get(Project, pid)
                if proj:
                    _project_names[pid] = proj.name
                    return proj.name
            except Exception:
                pass
        return f"项目{pid}"

    async def _get_cancelled_count(self, r, pid: int) -> int:
        """获取已取消的排队人数"""
        return await r.scard(_key_cancelled(pid)) or 0

    async def get_queue_info(self, project_id: int) -> dict:
        r = await get_redis()

        counter = await r.get(_key_counter(project_id))
        current = await r.get(_key_current(project_id))
        counter = int(counter) if counter else 0
        current = int(current) if current else 0
        cancelled = await self._get_cancelled_count(r, project_id)
        length = max(0, counter - current - cancelled)

        if length <= 5:
            crowd = "空闲"
        elif length <= 15:
            crowd = "适中"
        elif length <= 30:
            crowd = "拥挤"
        else:
            crowd = "非常拥挤"

        pname = await self._get_project_name(project_id)

        return {
            "project_id": project_id,
            "project_name": pname,
            "queue_length": length,
            "estimated_wait": length * 3,
            "current_number": current,
            "crowd_level": crowd,
        }

    async def take_number(self, project_id: int, user_id: int) -> dict:
        r = await get_redis()

        # 检查是否已取号
        existing = await r.get(_key_user(project_id, user_id))
        if existing:
            raise BizError(40001, "您已在排队中")

        # 检查用户是否有有效票据（Redis 中未过期的票）
        if self.db:
            from app.services.ticket_service import TicketService
            has_ticket = await TicketService(self.db).check_user_has_active_ticket(user_id)
            if not has_ticket:
                raise BizError(40001, "您没有有效票据，请先购票")

        # 自增计数器
        number = await r.incr(_key_counter(project_id))
        if number == 1:
            await r.set(_key_current(project_id), 0, ex=TTL_SECONDS)

        current = int(await r.get(_key_current(project_id)) or 0)
        # 计算前方人数时排除已取消的号码
        cancelled_set = await r.smembers(_key_cancelled(project_id)) or set()
        ahead = max(0, number - current - sum(1 for c in cancelled_set if current < int(c) <= number))
        pname = await self._get_project_name(project_id)

        # 根据排队人数动态计算 TTL（预计等待时间 + 30分钟缓冲）
        minutes_per_person = 3
        wait_minutes = ahead * minutes_per_person
        dynamic_ttl = max((wait_minutes + 30) * 60, 30 * 60)  # 最少30分钟，最长按等待时间+30分钟

        # 记录：用户→号码，号码→用户（TTL = 预计等待时间 + 30分钟）
        pipe = r.pipeline()
        pipe.set(_key_user(project_id, user_id), number, ex=dynamic_ttl)
        pipe.set(_key_num(project_id, number), user_id, ex=dynamic_ttl)
        pipe.expire(_key_counter(project_id), TTL_SECONDS)
        await pipe.execute()

        # 异步保存到数据库（不影响返回）
        if self.db:
            try:
                from app.models.misc import QueueRecord
                record = QueueRecord(
                    user_id=user_id, project_id=project_id,
                    queue_number=number, queue_date=date.today(), status="waiting",
                )
                self.db.add(record)
                await self.db.commit()
            except Exception as e:
                logger.warning(f"排队记录入库失败（Redis已保存）: {e}")
                try:
                    await self.db.rollback()
                except Exception:
                    pass

        return {
            "queue_number": number,
            "current_number": current,
            "ahead_count": ahead,
            "estimated_wait": ahead * 3,
            "project_name": pname,
        }

    async def get_my_queues(self, user_id: int) -> list[dict]:
        r = await get_redis()
        result = []

        # 扫描所有 queue:*:user:{user_id} 的 key
        pattern = f"queue:*:{_today()}:user:{user_id}"
        async for key in r.scan_iter(match=pattern, count=50):
            parts = key.split(":")
            try:
                pid = int(parts[1])
                num = int(await r.get(key))
                current = int(await r.get(_key_current(pid)) or 0)
                cancelled_set = await r.smembers(_key_cancelled(pid)) or set()
                ahead = max(0, num - current - sum(1 for c in cancelled_set if current < int(c) <= num))
                pname = await self._get_project_name(pid)
                result.append({
                    "project_id": pid,
                    "project_name": pname,
                    "my_number": num,
                    "current_number": current,
                    "ahead_count": ahead,
                    "estimated_wait": ahead * 3,
                    "crowd_level": "适中",
                    "status": "waiting",
                })
            except (ValueError, IndexError):
                continue

        return result

    async def cancel_queue(self, project_id: int, user_id: int) -> dict:
        r = await get_redis()

        num = await r.get(_key_user(project_id, user_id))
        if not num:
            raise BizError(40401, "未找到排队记录")

        num = int(num)

        # 删除 Redis 中的记录，并记录到已取消集合
        pipe = r.pipeline()
        pipe.delete(_key_user(project_id, user_id))
        pipe.delete(_key_num(project_id, num))
        pipe.sadd(_key_cancelled(project_id), num)
        pipe.expire(_key_cancelled(project_id), TTL_SECONDS)
        await pipe.execute()

        return {"queue_number": num, "message": "排队已取消"}

    async def call_next(self, project_id: int) -> dict | None:
        """叫号（运营端使用）— 自动跳过已取消的号码"""
        r = await get_redis()
        current = int(await r.get(_key_current(project_id)) or 0)
        counter = int(await r.get(_key_counter(project_id)) or 0)

        if current >= counter:
            return None  # 没有等待的人了

        cancelled_set = await r.smembers(_key_cancelled(project_id)) or set()
        cancelled_ints = {int(c) for c in cancelled_set}

        # 跳过已取消的号码
        next_num = current + 1
        while next_num in cancelled_ints and next_num < counter:
            next_num += 1

        if next_num > counter:
            return None  # 后面全是已取消的

        await r.set(_key_current(project_id), next_num, ex=TTL_SECONDS)

        uid = await r.get(_key_num(project_id, next_num))
        return {"queue_number": next_num, "user_id": uid}
