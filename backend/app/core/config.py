"""
GoldSight AI V3.0 - 配置管理模块

使用 pydantic-settings 从 .env 文件和环境变量读取配置。
所有敏感信息通过环境变量注入，严禁硬编码。
"""

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置"""

    model_config = SettingsConfigDict(
        # 从项目根目录 .env 读取，backend/ 上一级
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 应用基础配置 ──────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True

    # ── 后端服务配置 ──────────────────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"

    # ── PostgreSQL 数据库配置 ─────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "goldsight"
    postgres_user: str = "goldsight"
    postgres_password: str = "goldsight_dev_2024"
    database_url: str = "postgresql://goldsight:goldsight_dev_2024@localhost:5432/goldsight"

    # ── Redis 缓存配置 ────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "goldsight_redis_dev_2024"
    redis_db: int = 0
    redis_url: str = "redis://:goldsight_redis_dev_2024@localhost:6379/0"

    # ── DeepSeek API 配置 ─────────────────────────────────────
    deepseek_api_key: Optional[str] = None
    deepseek_api_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # ── JWT 认证配置 ──────────────────────────────────────────
    jwt_secret_key: str = "please_change_this_to_a_secure_random_string_in_production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # ── CORS 配置 ─────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    @property
    def async_database_url(self) -> str:
        """将 DATABASE_URL 转换为 asyncpg 异步驱动格式"""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def deepseek_configured(self) -> bool:
        """检查 DeepSeek API Key 是否已配置"""
        return bool(
            self.deepseek_api_key
            and self.deepseek_api_key != "your_deepseek_api_key_here"
        )


# 全局单例
settings = Settings()
