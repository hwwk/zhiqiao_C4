"""
数据存储模块
负责将采集的数据保存到JSON文件
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

from content_model import CollectionResult, ContentItem


class DataStorage:
    """数据存储管理器"""

    def __init__(self, storage_dir: Path = None):
        """
        初始化数据存储管理器

        Args:
            storage_dir: 存储目录，默认为当前目录下的 data 文件夹
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent / "data"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_results(self, results: List[CollectionResult], filename: str = None) -> Path:
        """
        保存采集结果到JSON文件

        Args:
            results: 采集结果列表
            filename: 文件名，None则自动生成（格式：collection_YYYYMMDD_HHMMSS.json）

        Returns:
            Path: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"collection_{timestamp}.json"

        # 确保文件名以 .json 结尾
        if not filename.endswith('.json'):
            filename += '.json'

        filepath = self.storage_dir / filename

        # 转换为可序列化的字典
        data = {
            'collected_at': datetime.now().isoformat(),
            'total_authors': len(results),
            'successful_authors': sum(1 for r in results if r.success),
            'failed_authors': sum(1 for r in results if not r.success),
            'total_items': sum(len(r.items) for r in results if r.success),
            'results': [result.to_dict() for result in results]
        }

        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def save_today_items_only(self, results: List[CollectionResult], filename: str = None) -> Path:
        """
        只保存今天发布的内容到JSON文件

        Args:
            results: 采集结果列表
            filename: 文件名，None则自动生成

        Returns:
            Path: 保存的文件路径
        """
        if filename is None:
            today = datetime.now().strftime("%Y%m%d")
            filename = f"today_{today}.json"

        # 筛选今天的内容
        today_results = []
        for result in results:
            if result.success:
                today_items = result.get_today_items()
                if today_items:
                    # 创建新的结果对象，只包含今天的内容
                    from content_model import CollectionResult
                    today_result = CollectionResult(
                        author_name=result.author_name,
                        author_url=result.author_url,
                        category=result.category,
                        success=True,
                        items=today_items,
                        collected_at=result.collected_at
                    )
                    today_results.append(today_result)

        return self.save_results(today_results, filename)

    def save_items_by_author(self, results: List[CollectionResult]) -> Dict[str, Path]:
        """
        按作者分别保存内容到不同的JSON文件

        Args:
            results: 采集结果列表

        Returns:
            Dict[str, Path]: 作者名称到文件路径的映射
        """
        saved_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for result in results:
            if result.success and result.items:
                # 生成安全的文件名
                safe_name = self._sanitize_filename(result.author_name)
                filename = f"{safe_name}_{timestamp}.json"
                filepath = self.storage_dir / filename

                # 保存单个作者的数据
                data = result.to_dict()

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                saved_files[result.author_name] = filepath

        return saved_files

    def load_results(self, filename: str) -> Optional[Dict]:
        """
        从JSON文件加载采集结果

        Args:
            filename: 文件名

        Returns:
            Dict: 采集结果数据，失败返回None
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            print(f"文件不存在: {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"加载文件失败: {e}")
            return None

    def list_saved_files(self, pattern: str = "*.json") -> List[Path]:
        """
        列出所有保存的JSON文件

        Args:
            pattern: 文件匹配模式

        Returns:
            List[Path]: 文件路径列表
        """
        files = sorted(self.storage_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        return files

    def get_latest_file(self) -> Optional[Path]:
        """
        获取最新的JSON文件

        Returns:
            Path: 最新文件路径，没有文件则返回None
        """
        files = self.list_saved_files()
        return files[0] if files else None

    def _sanitize_filename(self, name: str) -> str:
        """
        清理文件名，移除非法字符

        Args:
            name: 原始名称

        Returns:
            str: 安全的文件名
        """
        # 移除或替换非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = name
        for char in illegal_chars:
            sanitized = sanitized.replace(char, '_')

        # 移除前后空格
        sanitized = sanitized.strip()

        # 限制长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]

        return sanitized

    def create_summary_report(self, results: List[CollectionResult]) -> Dict:
        """
        创建采集摘要报告

        Args:
            results: 采集结果列表

        Returns:
            Dict: 摘要报告
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_items = sum(len(r.items) for r in successful)
        total_today = sum(len(r.get_today_items()) for r in successful)

        # 按分类统计
        category_stats = {}
        for result in successful:
            category = result.category.value
            if category not in category_stats:
                category_stats[category] = {'authors': 0, 'items': 0, 'today_items': 0}

            category_stats[category]['authors'] += 1
            category_stats[category]['items'] += len(result.items)
            category_stats[category]['today_items'] += len(result.get_today_items())

        report = {
            'summary': {
                'total_authors': len(results),
                'successful_authors': len(successful),
                'failed_authors': len(failed),
                'total_items': total_items,
                'today_items': total_today,
                'collection_time': datetime.now().isoformat()
            },
            'by_category': category_stats,
            'successful_authors': [r.author_name for r in successful],
            'failed_authors': [
                {'name': r.author_name, 'error': r.error_message}
                for r in failed
            ]
        }

        return report

    def save_summary_report(self, results: List[CollectionResult], filename: str = None) -> Path:
        """
        保存摘要报告

        Args:
            results: 采集结果列表
            filename: 文件名

        Returns:
            Path: 保存的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_{timestamp}.json"

        filepath = self.storage_dir / filename

        report = self.create_summary_report(results)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath

    def __repr__(self) -> str:
        """字符串表示"""
        return f"DataStorage(dir='{self.storage_dir}')"
