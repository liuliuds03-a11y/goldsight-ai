"""
GoldSight AI V3.0 - 统一异常处理模块

定义自定义异常类和全局异常处理器。
"""

import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


# ── 自定义异常 ────────────────────────────────────────────────


class GoldSightException(Exception):
    """GoldSight 基础异常"""

    def __init__(
        self,
        message: str = "服务器内部错误",
        code: int = 500,
        data: Optional[dict] = None,
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class NotFoundException(GoldSightException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在", data: Optional[dict] = None):
        super().__init__(message=message, code=404, data=data)


class ValidationException(GoldSightException):
    """参数校验失败"""

    def __init__(self, message: str = "参数校验失败", data: Optional[dict] = None):
        super().__init__(message=message, code=422, data=data)


class ServiceUnavailableException(GoldSightException):
    """服务不可用"""

    def __init__(self, message: str = "服务暂时不可用", data: Optional[dict] = None):
        super().__init__(message=message, code=503, data=data)


# ── 全局异常处理器注册 ────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(GoldSightException)
    async def goldsight_exception_handler(
        request: Request, exc: GoldSightException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=200,  # 业务错误仍返回 HTTP 200，通过 code 区分
            content={
                "code": exc.code,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(f"参数校验失败: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "code": 422,
                "message": "请求参数校验失败",
                "data": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"未预期的异常: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": "服务器内部错误",
                "data": None,
            },
        )
