"""
GoldSight AI V3.0 - 数据采集器基类

定义所有数据采集器的统一接口和通用逻辑。
每个数据源对应一个独立的 Collector 实现，继承 BaseCollector。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    数据采集器抽象基类

    所有数据源采集器必须实现以下接口：
    - source_name: 数据源唯一标识
    - target_table: 目标数据库表名
    - fetch(): 从外部数据源获取原始数据
    - clean(): 清洗原始数据为标准记录格式
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """数据源名称，用于记录来源（如 'yfinance', 'fred'）"""
        ...

    @property
    @abstractmethod
    def target_table(self) -> str:
        """目标数据库表名（如 'gold_prices', 'usd_data'）"""
        ...

    @abstractmethod
    async def fetch(self, **kwargs) -> List[Any]:
        """
        从外部数据源获取原始数据。
        对于同步 API（如 yfinance），使用 asyncio.to_thread 包装。

        Returns:
            原始数据列表（格式由具体采集器决定）
        """
        ...

    @abstractmethod
    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """
        清洗原始数据，转换为标准记录字典列表。

        每条记录必须包含目标表的业务字段。
        框架会自动补充 source、collected_at、quality_status。

        Returns:
            清洗后的记录字典列表
        """
        ...

    def validate(self, record: Dict[str, Any]) -> bool:
        """
        验证单条记录是否合法。
        子类可覆盖此方法添加特定校验规则。

        Returns:
            True 表示记录合法，False 表示应跳过
        """
        return True

    async def store(
        self,
        records: List[Dict[str, Any]],
        session: AsyncSession,
    ) -> int:
        """
        将记录写入目标数据库表。
        自动补充 source、collected_at、quality_status 字段。
        使用 ON CONFLICT DO NOTHING 避免重复插入。

        Returns:
            成功插入的记录数量
        """
        if not records:
            return 0

        now = datetime.utcnow()
        columns = list(records[0].keys())

        # 自动补充框架字段
        for col in ("source", "collected_at", "quality_status"):
            if col not in columns:
                columns.append(col)

        col_names = ", ".join(columns)
        placeholders = ", ".join([f":{c}" for c in columns])

        sql = text(
            f"INSERT INTO {self.target_table} ({col_names}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT DO NOTHING"
        )

        inserted = 0
        for record in records:
            values = dict(record)
            values.setdefault("source", self.source_name)
            values.setdefault("collected_at", now)
            values.setdefault("quality_status", "valid")

            try:
                result = await session.execute(sql, values)
                if result.rowcount > 0:
                    inserted += 1
            except Exception as e:
                logger.warning(
                    f"[{self.source_name}] 插入记录失败: {e}"
                )
                await self._log_quality_issue(
                    session, "accuracy", "warning",
                    f"数据插入失败: {e}",
                    {"record": str(values)[:500]},
                )

        return inserted

    async def _log_quality_issue(
        self,
        session: AsyncSession,
        check_type: str,
        severity: str,
        message: str,
        details: Optional[Dict] = None,
    ) -> None:
        """记录数据质量问题到 data_quality_logs 表"""
        try:
            sql = text(
                "INSERT INTO data_quality_logs "
                "(timestamp, table_name, check_type, severity, message, "
                "details, source, collected_at, quality_status) "
                "VALUES (:ts, :tbl, :ct, :sev, :msg, "
                ":det, :src, :cat, 'pending')"
            )
            await session.execute(sql, {
                "ts": datetime.utcnow(),
                "tbl": self.target_table,
                "ct": check_type,
                "sev": severity,
                "msg": message,
                "det": str(details or {}),
                "src": self.source_name,
                "cat": datetime.utcnow(),
            })
        except Exception as e:
            logger.error(f"[{self.source_name}] 写入质量日志失败: {e}")
