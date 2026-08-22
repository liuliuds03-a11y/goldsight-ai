"""
GoldSight AI V3.0 - 统一响应格式模块

所有 API 端点返回统一 JSON 格式：
{
    "code": 200,
    "message": "success",
    "data": {...}
}
"""

from typing import Any, Optional

from pydantic import BaseModel


class UnifiedResponse(BaseModel):
    """统一响应体"""

    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


def success(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> dict:
    """构造成功响应"""
    return {"code": code, "message": message, "data": data}


def error(
    message: str = "error",
    code: int = 400,
    data: Any = None,
) -> dict:
    """构造错误响应"""
    return {"code": code, "message": message, "data": data}
