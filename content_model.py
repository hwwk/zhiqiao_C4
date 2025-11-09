"""
内容数据模型
定义采集内容的数据结构
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict
from config_manager import CategoryType


@dataclass
class ContentItem:
    """内容项数据类"""

    # 基本信息
    title: str  # 标题
    url: str  # 内容链接
    author_name: str  # 作者名称
    author_url: str  # 作者主页链接
    category: CategoryType  # 分类

    # 内容详情
    description: str = ""  # 简介/摘要
    publish_date: Optional[datetime] = None  # 发布时间

    # 媒体资源
    thumbnail_url: Optional[str] = None  # 缩略图/封面图 URL
    cover_image_url: Optional[str] = None  # 文章配图/封面 URL
    images: List[str] = field(default_factory=list)  # 其他图片列表

    # 元数据
    duration: Optional[str] = None  # 视频/音频时长
    views: Optional[int] = None  # 观看/阅读次数
    tags: List[str] = field(default_factory=list)  # 标签

    # 采集信息
    collected_at: datetime = field(default_factory=datetime.now)  # 采集时间
    content_id: Optional[str] = None  # 内容唯一标识

    def __post_init__(self):
        """验证数据"""
        if not self.title or not self.title.strip():
            raise ValueError("标题不能为空")
        if not self.url or not self.url.startswith(("http://", "https://")):
            raise ValueError(f"无效的内容URL: {self.url}")
        if not self.author_name or not self.author_name.strip():
            raise ValueError("作者名称不能为空")

        # 确保 category 是 CategoryType 枚举
        if isinstance(self.category, str):
            self.category = CategoryType(self.category)

    def to_dict(self) -> Dict:
        """转换为字典，用于 JSON 序列化"""
        data = asdict(self)

        # 转换枚举为字符串
        data['category'] = self.category.value

        # 转换 datetime 为 ISO 格式字符串
        if self.publish_date:
            data['publish_date'] = self.publish_date.isoformat()

        if self.collected_at:
            data['collected_at'] = self.collected_at.isoformat()

        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentItem':
        """从字典创建对象"""
        # 复制数据避免修改原始字典
        data = data.copy()

        # 转换字符串为枚举
        if 'category' in data and isinstance(data['category'], str):
            data['category'] = CategoryType(data['category'])

        # 转换 ISO 格式字符串为 datetime
        if 'publish_date' in data and isinstance(data['publish_date'], str):
            data['publish_date'] = datetime.fromisoformat(data['publish_date'])

        if 'collected_at' in data and isinstance(data['collected_at'], str):
            data['collected_at'] = datetime.fromisoformat(data['collected_at'])

        return cls(**data)

    def is_today(self) -> bool:
        """判断是否是今天发布的内容"""
        if not self.publish_date:
            return False

        today = datetime.now().date()
        return self.publish_date.date() == today

    def get_primary_image(self) -> Optional[str]:
        """获取主要图片（优先缩略图，其次封面图）"""
        return self.thumbnail_url or self.cover_image_url

    def __repr__(self) -> str:
        """字符串表示"""
        return f"ContentItem(title='{self.title[:30]}...', author='{self.author_name}', category={self.category.value})"


@dataclass
class CollectionResult:
    """采集结果数据类"""

    author_name: str  # 作者名称
    author_url: str  # 作者主页
    category: CategoryType  # 分类
    success: bool  # 是否成功
    items: List[ContentItem] = field(default_factory=list)  # 采集到的内容列表
    error_message: Optional[str] = None  # 错误信息
    collected_at: datetime = field(default_factory=datetime.now)  # 采集时间

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'author_name': self.author_name,
            'author_url': self.author_url,
            'category': self.category.value,
            'success': self.success,
            'items': [item.to_dict() for item in self.items],
            'error_message': self.error_message,
            'collected_at': self.collected_at.isoformat(),
            'total_items': len(self.items)
        }

    def get_today_items(self) -> List[ContentItem]:
        """获取今天发布的内容"""
        return [item for item in self.items if item.is_today()]

    def __repr__(self) -> str:
        """字符串表示"""
        status = "成功" if self.success else "失败"
        return f"CollectionResult(author='{self.author_name}', status={status}, items={len(self.items)})"
