"""
GoldSight AI V3.0 - 采集器注册中心

管理所有数据采集器的注册、发现和实例化。
支持通过装饰器或方法调用注册新采集器，无需修改框架代码（开闭原则）。
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Type

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class CollectorRegistry:
    """
    采集器注册中心（单例模式）

    使用方式：
        registry = CollectorRegistry.get_instance()
        registry.register(GoldPriceCollector)
        collector = registry.get("gold_prices")
    """

    _instance: Optional[CollectorRegistry] = None
    _collectors: Dict[str, Type[BaseCollector]] = {}

    @classmethod
    def get_instance(cls) -> CollectorRegistry:
        """获取全局单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, collector_cls: Type[BaseCollector]) -> None:
        """
        注册采集器类

        Args:
            collector_cls: BaseCollector 的子类
        """
        name = collector_cls.__name__
        self._collectors[name] = collector_cls
        logger.info(f"注册采集器: {name}")

    def get(self, name: str) -> Optional[BaseCollector]:
        """
        按类名获取采集器实例

        Args:
            name: 采集器类名

        Returns:
            采集器实例，未找到返回 None
        """
        cls = self._collectors.get(name)
        if cls is not None:
            return cls()
        return None

    def get_all(self) -> Dict[str, BaseCollector]:
        """获取所有已注册采集器的实例"""
        return {name: cls() for name, cls in self._collectors.items()}

    def list_names(self) -> list:
        """列出所有已注册采集器名称"""
        return list(self._collectors.keys())

    @classmethod
    def reset(cls) -> None:
        """重置注册表（仅用于测试）"""
        cls._instance = None
        cls._collectors = {}
