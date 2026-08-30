"""
GoldSight AI V3.0 - 数据采集运行脚本

命令行运行采集器，支持运行全部或指定采集器。

使用方式（在项目根目录执行）：
    # 运行所有采集器
    .venv\\Scripts\\python.exe -m app.services.data_collection.runner --all

    # 仅运行黄金价格采集器
    .venv\\Scripts\\python.exe -m app.services.data_collection.runner --collector GoldPriceCollector

    # 列出已注册采集器
    .venv\\Scripts\\python.exe -m app.services.data_collection.runner --list
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="GoldSight 数据采集运行器")
    parser.add_argument(
        "--all", action="store_true",
        help="运行所有已注册采集器",
    )
    parser.add_argument(
        "--collector", type=str, default=None,
        help="指定采集器类名（如 GoldPriceCollector）",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="列出所有已注册采集器",
    )
    parser.add_argument(
        "--days", type=int, default=120,
        help="历史数据天数（默认 120，确保 90+ 交易日）",
    )
    args = parser.parse_args()

    # 导入数据采集模块以触发采集器注册
    from app.services.data_collection import (
        CollectorRegistry,
        DataPipeline,
    )

    registry = CollectorRegistry.get_instance()

    # 列出采集器
    if args.list:
        names = registry.list_names()
        print(f"已注册采集器 ({len(names)}):")
        for name in names:
            collector = registry.get(name)
            if collector:
                print(f"  - {name}")
                print(f"    数据源: {collector.source_name}")
                print(f"    目标表: {collector.target_table}")
        return

    pipeline = DataPipeline(max_retries=3, retry_delay=2.0)

    # 运行指定采集器
    if args.collector:
        print(f"正在运行采集器: {args.collector} ...")
        result = await pipeline.run(args.collector, days=args.days)
        _print_result(result)
        return

    # 运行所有采集器
    if args.all:
        print("正在运行所有采集器...")
        results = await pipeline.run_all(days=args.days)
        for result in results:
            _print_result(result)
        return

    # 无参数时显示帮助
    parser.print_help()


def _print_result(result: dict) -> None:
    """格式化打印采集结果"""
    status_mark = {
        "success": "[OK]",
        "error": "[FAIL]",
        "empty": "[EMPTY]",
        "pending": "[WAIT]",
    }
    mark = status_mark.get(result.get("status", ""), "[??]")
    print(f"\n{mark} [{result.get('collector', '?')}]")
    print(f"   状态: {result.get('status')}")
    print(f"   数据源: {result.get('source')}")
    print(f"   目标表: {result.get('target_table')}")
    print(f"   获取: {result.get('records_fetched')} 条")
    print(f"   清洗: {result.get('records_cleaned')} 条")
    print(f"   验证: {result.get('records_valid')} 条")
    print(f"   入库: {result.get('records_stored')} 条")
    if result.get("errors"):
        for err in result["errors"]:
            print(f"   [!] {err}")


if __name__ == "__main__":
    asyncio.run(main())
