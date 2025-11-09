"""
Podcast 采集器
通过 RSS Feed 采集播客内容
"""
import feedparser
from typing import Optional, List
from datetime import datetime
from base_collector import BaseCollector
from content_model import ContentItem, CollectionResult
from config_manager import CategoryType


class PodcastCollector(BaseCollector):
    """Podcast 内容采集器"""

    def __init__(self, author, timeout=30):
        super().__init__(author, timeout)
        self.rss_url = self._get_rss_url()

    def _get_rss_url(self) -> str:
        """
        获取 Podcast RSS Feed URL

        支持的格式：
        1. 直接的 RSS feed URL（包含 feed 或 rss）
        2. Lex Fridman 格式：https://lexfridman.com/podcast/ -> https://lexfridman.com/feed/podcast/
        """
        url = self.author.url.rstrip('/')

        # 如果已经是 feed URL，直接返回
        if 'feed' in url.lower() or 'rss' in url.lower():
            return url

        # Lex Fridman 特殊处理
        if 'lexfridman.com' in url:
            if url.endswith('/podcast'):
                return 'https://lexfridman.com/feed/podcast/'
            elif url.endswith('/podcast/'):
                return 'https://lexfridman.com/feed/podcast/'

        # 尝试通用的 feed URL 模式
        if url.endswith('/'):
            return url + 'feed/'
        else:
            return url + '/feed/'

    def collect(self, max_items: int = 10) -> CollectionResult:
        """
        采集 Podcast 内容

        Args:
            max_items: 最多采集的条目数

        Returns:
            CollectionResult: 采集结果
        """
        try:
            # 解析 RSS Feed
            feed = feedparser.parse(self.rss_url)

            if not feed.entries:
                return self._create_error_result(f"RSS Feed 中没有找到任何条目")

            items: List[ContentItem] = []

            for entry in feed.entries[:max_items]:
                try:
                    item = self._parse_entry(entry, feed)
                    if item:
                        items.append(item)
                except Exception as e:
                    print(f"警告: 解析条目失败: {e}")
                    continue

            if not items:
                return self._create_error_result("未能解析任何有效的 Podcast 条目")

            return self._create_success_result(items)

        except Exception as e:
            return self._create_error_result(f"采集失败: {str(e)}")

    def _parse_entry(self, entry, feed) -> Optional[ContentItem]:
        """
        解析单个 Podcast 条目

        Args:
            entry: RSS feed entry
            feed: 完整的 feed 对象（用于获取频道级别的图片）

        Returns:
            ContentItem 或 None
        """
        # 提取标题
        title = entry.get('title', '').strip()
        if not title:
            return None

        # 提取链接
        link = entry.get('link', '').strip()
        if not link:
            return None

        # 提取简介（尝试多个字段）
        description = ''
        if hasattr(entry, 'summary'):
            description = entry.summary
        elif hasattr(entry, 'description'):
            description = entry.description
        elif hasattr(entry, 'content'):
            description = entry.content[0].value if entry.content else ''

        # 清理 HTML 标签
        if description:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text().strip()
            # 限制长度
            if len(description) > 500:
                description = description[:500] + '...'

        # 提取发布时间
        publish_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                from datetime import datetime
                publish_date = datetime(*entry.published_parsed[:6])
            except:
                pass

        # 提取封面图（优先级：条目图片 > 频道图片）
        cover_image_url = None

        # 1. 尝试从条目的 itunes:image 获取
        if hasattr(entry, 'image'):
            if isinstance(entry.image, dict) and 'href' in entry.image:
                cover_image_url = entry.image['href']
            elif isinstance(entry.image, str):
                cover_image_url = entry.image

        # 2. 尝试从 media:thumbnail 获取
        if not cover_image_url and hasattr(entry, 'media_thumbnail'):
            if entry.media_thumbnail and len(entry.media_thumbnail) > 0:
                cover_image_url = entry.media_thumbnail[0].get('url')

        # 3. 使用频道级别的图片
        if not cover_image_url and hasattr(feed, 'feed'):
            if hasattr(feed.feed, 'image'):
                if isinstance(feed.feed.image, dict) and 'href' in feed.feed.image:
                    cover_image_url = feed.feed.image['href']
                elif isinstance(feed.feed.image, dict) and 'url' in feed.feed.image:
                    cover_image_url = feed.feed.image['url']

        # 提取唯一 ID
        content_id = entry.get('id', link)

        return ContentItem(
            title=title,
            url=link,
            author_name=self.author.name,
            author_url=self.author.url,
            category=CategoryType.PODCAST,
            description=description,
            publish_date=publish_date,
            cover_image_url=cover_image_url,
            content_id=content_id
        )
