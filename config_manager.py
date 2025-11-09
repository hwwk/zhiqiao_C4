"""
配置管理模块
负责读取和验证 config.json 文件
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class CategoryType(Enum):
    """内容分类枚举"""
    PODCAST = "Podcast"
    VIDEO = "Video"
    NEWS = "News"


@dataclass
class Author:
    """作者配置数据类"""
    name: str
    url: str
    category: CategoryType
    enabled: bool = True

    def __post_init__(self):
        """验证数据"""
        if not self.name or not self.name.strip():
            raise ValueError("作者名称不能为空")
        if not self.url or not self.url.startswith(("http://", "https://")):
            raise ValueError(f"无效的URL: {self.url}")
        if isinstance(self.category, str):
            self.category = CategoryType(self.category)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "url": self.url,
            "category": self.category.value,
            "enabled": self.enabled
        }


@dataclass
class Settings:
    """全局设置数据类"""
    check_interval_minutes: int = 60
    max_items_per_author: int = 10

    def __post_init__(self):
        """验证数据"""
        if self.check_interval_minutes <= 0:
            raise ValueError("检查间隔必须大于0")
        if self.max_items_per_author <= 0:
            raise ValueError("每个作者的最大条目数必须大于0")


class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为项目根目录的 config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.authors: List[Author] = []
        self.settings: Settings = Settings()

    def load(self) -> bool:
        """
        加载配置文件

        Returns:
            bool: 加载成功返回True，否则返回False

        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON格式错误
            ValueError: 配置数据验证失败
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # 加载设置
        if "settings" in config_data:
            self.settings = Settings(**config_data["settings"])

        # 加载作者列表
        if "authors" not in config_data:
            raise ValueError("配置文件缺少 'authors' 字段")

        self.authors = []
        for author_data in config_data["authors"]:
            try:
                author = Author(**author_data)
                self.authors.append(author)
            except Exception as e:
                print(f"警告: 跳过无效的作者配置 {author_data.get('name', 'Unknown')}: {e}")
                continue

        if not self.authors:
            raise ValueError("配置文件中没有有效的作者")

        return True

    def get_enabled_authors(self) -> List[Author]:
        """
        获取所有启用的作者

        Returns:
            List[Author]: 启用的作者列表
        """
        return [author for author in self.authors if author.enabled]

    def get_authors_by_category(self, category: CategoryType) -> List[Author]:
        """
        根据分类获取作者

        Args:
            category: 分类类型

        Returns:
            List[Author]: 指定分类的作者列表
        """
        return [author for author in self.authors if author.category == category and author.enabled]

    def save(self) -> bool:
        """
        保存配置到文件

        Returns:
            bool: 保存成功返回True
        """
        config_data = {
            "authors": [author.to_dict() for author in self.authors],
            "settings": {
                "check_interval_minutes": self.settings.check_interval_minutes,
                "max_items_per_author": self.settings.max_items_per_author
            }
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        return True

    def add_author(self, name: str, url: str, category: CategoryType, enabled: bool = True) -> Author:
        """
        添加新作者

        Args:
            name: 作者名称
            url: 作者主页链接
            category: 分类
            enabled: 是否启用

        Returns:
            Author: 新添加的作者对象
        """
        author = Author(name=name, url=url, category=category, enabled=enabled)
        self.authors.append(author)
        return author

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ConfigManager(authors={len(self.authors)}, enabled={len(self.get_enabled_authors())})"
