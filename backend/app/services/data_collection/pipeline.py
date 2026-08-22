"""
GoldSight AI V3.0 - 数据流水线

编排完整的采集流程：获取 → 清洗 → 验证 → 入库。
支持自动重试、错误日志、质量追踪。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_collector import BaseCollector
from .registry import CollectorRegistry

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    数据采集流水线

    完整流程：
    1. fetch   — 从外部 API 获取原始数据（支持重试）
    2. clean   — 清洗为标准记录格式
    3. validate — 逐条校验
    4. store   — 写入 PostgreSQL

    使用方式：
        pipeline = DataPipeline()
        result = await pipeline.run("GoldPriceCollector")
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.registry = CollectorRegistry.get_instance()
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def run(
        self,
        collector_name: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行指定采集器的完整流水线

        Args:
            collector_name: 采集器类名
            **kwargs: 传递给 fetch() 的参数

        Returns:
            执行结果摘要字典
        """
        collector = self.registry.get(collector_name)
        if collector is None:
            logger.error(f"采集器未注册: {collector_name}")
            return {
                "collector": collector_name,
                "status": "error",
                "message": "采集器未注册",
                "records_fetched": 0,
                "records_stored": 0,
                "errors": [f"采集器 '{collector_name}' 未在注册中心注册"],
            }

        start_time = datetime.utcnow()
        result: Dict[str, Any] = {
            "collector": collector_name,
            "source": collector.source_name,
            "target_table": collector.target_table,
            "status": "pending",
            "records_fetched": 0,
            "records_cleaned": 0,
            "records_valid": 0,
            "records_stored": 0,
            "errors": [],
            "started_at": start_time.isoformat(),
            "finished_at": None,
        }

        # ── 步骤 1：获取数据（带重试） ──────────────────────
        try:
            raw_data = await self._fetch_with_retry(collector, **kwargs)
            result["records_fetched"] = len(raw_data)
            logger.info(
                f"[{collector_name}] 获取到 {len(raw_data)} 条原始数据"
            )
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"获取数据失败: {e}")
            result["finished_at"] = datetime.utcnow().isoformat()
            logger.error(f"[{collector_name}] 获取数据失败: {e}")
            return result

        if not raw_data:
            result["status"] = "empty"
            result["finished_at"] = datetime.utcnow().isoformat()
            logger.warning(f"[{collector_name}] 未获取到数据")
            return result

        # ── 步骤 2：清洗数据 ────────────────────────────────
        try:
            cleaned = collector.clean(raw_data)
            result["records_cleaned"] = len(cleaned)
            logger.info(
                f"[{collector_name}] 清洗后 {len(cleaned)} 条记录"
            )
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"清洗数据失败: {e}")
            result["finished_at"] = datetime.utcnow().isoformat()
            logger.error(f"[{collector_name}] 清洗数据失败: {e}")
            return result

        # ── 步骤 3：逐条验证 ────────────────────────────────
        valid_records: List[Dict[str, Any]] = []
        for record in cleaned:
            if collector.validate(record):
                valid_records.append(record)
            else:
                logger.debug(
                    f"[{collector_name}] 记录验证跳过: {record}"
                )
        result["records_valid"] = len(valid_records)

        # ── 步骤 4：写入数据库 ──────────────────────────────
        if valid_records:
            try:
                from app.core.database import get_db_context
                async with get_db_context() as session:
                    stored = await collector.store(valid_records, session)
                    result["records_stored"] = stored
                    logger.info(
                        f"[{collector_name}] 成功写入 {stored} 条记录"
                    )
            except Exception as e:
                result["status"] = "error"
                result["errors"].append(f"存储数据失败: {e}")
                result["finished_at"] = datetime.utcnow().isoformat()
                logger.error(f"[{collector_name}] 存储数据失败: {e}")
                return result

        # ── 完成 ────────────────────────────────────────────
        result["status"] = "success"
        result["finished_at"] = datetime.utcnow().isoformat()
        return result

    async def run_all(self, **kwargs) -> List[Dict[str, Any]]:
        """运行所有已注册采集器"""
        results = []
        for name in self.registry.list_names():
            result = await self.run(name, **kwargs)
            results.append(result)
        return results

    # ── 内部方法 ────────────────────────────────────────────

    async def _fetch_with_retry(
        self,
        collector: BaseCollector,
        **kwargs,
    ) -> List[Any]:
        """带重试的数据获取"""
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                data = await collector.fetch(**kwargs)
                if not isinstance(data, list):
                    data = [data] if data is not None else []
                return data
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))
                    logger.warning(
                        f"[{collector.source_name}] "
                        f"第 {attempt} 次获取失败: {e}，"
                        f"{delay:.1f}s 后重试..."
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"[{collector.source_name}] "
                        f"第 {attempt} 次获取失败，已达最大重试次数: {e}"
                    )

        raise last_error  # type: ignore[misc]
