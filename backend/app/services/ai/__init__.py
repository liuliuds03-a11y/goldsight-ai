"""
GoldSight AI V3.0 - AI 预测模块

提供 DeepSeek 大模型接入与智能预测功能：
- deepseek_client: DeepSeek API 异步客户端
- prediction_engine: AI 综合预测引擎
"""

from app.services.ai.deepseek_client import DeepSeekClient
from app.services.ai.prediction_engine import run_ai_prediction, run_ai_summary

__all__ = [
    "DeepSeekClient",
    "run_ai_prediction",
    "run_ai_summary",
]
