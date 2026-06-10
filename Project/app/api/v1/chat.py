"""AI 对话路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.common import ok
from app.schemas.chat import ChatMessageReq
from app.services.dify_service import dify_service

router = APIRouter()

# 意图关键词分类
INTENT_KEYWORDS = {
    "recommend": ["推荐", "玩什么", "适合", "有什么项目", "能玩"],
    "route_plan": ["路线", "规划", "一日游", "怎么安排", "行程"],
    "event": ["表演", "演出", "活动", "今天有什么", "花车", "魔术"],
    "queue": ["排队", "等多久", "要排", "多久"],
    "facility": ["母婴室", "厕所", "卫生间", "餐厅", "充电", "储物"],
    "safety": ["安全", "身高", "限制", "能玩吗", "天气", "下雨"],
    "ticket": ["票价", "买票", "多少钱", "门票", "订单"],
    "greeting": ["你好", "谢谢", "再见", "你是谁", "你好呀"],
}

INTENT_TO_AGENT = {
    "recommend": "planner", "route_plan": "planner", "event": "planner",
    "queue": "guide", "facility": "guide", "safety": "guide",
    "ticket": "ticket", "greeting": "self", "unknown": "self",
}

# 会话 → Agent 映射（保持多轮对话的 Agent 一致性）
_conv_agent: dict[str, str] = {}


def classify_intent(message: str) -> str:
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in message:
                return intent
    return "unknown"


@router.post("/message")
async def chat_message(req: ChatMessageReq, user=Depends(get_current_user)):
    # 清理 conversation_id
    conv_id = req.conversation_id if req.conversation_id and req.conversation_id not in ("null", "None", "") else None

    intent = classify_intent(req.message)

    # 核心逻辑：有会话上下文时，继续用同一个 Agent
    if conv_id and conv_id in _conv_agent:
        agent = _conv_agent[conv_id]
        logger.info(f"[Chat] 多轮对话 conv_id={conv_id}, 复用 Agent={agent}, 消息={req.message[:30]}")
    elif intent != "unknown":
        agent = INTENT_TO_AGENT.get(intent, "self")
        logger.info(f"[Chat] 新对话 意图={intent}, Agent={agent}, 消息={req.message[:30]}")
    else:
        # 无法识别意图且无上下文 → 智能兜底：用 Dify planner 处理
        agent = "planner"
        logger.info(f"[Chat] 未知意图，fallback 到 planner, 消息={req.message[:30]}")

    # 问候类直接回复（仅在无会话上下文时）
    if agent == "self" and not conv_id:
        greeting_map = {
            "你好": "你好呀！欢迎来到乐乐亲子乐园！🎉 我是智能助手乐乐，可以帮你推荐项目、规划路线、查询排队时间等，有什么需要帮忙的？",
            "谢谢": "不客气！还有什么我能帮你的吗？😊",
            "再见": "再见！祝你在乐乐乐园玩得开心！🎠",
        }
        for kw, resp in greeting_map.items():
            if kw in req.message:
                return ok({"conversation_id": None, "answer": resp, "intent": "greeting", "agent": "self", "suggested_questions": ["3岁宝宝能玩什么", "帮我规划路线", "旋转木马排多久"]})
        # 兜底：交给 Dify
        agent = "planner"

    # 构建上下文
    context_str = ""
    if req.user_context:
        ctx = req.user_context
        context_str = f"用户信息：孩子年龄={ctx.get('child_age', '未知')}，兴趣={','.join(ctx.get('interests', []))}"

    full_query = f"{context_str}\n用户问题：{req.message}" if context_str else req.message

    # 调用 Dify
    result = await dify_service.chat(
        app_type=agent, query=full_query, user_id=str(user.id),
        conversation_id=conv_id,
    )

    answer = result.get("answer", "")
    new_conv_id = result.get("conversation_id", conv_id)
    error = result.get("error", "")

    if error:
        logger.warning(f"[Chat] Dify 错误: {error}")

    # 记录会话使用的 Agent（保持多轮一致）
    if new_conv_id:
        _conv_agent[new_conv_id] = agent

    suggested = {
        "recommend": ["帮我规划路线", "旋转木马排多久", "今天有什么表演"],
        "route_plan": ["3岁能玩什么", "母婴室在哪", "今天有什么表演"],
        "queue": ["推荐适合3岁的项目", "还有哪些项目排队短", "母婴室在哪"],
        "facility": ["推荐适合3岁的项目", "旋转木马排多久", "今天有什么表演"],
        "safety": ["推荐适合3岁的项目", "旋转木马排多久", "下雨天能玩什么"],
        "ticket": ["怎么买票", "有什么优惠", "订单查询"],
    }

    return ok({
        "conversation_id": new_conv_id,
        "answer": answer or "抱歉，暂时无法回答，请稍后再试。",
        "intent": intent,
        "agent": f"lele-{agent}" if agent != "self" else "self",
        "suggested_questions": suggested.get(intent, suggested["recommend"]),
    })
