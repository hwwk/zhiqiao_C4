"""
YouTube 内容采集器
通过 RSS Feed 采集 YouTube 频道内容
"""
import re
import feedparser
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from base_collector import BaseCollector
from content_model import ContentItem, CollectionResult
from config_manager import Author, CategoryType


class YouTubeCollector(BaseCollector):
    """YouTube 采集器"""

    def __init__(self, author: Author, timeout: int = 30):
        """
        初始化 YouTube 采集器

        Args:
            author: 作者配置对象
            timeout: 请求超时时间
        """
        super().__init__(author, timeout)
        self.channel_id = self._extract_channel_id()
        self.rss_url = None

        if self.channel_id:
            self.rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={self.channel_id}"

    def _extract_channel_id(self) -> Optional[str]:
        """
        从作者URL中提取频道ID

        Returns:
            str: 频道ID，失败返回None
        """
        url = self.author.url

        # 如果是 @username 格式，需要先获取真实的频道ID
        if "/@" in url:
            return self._get_channel_id_from_handle(url)

        # 如果是 /channel/ID 格式
        channel_match = re.search(r'/channel/([a-zA-Z0-9_-]+)', url)
        if channel_match:
            return channel_match.group(1)

        # 如果是 /c/name 或 /user/name 格式
        if "/c/" in url or "/user/" in url:
            return self._get_channel_id_from_page(url)

        return None

    def _get_channel_id_from_handle(self, url: str) -> Optional[str]:
        """
        从 @username 格式的URL获取频道ID

        Args:
            url: YouTube 频道URL

        Returns:
            str: 频道ID，失败返回None
        """
        try:
            response = self._fetch_url(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 尝试从页面中提取频道ID
            # 方法1: 从 link 标签中提取
            rss_link = soup.find('link', {'rel': 'alternate', 'type': 'application/rss+xml'})
            if rss_link and rss_link.get('href'):
                match = re.search(r'channel_id=([a-zA-Z0-9_-]+)', rss_link['href'])
                if match:
                    return match.group(1)

            # 方法2: 从 meta 标签中提取
            channel_id_meta = soup.find('meta', {'property': 'og:url'})
            if channel_id_meta and channel_id_meta.get('content'):
                match = re.search(r'/channel/([a-zA-Z0-9_-]+)', channel_id_meta['content'])
                if match:
                    return match.group(1)

            # 方法3: 从 script 中提取
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'channelId' in script.string:
                    match = re.search(r'"channelId":"([a-zA-Z0-9_-]+)"', script.string)
                    if match:
                        return match.group(1)

        except Exception as e:
            print(f"从handle获取频道ID失败: {e}")

        return None

    def _get_channel_id_from_page(self, url: str) -> Optional[str]:
        """
        从频道页面获取频道ID

        Args:
            url: YouTube 频道URL

        Returns:
            str: 频道ID，失败返回None
        """
        try:
            response = self._fetch_url(url)
            if not response:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 从 link 标签中提取
            rss_link = soup.find('link', {'rel': 'alternate', 'type': 'application/rss+xml'})
            if rss_link and rss_link.get('href'):
                match = re.search(r'channel_id=([a-zA-Z0-9_-]+)', rss_link['href'])
                if match:
                    return match.group(1)

        except Exception as e:
            print(f"从页面获取频道ID失败: {e}")

        return None

    def collect(self, max_items: int = 10) -> CollectionResult:
        """
        采集 YouTube 频道内容

        Args:
            max_items: 最大采集条目数

        Returns:
            CollectionResult: 采集结果
        """
        # 检查是否有有效的RSS URL
        if not self.rss_url:
            return self._create_error_result("无法获取频道ID，请检查URL格式")

        try:
            # 解析 RSS Feed
            feed = feedparser.parse(self.rss_url)

            if not feed.entries:
                return self._create_error_result("未找到任何视频内容")

            items = []
            for entry in feed.entries[:max_items]:
                try:
                    item = self._parse_entry(entry)
                    if item:
                        items.append(item)
                except Exception as e:
                    print(f"解析条目失败: {e}")
                    continue

            return self._create_success_result(items)

        except Exception as e:
            return self._create_error_result(f"采集失败: {str(e)}")

    def _parse_entry(self, entry) -> Optional[ContentItem]:
        """
        解析单个RSS条目

        Args:
            entry: feedparser 条目对象

        Returns:
            ContentItem: 内容项，失败返回None
        """
        try:
            # 提取基本信息
            title = entry.get('title', '').strip()
            url = entry.get('link', '')
            description = entry.get('summary', '').strip()

            # 提取发布时间
            publish_date = None
            if 'published_parsed' in entry and entry.published_parsed:
                from time import struct_time
                import calendar
                publish_date = datetime.fromtimestamp(
                    calendar.timegm(entry.published_parsed)
                )
            elif 'published' in entry:
                try:
                    publish_date = date_parser.parse(entry.published)
                except:
                    pass

            # 提取缩略图
            thumbnail_url = None
            if 'media_thumbnail' in entry and entry.media_thumbnail:
                thumbnail_url = entry.media_thumbnail[0].get('url')

            # 如果没有缩略图，尝试从视频ID提取
            if not thumbnail_url:
                video_id = self._extract_video_id(url)
                if video_id:
                    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"

            # 提取视频ID作为唯一标识
            content_id = self._extract_video_id(url)

            # 创建内容项
            item = ContentItem(
                title=title,
                url=url,
                author_name=self.author.name,
                author_url=self.author.url,
                category=CategoryType.VIDEO,
                description=description,
                publish_date=publish_date,
                thumbnail_url=thumbnail_url,
                content_id=content_id
            )

            return item

        except Exception as e:
            print(f"解析条目失败: {e}")
            return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """
        从YouTube URL中提取视频ID

        Args:
            url: YouTube 视频URL

        Returns:
            str: 视频ID，失败返回None
        """
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None


def create_collector(author: Author) -> Optional[BaseCollector]:
    """
    创建合适的采集器

    Args:
        author: 作者配置对象

    Returns:
        BaseCollector: 采集器实例，失败返回None
    """
    # 根据分类创建采集器
    if author.category == CategoryType.VIDEO:
        return YouTubeCollector(author)
    elif author.category == CategoryType.PODCAST:
        # 导入 Podcast 采集器
        from podcast_collector import PodcastCollector
        return PodcastCollector(author)
    elif author.category == CategoryType.NEWS:
        # 导入 News 采集器
        from news_collector import NewsCollector
        return NewsCollector(author)

    # 可以在这里添加其他平台的采集器
    # elif 'podcast' in url:
    #     return PodcastCollector(author)
    # elif 'news' in url:
    #     return NewsCollector(author)

    return None
