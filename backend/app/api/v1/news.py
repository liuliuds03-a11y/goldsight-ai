"""
GoldSight AI V3.0 - 新闻资讯聚合接口

从多个金融新闻 RSS 源聚合黄金/贵金属/宏观经济相关新闻。
使用 Redis 缓存 30 分钟，避免频繁请求外部源。
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Query

from app.core.redis_client import get_redis, is_redis_available
from app.core.response import success

logger = logging.getLogger(__name__)

router = APIRouter()

NEWS_CACHE_TTL = 1800  # 30 分钟
NEWS_CACHE_KEY = "news_feed:"

# RSS 新闻源配置
RSS_FEEDS = [
    {
        "name": "Kitco Gold News",
        "url": "https://www.kitco.com/rss/gold.xml",
        "category": "黄金",
        "icon": "",
    },
    {
        "name": "Kitco Silver News",
        "url": "https://www.kitco.com/rss/silver.xml",
        "category": "白银",
        "icon": "🥈",
    },
    {
        "name": "Reuters Business",
        "url": "https://feeds.reuters.com/reuters/businessNews",
        "category": "财经",
        "icon": "",
    },
    {
        "name": "CNBC Top News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "category": "市场",
        "icon": "",
    },
    {
        "name": "MarketWatch",
        "url": "https://feeds.marketwatch.com/marketwatch/topstories/",
        "category": "市场",
        "icon": "📈",
    },
]


def _parse_rss_feed(xml_content: str, source_name: str, category: str, icon: str) -> List[Dict[str, Any]]:
    """解析 RSS XML 内容为新闻条目"""
    items = []
    try:
        root = ET.fromstring(xml_content)
        channel = root.find("channel")
        if channel is None:
            return items

        for item in channel.findall("item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            pub_date_elem = item.find("pubDate")

            if title_elem is None or title_elem.text is None:
                continue

            title = title_elem.text.strip()
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            description = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""
            # 清理 HTML 标签
            if "<" in description:
                description = ET.fromstring(f"<div>{description}</div>").text or ""

            pub_date = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    # 尝试解析 RFC 822 日期格式
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(pub_date_elem.text).isoformat()
                except Exception:
                    pub_date = pub_date_elem.text

            items.append({
                "title": title,
                "link": link,
                "description": description[:200],  # 限制描述长度
                "source": source_name,
                "category": category,
                "icon": icon,
                "pub_date": pub_date,
                "published_at": pub_date,
            })
    except ET.ParseError as e:
        logger.warning(f"RSS 解析失败 [{source_name}]: {e}")
    except Exception as e:
        logger.warning(f"RSS 处理异常 [{source_name}]: {e}")

    return items


async def _fetch_feed(feed_config: Dict[str, str], timeout: float = 10.0) -> List[Dict[str, Any]]:
    """获取并解析单个 RSS 源"""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(feed_config["url"])
            if resp.status_code == 200:
                return _parse_rss_feed(
                    resp.text,
                    feed_config["name"],
                    feed_config["category"],
                    feed_config["icon"],
                )
    except Exception as e:
        logger.warning(f"RSS 获取失败 [{feed_config['name']}]: {e}")
    return []


async def _get_cached_news() -> Optional[List[Dict[str, Any]]]:
    """从缓存获取新闻"""
    if not is_redis_available():
        return None
    try:
        r = get_redis()
        data = await r.get(NEWS_CACHE_KEY + "latest")
        if data:
            import json
            return json.loads(data)
    except Exception as e:
        logger.warning(f"新闻缓存读取失败: {e}")
    return None


async def _set_cached_news(news: List[Dict[str, Any]]) -> None:
    """缓存新闻数据"""
    if not is_redis_available():
        return
    try:
        r = get_redis()
        import json
        await r.setex(
            NEWS_CACHE_KEY + "latest",
            NEWS_CACHE_TTL,
            json.dumps(news, ensure_ascii=False),
        )
    except Exception as e:
        logger.warning(f"新闻缓存写入失败: {e}")


@router.get("/news/feed")
async def get_news_feed(
    category: Optional[str] = Query(None, description="新闻分类过滤"),
    limit: int = Query(50, ge=1, le=100, description="返回条数"),
    source: Optional[str] = Query(None, description="新闻源过滤"),
):
    """
    获取聚合新闻列表

    从多个 RSS 源获取最新金融新闻，支持分类和来源过滤。
    """
    # 尝试从缓存获取
    cached = await _get_cached_news()
    if cached:
        # 应用过滤
        filtered = cached
        if category:
            filtered = [n for n in filtered if n.get("category") == category]
        if source:
            filtered = [n for n in filtered if n.get("source") == source]
        return success(data={
            "articles": filtered[:limit],
            "total": len(filtered),
            "_cached": True,
        })

    # 从 RSS 源获取
    import asyncio
    tasks = [_fetch_feed(feed) for feed in RSS_FEEDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles = []
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)

    # 按发布时间排序（最新的在前）
    def sort_key(article):
        pub_date = article.get("pub_date")
        if pub_date:
            try:
                return datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except Exception:
                pass
        return datetime.min.replace(tzinfo=timezone.utc)

    all_articles.sort(key=sort_key, reverse=True)

    # 应用过滤
    filtered = all_articles
    if category:
        filtered = [n for n in filtered if n.get("category") == category]
    if source:
        filtered = [n for n in filtered if n.get("source") == source]

    # 缓存结果
    await _set_cached_news(all_articles)

    return success(data={
        "articles": filtered[:limit],
        "total": len(filtered),
        "sources": [f["name"] for f in RSS_FEEDS],
        "categories": list(set(f["category"] for f in RSS_FEEDS)),
        "_cached": False,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/news/categories")
async def get_news_categories():
    """获取新闻分类列表"""
    categories = list(set(f["category"] for f in RSS_FEEDS))
    sources = [{"name": f["name"], "category": f["category"], "icon": f["icon"]} for f in RSS_FEEDS]
    return success(data={
        "categories": categories,
        "sources": sources,
    })
