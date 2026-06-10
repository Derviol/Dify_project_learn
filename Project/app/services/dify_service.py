"""Dify API 调用封装"""
import json
import re
import httpx
from app.core.config import settings
from loguru import logger


def clean_answer(text: str) -> str:
    """清洗 Dify 回复中的乱码、思考过程、工具调用标记"""
    if not text:
        return text

    # 移除 DeepSeek 工具调用标记
    text = re.sub(r'<｜｜DSML｜｜[^>]*>.*?(?=<｜｜DSML｜｜|$)', '', text, flags=re.DOTALL)
    text = re.sub(r'<\｜\｜DSML\｜\｜[^>]*>', '', text)

    # 移除工具调用标签
    text = re.sub(r'<tool_call>.*?</tool_call>', '', text, flags=re.DOTALL)

    # 移除思考过程
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)

    # 移除 DeepSeek 特殊 token
    text = re.sub(r'<｜[^｜]*｜>', '', text)

    # 移除开头的自言自语
    thinking_patterns = [
        r'^.*?用户想要.*?[\n。]',
        r'^.*?我需要先获取.*?[\n。]',
        r'^.*?让我先.*?[\n。]',
        r'^.*?让我看看.*?[\n。]',
        r'^.*?工具调用失败.*?[\n。]',
        r'^.*?别急.*?[～~。]',
        r'^.*?让我尝试.*?[\n。]',
        r'^.*?换个方式.*?[～~。]',
        r'^.*?好的，让我.*?[\n。]',
    ]
    for pattern in thinking_patterns:
        text = re.sub(pattern, '', text, count=1)

    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class DifyService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)
        self.app_keys = {
            "planner": settings.DIFY_APP_KEY_PLANNER,
            "guide": settings.DIFY_APP_KEY_GUIDE,
            "ticket": settings.DIFY_APP_KEY_TICKET,
        }

    async def chat(
        self, app_type: str, query: str, user_id: str,
        conversation_id: str = None, inputs: dict = None,
    ) -> dict:
        """调用 Dify（带自动重试）"""
        app_key = self.app_keys.get(app_type, settings.DIFY_APP_KEY_PLANNER)
        if not app_key:
            return self._mock_response(app_type, query)

        last_result = {}
        for attempt in range(2):
            result = await self._do_chat(app_key, app_type, query, user_id, conversation_id, inputs)
            answer = result.get("answer", "")
            error = result.get("error", "")
            last_result = result

            if answer and not error:
                return result
            if error and "401" in str(error):
                return result
            if attempt == 0:
                logger.warning(f"[Dify] 第1次无结果，重试... error={error}, answer_len={len(answer)}")

        return last_result

    async def _do_chat(
        self, app_key: str, app_type: str, query: str, user_id: str,
        conversation_id: str = None, inputs: dict = None,
    ) -> dict:
        """单次调用 Dify Chat API"""
        url = f"{settings.DIFY_API_BASE}/chat-messages"
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id and conversation_id not in ("null", "None", ""):
            payload["conversation_id"] = conversation_id

        headers = {"Authorization": f"Bearer {app_key}", "Content-Type": "application/json"}

        logger.info(f"[Dify] 调用 {app_type}: query={query[:60]}")

        try:
            async with self.client.stream("POST", url, json=payload, headers=headers, timeout=120.0) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")
                    logger.error(f"[Dify] API 错误: {resp.status_code} - {body[:300]}")
                    return {"answer": "", "conversation_id": conversation_id, "error": f"Dify {resp.status_code}"}

                answer = ""
                conv_id = conversation_id
                buffer = ""

                async for line in resp.aiter_lines():
                    buffer += line + "\n"
                    while "\n\n" in buffer:
                        chunk_text, buffer = buffer.split("\n\n", 1)
                        event_type = ""
                        data_str = ""
                        for l in chunk_text.split("\n"):
                            if l.startswith("event:"):
                                event_type = l[6:].strip()
                            elif l.startswith("data:"):
                                data_str = l[5:].strip()

                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        etype = event_type or data.get("event", "")

                        if etype in ("message", "agent_message"):
                            answer += data.get("answer", "")
                        elif etype == "agent_thought":
                            pass
                        elif etype == "message_end":
                            conv_id = data.get("conversation_id", conv_id)
                        elif etype == "error":
                            return {"answer": answer or "", "conversation_id": conv_id, "error": data.get("message", "未知错误")}

                logger.info(f"[Dify] 回复长度={len(answer)}, conv_id={conv_id}")
                return {"answer": clean_answer(answer), "conversation_id": conv_id}

        except httpx.ConnectError as e:
            logger.error(f"[Dify] 连接失败: {e}")
            return {"answer": "", "error": f"无法连接 Dify"}
        except httpx.TimeoutException:
            logger.error(f"[Dify] 超时")
            return {"answer": "", "error": "Dify 请求超时"}
        except Exception as e:
            logger.error(f"[Dify] 异常: {e}")
            return {"answer": "", "error": str(e)}

    async def chat_stream(
        self, app_type: str, query: str, user_id: str,
        conversation_id: str = None, inputs: dict = None,
    ):
        """流式调用 Dify，逐个 yield SSE event dict（供 WebSocket 使用）"""
        app_key = self.app_keys.get(app_type, settings.DIFY_APP_KEY_PLANNER)
        if not app_key:
            yield {"event": "message", "answer": self._mock_response(app_type, query).get("answer", "")}
            yield {"event": "message_end", "conversation_id": "mock_001"}
            return

        url = f"{settings.DIFY_API_BASE}/chat-messages"
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id and conversation_id not in ("null", "None", ""):
            payload["conversation_id"] = conversation_id

        headers = {"Authorization": f"Bearer {app_key}", "Content-Type": "application/json"}

        try:
            async with self.client.stream("POST", url, json=payload, headers=headers, timeout=120.0) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode("utf-8", errors="replace")
                    logger.error(f"[Dify] stream 错误: {resp.status_code} - {body[:300]}")
                    yield {"event": "error", "message": f"Dify {resp.status_code}"}
                    return

                buffer = ""
                async for line in resp.aiter_lines():
                    buffer += line + "\n"
                    while "\n\n" in buffer:
                        chunk_text, buffer = buffer.split("\n\n", 1)
                        event_type = ""
                        data_str = ""
                        for l in chunk_text.split("\n"):
                            if l.startswith("event:"):
                                event_type = l[6:].strip()
                            elif l.startswith("data:"):
                                data_str = l[5:].strip()

                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        etype = event_type or data.get("event", "")
                        if etype in ("message", "agent_message"):
                            yield {"event": "message", "answer": data.get("answer", "")}
                        elif etype == "message_end":
                            yield {"event": "message_end", "conversation_id": data.get("conversation_id", conversation_id)}
                        elif etype == "error":
                            yield {"event": "error", "message": data.get("message", "未知错误")}

        except httpx.ConnectError:
            yield {"event": "error", "message": "无法连接 Dify 服务"}
        except httpx.TimeoutException:
            yield {"event": "error", "message": "Dify 请求超时"}
        except Exception as e:
            logger.error(f"[Dify] stream 异常: {e}")
            yield {"event": "error", "message": str(e)}

    def _mock_response(self, app_type: str, query: str) -> dict:
        mock = {
            "planner": f"（模拟）关于「{query}」，推荐旋转木马、小火车等经典项目。",
            "guide": f"（模拟）关于「{query}」，园区设有 5 个母婴室、4 家主题餐厅。",
            "ticket": f"（模拟）票价信息：成人票120元，儿童票80元，家庭套票280元起。",
        }
        return {"answer": mock.get(app_type, f"（模拟）{query}"), "conversation_id": "mock_001"}


dify_service = DifyService()
