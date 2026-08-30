"""
GoldSight AI V3.0 - DeepSeek API 异步客户端

封装 DeepSeek 大模型 API 调用：
- 使用 httpx 异步请求
- 支持系统提示词 + 用户消息
- 超时重试（最多 3 次）
- API 调用失败时优雅降级
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── 常量 ──────────────────────────────────────────────────────

_MAX_RETRIES = 3
_REQUEST_TIMEOUT = 60.0  # 秒


class DeepSeekClient:
    """
    DeepSeek API 异步客户端

    使用 httpx.AsyncClient 调用 DeepSeek Chat Completions API，
    内置超时重试与降级机制。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = (base_url or settings.deepseek_api_base_url).rstrip("/")
        self.model = model or settings.deepseek_model

    @property
    def _headers(self) -> Dict[str, str]:
        """构造请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def _completions_url(self) -> str:
        """Chat Completions 端点 URL"""
        return f"{self.base_url}/v1/chat/completions"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek Chat Completions API

        Args:
            messages: 消息列表，每条包含 role 和 content
            temperature: 采样温度（0-2）
            max_tokens: 最大生成 token 数
            response_format: 响应格式约束，如 {"type": "json_object"}

        Returns:
            API 原始响应中的第一个 choice.message 内容（已解析）

        Raises:
            DeepSeekAPIError: API 调用最终失败（重试耗尽后）
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        last_error: Optional[Exception] = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                logger.debug(
                    f"DeepSeek API 请求 (第 {attempt}/{_MAX_RETRIES} 次): "
                    f"model={self.model}, messages_count={len(messages)}"
                )

                async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
                    response = await client.post(
                        self._completions_url,
                        headers=self._headers,
                        json=payload,
                    )

                    # HTTP 状态码检查
                    if response.status_code != 200:
                        error_body = response.text[:500]
                        logger.warning(
                            f"DeepSeek API 返回非 200 状态码: "
                            f"{response.status_code}, body={error_body}"
                        )
                        raise DeepSeekAPIError(
                            f"API 返回状态码 {response.status_code}: {error_body}"
                        )

                    # 解析响应
                    data = response.json()
                    choices = data.get("choices", [])
                    if not choices:
                        raise DeepSeekAPIError("API 响应中无 choices 字段")

                    message = choices[0].get("message", {})
                    content = message.get("content", "")

                    if not content:
                        raise DeepSeekAPIError("API 响应中 message.content 为空")

                    # 记录 token 使用情况
                    usage = data.get("usage", {})
                    logger.info(
                        f"DeepSeek API 调用成功: "
                        f"prompt_tokens={usage.get('prompt_tokens', 'N/A')}, "
                        f"completion_tokens={usage.get('completion_tokens', 'N/A')}, "
                        f"total_tokens={usage.get('total_tokens', 'N/A')}"
                    )

                    return {"content": content, "usage": usage}

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"DeepSeek API 请求超时 (第 {attempt}/{_MAX_RETRIES} 次): {e}"
                )
            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"DeepSeek API 网络错误 (第 {attempt}/{_MAX_RETRIES} 次): {e}"
                )
            except DeepSeekAPIError as e:
                last_error = e
                logger.warning(
                    f"DeepSeek API 业务错误 (第 {attempt}/{_MAX_RETRIES} 次): {e}"
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    f"DeepSeek API 未知错误 (第 {attempt}/{_MAX_RETRIES} 次): {e}"
                )

        # 重试耗尽
        raise DeepSeekAPIError(
            f"DeepSeek API 调用失败（已重试 {_MAX_RETRIES} 次）: {last_error}"
        )

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        调用 DeepSeek 并期望返回 JSON 格式

        自动解析返回内容为 Python 字典。
        若解析失败，降级返回包含原始文本的错误字典。

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 采样温度
            max_tokens: 最大 token 数

        Returns:
            解析后的 JSON 字典
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            result = await self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
        except DeepSeekAPIError:
            # 如果指定 response_format 失败，尝试不带格式约束
            logger.info("尝试不带 JSON 格式约束重新调用 DeepSeek API")
            result = await self.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        content = result["content"]

        # 尝试解析 JSON
        try:
            parsed = json.loads(content)
            return parsed
        except (json.JSONDecodeError, TypeError):
            # 尝试从文本中提取 JSON 块
            parsed = _extract_json_from_text(content)
            if parsed is not None:
                return parsed
            logger.warning(f"DeepSeek 返回内容无法解析为 JSON: {content[:200]}")
            return {
                "error": "JSON 解析失败",
                "raw_content": content,
            }

    async def chat_text(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        调用 DeepSeek 并返回纯文本结果

        用于不需要 JSON 结构的场景（如一句话摘要）。

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            temperature: 采样温度
            max_tokens: 最大 token 数

        Returns:
            模型生成的文本内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result["content"]

    def is_configured(self) -> bool:
        """检查客户端是否已配置（API Key 是否可用）"""
        return bool(
            self.api_key
            and self.api_key != "your_deepseek_api_key_here"
        )


# ── 工具函数 ──────────────────────────────────────────────────


def _extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    尝试从包含代码块的文本中提取 JSON 对象

    支持 ```json ... ``` 和 ``` ... ``` 格式。
    """
    import re

    # 匹配 ```json ... ``` 或 ``` ... ```
    patterns = [
        r"```json\s*\n([\s\S]*?)\n\s*```",
        r"```\s*\n([\s\S]*?)\n\s*```",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                continue

    # 最后尝试直接解析整段文本
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    return None


# ── 自定义异常 ────────────────────────────────────────────────


class DeepSeekAPIError(Exception):
    """DeepSeek API 调用异常"""

    def __init__(self, message: str = "DeepSeek API 调用失败"):
        self.message = message
        super().__init__(self.message)
