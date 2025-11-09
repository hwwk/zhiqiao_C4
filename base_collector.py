"""
采集器基类
定义统一的内容采集接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from datetime import datetime, timedelta
from content_model import ContentItem, CollectionResult
from config_manager import Author, CategoryType


class BaseCollector(ABC):
    """采集器基类"""

    def __init__(self, author: Author, timeout: int = 30):
        """
        初始化采集器

        Args:
            author: 作者配置对象
            timeout: 请求超时时间（秒）
        """
        self.author = author
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    @abstractmethod
    def collect(self, max_items: int = 10) -> CollectionResult:
        """
        采集内容（子类必须实现）

        Args:
            max_items: 最大采集条目数

        Returns:
            CollectionResult: 采集结果
        """
        pass

    def collect_today_only(self, max_items: int = 10) -> CollectionResult:
        """
        只采集今天发布的内容

        Args:
            max_items: 最大采集条目数

        Returns:
            CollectionResult: 只包含今天发布内容的采集结果
        """
        result = self.collect(max_items)

        if result.success:
            # 筛选今天的内容
            today_items = result.get_today_items()
            result.items = today_items

        return result

    def _create_success_result(self, items: List[ContentItem]) -> CollectionResult:
        """
        创建成功的采集结果

        Args:
            items: 内容列表

        Returns:
            CollectionResult: 成功的采集结果
        """
        return CollectionResult(
            author_name=self.author.name,
            author_url=self.author.url,
            category=self.author.category,
            success=True,
            items=items
        )

    def _create_error_result(self, error_message: str) -> CollectionResult:
        """
        创建失败的采集结果

        Args:
            error_message: 错误信息

        Returns:
            CollectionResult: 失败的采集结果
        """
        return CollectionResult(
            author_name=self.author.name,
            author_url=self.author.url,
            category=self.author.category,
            success=False,
            error_message=error_message
        )

    def _fetch_url(self, url: str) -> Optional[requests.Response]:
        """
        获取URL内容

        Args:
            url: 目标URL

        Returns:
            Response对象，失败返回None
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"请求失败 {url}: {e}")
            return None

    def _is_within_days(self, publish_date: datetime, days: int = 1) -> bool:
        """
        判断发布时间是否在指定天数内

        Args:
            publish_date: 发布时间
            days: 天数

        Returns:
            bool: 是否在指定天数内
        """
        if not publish_date:
            return False

        now = datetime.now()
        delta = now - publish_date
        return delta.days < days

    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(author='{self.author.name}', category={self.author.category.value})"
