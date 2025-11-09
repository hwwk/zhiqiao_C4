"""
News/Blog 采集器
通过 RSS/Atom Feed 采集新闻和博客内容
"""
import feedparser
from typing import Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
from base_collector import BaseCollector
from content_model import ContentItem, CollectionResult
from config_manager import CategoryType


class NewsCollector(BaseCollector):
    """新闻/博客内容采集器"""

    def __init__(self, author, timeout=30):
        super().__init__(author, timeout)
        self.feed_url = self._get_feed_url()

    def _get_feed_url(self) -> str:
        """
        获取 RSS/Atom Feed URL

        支持的格式：
        1. 直接的 feed URL（包含 feed、rss 或 atom）
        2. Simon Willison 格式：https://simonwillison.net/ -> https://simonwillison.net/atom/everything/
        3. 通用 WordPress：添加 /feed/ 或 /feed
        """
        url = self.author.url.rstrip('/')

        # 如果已经是 feed URL，直接返回
        if any(keyword in url.lower() for keyword in ['feed', 'rss', 'atom']):
            return url

        # Simon Willison 特殊处理
        if 'simonwillison.net' in url:
            return 'https://simonwillison.net/atom/everything/'

        # 尝试通用的 feed URL 模式
        # 先尝试获取页面，检查是否有 feed 链接
        try:
            response = self._make_request(url)
            if response:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找 RSS/Atom link
                feed_link = soup.find('link', {'type': 'application/rss+xml'})
                if not feed_link:
                    feed_link = soup.find('link', {'type': 'application/atom+xml'})

                if feed_link and feed_link.get('href'):
                    feed_href = feed_link['href']
                    # 处理相对路径
                    if feed_href.startswith('http'):
                        return feed_href
                    elif feed_href.startswith('/'):
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        return f"{parsed.scheme}://{parsed.netloc}{feed_href}"
                    else:
                        return f"{url}/{feed_href}"
        except:
            pass

        # 如果没找到，尝试常见的 feed 路径
        return url + '/feed/'

    def collect(self, max_items: int = 10) -> CollectionResult:
        """
        采集新闻/博客内容

        Args:
            max_items: 最多采集的条目数

        Returns:
            CollectionResult: 采集结果
        """
        try:
            # 解析 Feed
            feed = feedparser.parse(self.feed_url)

            if not feed.entries:
                return self._create_error_result(f"Feed 中没有找到任何条目")

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
                return self._create_error_result("未能解析任何有效的新闻条目")

            return self._create_success_result(items)

        except Exception as e:
            return self._create_error_result(f"采集失败: {str(e)}")

    def _parse_entry(self, entry, feed) -> Optional[ContentItem]:
        """
        解析单个新闻/博客条目

        Args:
            entry: Feed entry
            feed: 完整的 feed 对象

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
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text().strip()
            # 限制长度
            if len(description) > 500:
                description = description[:500] + '...'

        # 提取发布时间
        publish_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                publish_date = datetime(*entry.published_parsed[:6])
            except:
                pass

        # 如果没有 published，尝试 updated
        if not publish_date and hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                publish_date = datetime(*entry.updated_parsed[:6])
            except:
                pass

        # 提取封面图
        cover_image_url = None

        # 1. 尝试从 media:thumbnail 获取
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            if len(entry.media_thumbnail) > 0:
                cover_image_url = entry.media_thumbnail[0].get('url')

        # 2. 尝试从 media:content 获取
        if not cover_image_url and hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('medium') == 'image' or 'image' in media.get('type', ''):
                    cover_image_url = media.get('url')
                    break

        # 3. 尝试从 summary 中提取第一张图片
        if not cover_image_url and hasattr(entry, 'summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            img = soup.find('img')
            if img and img.get('src'):
                img_src = img['src']
                # 处理相对路径
                if img_src.startswith('http'):
                    cover_image_url = img_src
                elif img_src.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(link)
                    cover_image_url = f"{parsed.scheme}://{parsed.netloc}{img_src}"

        # 提取唯一 ID
        content_id = entry.get('id', link)

        return ContentItem(
            title=title,
            url=link,
            author_name=self.author.name,
            author_url=self.author.url,
            category=CategoryType.NEWS,
            description=description,
            publish_date=publish_date,
            cover_image_url=cover_image_url,
            content_id=content_id
        )
