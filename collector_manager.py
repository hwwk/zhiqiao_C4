"""
采集管理器
统一管理所有内容采集器
"""
from typing import List, Dict
from datetime import datetime

from config_manager import ConfigManager, Author
from content_model import CollectionResult
from youtube_collector import create_collector
from base_collector import BaseCollector


class CollectorManager:
    """采集管理器"""

    def __init__(self, config_manager: ConfigManager):
        """
        初始化采集管理器

        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.collectors: Dict[str, BaseCollector] = {}
        self._initialize_collectors()

    def _initialize_collectors(self):
        """根据配置初始化所有采集器"""
        enabled_authors = self.config_manager.get_enabled_authors()

        for author in enabled_authors:
            collector = create_collector(author)
            if collector:
                self.collectors[author.name] = collector
            else:
                print(f"警告: 无法为作者 {author.name} 创建采集器")

    def collect_all(self, max_items_per_author: int = None) -> List[CollectionResult]:
        """
        采集所有启用作者的内容

        Args:
            max_items_per_author: 每个作者的最大采集条目数，None则使用配置值

        Returns:
            List[CollectionResult]: 所有采集结果
        """
        if max_items_per_author is None:
            max_items_per_author = self.config_manager.settings.max_items_per_author

        results = []
        total = len(self.collectors)

        print(f"\n开始采集，共 {total} 个作者...")
        print("=" * 60)

        for idx, (author_name, collector) in enumerate(self.collectors.items(), 1):
            print(f"\n[{idx}/{total}] 正在采集: {author_name}")
            print(f"  URL: {collector.author.url}")
            print(f"  分类: {collector.author.category.value}")

            try:
                result = collector.collect(max_items=max_items_per_author)
                results.append(result)

                if result.success:
                    print(f"  ✓ 成功采集 {len(result.items)} 条内容")
                    today_items = result.get_today_items()
                    if today_items:
                        print(f"  📅 今天发布: {len(today_items)} 条")
                else:
                    print(f"  ✗ 采集失败: {result.error_message}")

            except Exception as e:
                print(f"  ✗ 采集异常: {e}")
                # 创建失败结果
                result = CollectionResult(
                    author_name=author_name,
                    author_url=collector.author.url,
                    category=collector.author.category,
                    success=False,
                    error_message=str(e)
                )
                results.append(result)

        print("\n" + "=" * 60)
        print(f"采集完成！")
        self._print_summary(results)

        return results

    def collect_today_only(self, max_items_per_author: int = None) -> List[CollectionResult]:
        """
        只采集今天发布的内容

        Args:
            max_items_per_author: 每个作者的最大采集条目数

        Returns:
            List[CollectionResult]: 只包含今天发布内容的采集结果
        """
        if max_items_per_author is None:
            max_items_per_author = self.config_manager.settings.max_items_per_author

        results = []
        total = len(self.collectors)

        print(f"\n开始采集今天的内容，共 {total} 个作者...")
        print("=" * 60)

        for idx, (author_name, collector) in enumerate(self.collectors.items(), 1):
            print(f"\n[{idx}/{total}] 正在采集: {author_name}")

            try:
                result = collector.collect_today_only(max_items=max_items_per_author)
                results.append(result)

                if result.success:
                    if result.items:
                        print(f"  ✓ 今天发布: {len(result.items)} 条")
                    else:
                        print(f"  - 今天没有新内容")
                else:
                    print(f"  ✗ 采集失败: {result.error_message}")

            except Exception as e:
                print(f"  ✗ 采集异常: {e}")
                result = CollectionResult(
                    author_name=author_name,
                    author_url=collector.author.url,
                    category=collector.author.category,
                    success=False,
                    error_message=str(e)
                )
                results.append(result)

        print("\n" + "=" * 60)
        print(f"采集完成！")
        self._print_summary(results)

        return results

    def collect_by_author(self, author_name: str, max_items: int = None) -> CollectionResult:
        """
        采集指定作者的内容

        Args:
            author_name: 作者名称
            max_items: 最大采集条目数

        Returns:
            CollectionResult: 采集结果
        """
        if max_items is None:
            max_items = self.config_manager.settings.max_items_per_author

        if author_name not in self.collectors:
            # 返回错误结果
            return CollectionResult(
                author_name=author_name,
                author_url="",
                category=None,
                success=False,
                error_message=f"未找到作者: {author_name}"
            )

        collector = self.collectors[author_name]
        return collector.collect(max_items=max_items)

    def _print_summary(self, results: List[CollectionResult]):
        """
        打印采集汇总信息

        Args:
            results: 采集结果列表
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_items = sum(len(r.items) for r in successful)
        total_today = sum(len(r.get_today_items()) for r in successful)

        print(f"\n采集汇总:")
        print(f"  - 成功: {len(successful)}/{len(results)} 个作者")
        print(f"  - 失败: {len(failed)}/{len(results)} 个作者")
        print(f"  - 总内容: {total_items} 条")
        print(f"  - 今天发布: {total_today} 条")

        if failed:
            print(f"\n失败的作者:")
            for result in failed:
                print(f"  - {result.author_name}: {result.error_message}")

    def get_collector_count(self) -> int:
        """获取采集器数量"""
        return len(self.collectors)

    def __repr__(self) -> str:
        """字符串表示"""
        return f"CollectorManager(collectors={len(self.collectors)})"
