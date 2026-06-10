"""WebSocket 流式 AI 对话"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.security import decode_token
from app.services.dify_service import dify_service

router = APIRouter()


@router.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    # 鉴权
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="缺少 token")
        return

    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Token 无效")
        return

    user_id = str(payload["user_id"])
    await websocket.accept()

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            message = data.get("message", "").strip()
            conversation_id = data.get("conversation_id")
            app_type = data.get("app_type", "planner")

            if not message:
                await websocket.send_json({"type": "error", "content": "消息不能为空"})
                continue

            await websocket.send_json({"type": "thinking", "content": "正在分析您的需求..."})

            full_content = ""
            conv_id = conversation_id
            try:
                async for chunk in dify_service.chat_stream(
                    app_type=app_type, query=message,
                    user_id=user_id, conversation_id=conversation_id,
                ):
                    event = chunk.get("event", "")
                    if event == "message":
                        token_text = chunk.get("answer", "")
                        full_content += token_text
                        await websocket.send_json({"type": "token", "content": token_text})
                    elif event == "message_end":
                        conv_id = chunk.get("conversation_id", conv_id)
                    elif event == "error":
                        await websocket.send_json({"type": "error", "content": chunk.get("message", "AI 服务异常")})
            except Exception as e:
                await websocket.send_json({"type": "error", "content": f"调用失败: {str(e)}"})

            await websocket.send_json({
                "type": "done", "conversation_id": conv_id, "full_content": full_content,
            })

    except WebSocketDisconnect:
        pass
