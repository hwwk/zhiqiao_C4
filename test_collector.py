"""
采集功能测试文件
测试内容采集、数据存储等功能
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from config_manager import ConfigManager, Author, CategoryType
from content_model import ContentItem, CollectionResult
from collector_manager import CollectorManager
from data_storage import DataStorage
from youtube_collector import YouTubeCollector


class TestContentItem:
    """测试 ContentItem 数据类"""

    def test_create_valid_content_item(self):
        """测试创建有效的内容项"""
        item = ContentItem(
            title="Test Video",
            url="https://youtube.com/watch?v=test123",
            author_name="Test Author",
            author_url="https://youtube.com/@test",
            category=CategoryType.VIDEO,
            description="Test description",
            thumbnail_url="https://example.com/thumb.jpg"
        )

        assert item.title == "Test Video"
        assert item.url == "https://youtube.com/watch?v=test123"
        assert item.category == CategoryType.VIDEO

    def test_content_item_invalid_title(self):
        """测试空标题应抛出异常"""
        with pytest.raises(ValueError, match="标题不能为空"):
            ContentItem(
                title="",
                url="https://example.com",
                author_name="Test",
                author_url="https://example.com",
                category=CategoryType.VIDEO
            )

    def test_content_item_invalid_url(self):
        """测试无效URL应抛出异常"""
        with pytest.raises(ValueError, match="无效的内容URL"):
            ContentItem(
                title="Test",
                url="invalid-url",
                author_name="Test",
                author_url="https://example.com",
                category=CategoryType.VIDEO
            )

    def test_content_item_to_dict(self):
        """测试转换为字典"""
        item = ContentItem(
            title="Test",
            url="https://example.com/video",
            author_name="Author",
            author_url="https://example.com",
            category=CategoryType.PODCAST
        )

        data = item.to_dict()
        assert data['title'] == "Test"
        assert data['category'] == "Podcast"
        assert 'collected_at' in data

    def test_content_item_from_dict(self):
        """测试从字典创建对象"""
        data = {
            'title': 'Test Video',
            'url': 'https://example.com/video',
            'author_name': 'Test Author',
            'author_url': 'https://example.com',
            'category': 'Video',
            'publish_date': '2025-11-10T10:00:00',
            'collected_at': '2025-11-10T11:00:00'
        }

        item = ContentItem.from_dict(data)
        assert item.title == 'Test Video'
        assert item.category == CategoryType.VIDEO
        assert isinstance(item.publish_date, datetime)

    def test_is_today(self):
        """测试判断是否是今天发布"""
        # 今天的内容
        today_item = ContentItem(
            title="Today",
            url="https://example.com/1",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            publish_date=datetime.now()
        )
        assert today_item.is_today() is True

        # 昨天的内容
        yesterday_item = ContentItem(
            title="Yesterday",
            url="https://example.com/2",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            publish_date=datetime.now() - timedelta(days=1)
        )
        assert yesterday_item.is_today() is False

    def test_get_primary_image(self):
        """测试获取主要图片"""
        # 有缩略图
        item1 = ContentItem(
            title="Test",
            url="https://example.com",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            thumbnail_url="https://example.com/thumb.jpg"
        )
        assert item1.get_primary_image() == "https://example.com/thumb.jpg"

        # 只有封面图
        item2 = ContentItem(
            title="Test",
            url="https://example.com",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.NEWS,
            cover_image_url="https://example.com/cover.jpg"
        )
        assert item2.get_primary_image() == "https://example.com/cover.jpg"


class TestCollectionResult:
    """测试 CollectionResult 数据类"""

    def test_create_collection_result(self):
        """测试创建采集结果"""
        result = CollectionResult(
            author_name="Test Author",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            success=True
        )

        assert result.success is True
        assert len(result.items) == 0

    def test_collection_result_to_dict(self):
        """测试转换为字典"""
        result = CollectionResult(
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.PODCAST,
            success=True
        )

        data = result.to_dict()
        assert data['author_name'] == "Test"
        assert data['success'] is True
        assert data['total_items'] == 0

    def test_get_today_items(self):
        """测试获取今天的内容"""
        today_item = ContentItem(
            title="Today",
            url="https://example.com/1",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            publish_date=datetime.now()
        )

        old_item = ContentItem(
            title="Old",
            url="https://example.com/2",
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            publish_date=datetime.now() - timedelta(days=5)
        )

        result = CollectionResult(
            author_name="Test",
            author_url="https://example.com",
            category=CategoryType.VIDEO,
            success=True,
            items=[today_item, old_item]
        )

        today_items = result.get_today_items()
        assert len(today_items) == 1
        assert today_items[0].title == "Today"


class TestDataStorage:
    """测试数据存储功能"""

    @pytest.fixture
    def temp_storage_dir(self):
        """创建临时存储目录"""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        # 清理
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_results(self):
        """创建示例采集结果"""
        item1 = ContentItem(
            title="Test Video 1",
            url="https://example.com/1",
            author_name="Author 1",
            author_url="https://example.com/author1",
            category=CategoryType.VIDEO,
            publish_date=datetime.now()
        )

        item2 = ContentItem(
            title="Test Video 2",
            url="https://example.com/2",
            author_name="Author 1",
            author_url="https://example.com/author1",
            category=CategoryType.VIDEO,
            publish_date=datetime.now() - timedelta(days=1)
        )

        result = CollectionResult(
            author_name="Author 1",
            author_url="https://example.com/author1",
            category=CategoryType.VIDEO,
            success=True,
            items=[item1, item2]
        )

        return [result]

    def test_save_results(self, temp_storage_dir, sample_results):
        """测试保存采集结果"""
        storage = DataStorage(storage_dir=temp_storage_dir)
        filepath = storage.save_results(sample_results, filename="test_results.json")

        assert filepath.exists()
        assert filepath.name == "test_results.json"

        # 验证文件内容
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['total_authors'] == 1
        assert data['total_items'] == 2
        assert len(data['results']) == 1

    def test_save_today_items_only(self, temp_storage_dir, sample_results):
        """测试只保存今天的内容"""
        storage = DataStorage(storage_dir=temp_storage_dir)
        filepath = storage.save_today_items_only(sample_results, filename="test_today.json")

        assert filepath.exists()

        # 验证只有今天的内容
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data['total_items'] == 1  # 只有今天的1条

    def test_load_results(self, temp_storage_dir, sample_results):
        """测试加载采集结果"""
        storage = DataStorage(storage_dir=temp_storage_dir)

        # 先保存
        filepath = storage.save_results(sample_results, filename="test_load.json")

        # 再加载
        loaded_data = storage.load_results("test_load.json")

        assert loaded_data is not None
        assert loaded_data['total_authors'] == 1

    def test_list_saved_files(self, temp_storage_dir, sample_results):
        """测试列出保存的文件"""
        storage = DataStorage(storage_dir=temp_storage_dir)

        # 保存多个文件
        storage.save_results(sample_results, filename="file1.json")
        storage.save_results(sample_results, filename="file2.json")

        files = storage.list_saved_files()
        assert len(files) >= 2

    def test_get_latest_file(self, temp_storage_dir, sample_results):
        """测试获取最新文件"""
        storage = DataStorage(storage_dir=temp_storage_dir)

        storage.save_results(sample_results, filename="old.json")
        import time
        time.sleep(0.1)
        storage.save_results(sample_results, filename="new.json")

        latest = storage.get_latest_file()
        assert latest is not None
        assert latest.name == "new.json"

    def test_create_summary_report(self, sample_results):
        """测试创建摘要报告"""
        storage = DataStorage()
        report = storage.create_summary_report(sample_results)

        assert 'summary' in report
        assert report['summary']['total_authors'] == 1
        assert report['summary']['total_items'] == 2
        assert report['summary']['today_items'] == 1


class TestYouTubeCollector:
    """测试 YouTube 采集器"""

    def test_create_youtube_collector(self):
        """测试创建 YouTube 采集器"""
        author = Author(
            name="Test Channel",
            url="https://www.youtube.com/@PatrickOakleyEllis",
            category=CategoryType.VIDEO
        )

        collector = YouTubeCollector(author)
        assert collector is not None
        assert collector.author.name == "Test Channel"

    def test_extract_video_id(self):
        """测试提取视频ID"""
        author = Author(
            name="Test",
            url="https://www.youtube.com/@test",
            category=CategoryType.VIDEO
        )

        collector = YouTubeCollector(author)

        # 测试不同格式的URL
        video_id1 = collector._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id1 == "dQw4w9WgXcQ"

        video_id2 = collector._extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        assert video_id2 == "dQw4w9WgXcQ"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
