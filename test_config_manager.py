"""
配置管理器测试文件
"""
import pytest
import json
import tempfile
from pathlib import Path
from config_manager import ConfigManager, Author, CategoryType, Settings


class TestAuthor:
    """测试 Author 数据类"""

    def test_create_valid_author(self):
        """测试创建有效的作者"""
        author = Author(
            name="Test Author",
            url="https://example.com",
            category=CategoryType.VIDEO,
            enabled=True
        )
        assert author.name == "Test Author"
        assert author.url == "https://example.com"
        assert author.category == CategoryType.VIDEO
        assert author.enabled is True

    def test_author_with_string_category(self):
        """测试使用字符串创建作者（自动转换为枚举）"""
        author = Author(
            name="Test Author",
            url="https://example.com",
            category="Podcast",
            enabled=True
        )
        assert author.category == CategoryType.PODCAST

    def test_author_invalid_name(self):
        """测试空名称应抛出异常"""
        with pytest.raises(ValueError, match="作者名称不能为空"):
            Author(
                name="",
                url="https://example.com",
                category=CategoryType.VIDEO
            )

    def test_author_invalid_url(self):
        """测试无效URL应抛出异常"""
        with pytest.raises(ValueError, match="无效的URL"):
            Author(
                name="Test Author",
                url="invalid-url",
                category=CategoryType.VIDEO
            )

    def test_author_to_dict(self):
        """测试作者转换为字典"""
        author = Author(
            name="Test Author",
            url="https://example.com",
            category=CategoryType.NEWS,
            enabled=False
        )
        data = author.to_dict()
        assert data["name"] == "Test Author"
        assert data["url"] == "https://example.com"
        assert data["category"] == "News"
        assert data["enabled"] is False


class TestSettings:
    """测试 Settings 数据类"""

    def test_create_valid_settings(self):
        """测试创建有效的设置"""
        settings = Settings(check_interval_minutes=30, max_items_per_author=20)
        assert settings.check_interval_minutes == 30
        assert settings.max_items_per_author == 20

    def test_default_settings(self):
        """测试默认设置值"""
        settings = Settings()
        assert settings.check_interval_minutes == 60
        assert settings.max_items_per_author == 10

    def test_invalid_interval(self):
        """测试无效的检查间隔"""
        with pytest.raises(ValueError, match="检查间隔必须大于0"):
            Settings(check_interval_minutes=0)

    def test_invalid_max_items(self):
        """测试无效的最大条目数"""
        with pytest.raises(ValueError, match="每个作者的最大条目数必须大于0"):
            Settings(max_items_per_author=-1)


class TestConfigManager:
    """测试 ConfigManager 配置管理器"""

    @pytest.fixture
    def sample_config(self):
        """创建示例配置数据"""
        return {
            "authors": [
                {
                    "name": "Author 1",
                    "url": "https://example.com/author1",
                    "category": "Video",
                    "enabled": True
                },
                {
                    "name": "Author 2",
                    "url": "https://example.com/author2",
                    "category": "Podcast",
                    "enabled": True
                },
                {
                    "name": "Author 3",
                    "url": "https://example.com/author3",
                    "category": "News",
                    "enabled": False
                }
            ],
            "settings": {
                "check_interval_minutes": 45,
                "max_items_per_author": 15
            }
        }

    @pytest.fixture
    def temp_config_file(self, sample_config):
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(sample_config, f)
            temp_path = Path(f.name)

        yield temp_path

        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()

    def test_load_config(self, temp_config_file):
        """测试加载配置文件"""
        manager = ConfigManager(config_path=temp_config_file)
        assert manager.load() is True
        assert len(manager.authors) == 3
        assert manager.settings.check_interval_minutes == 45
        assert manager.settings.max_items_per_author == 15

    def test_load_nonexistent_config(self):
        """测试加载不存在的配置文件"""
        manager = ConfigManager(config_path=Path("nonexistent.json"))
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            manager.load()

    def test_get_enabled_authors(self, temp_config_file):
        """测试获取启用的作者"""
        manager = ConfigManager(config_path=temp_config_file)
        manager.load()
        enabled_authors = manager.get_enabled_authors()
        assert len(enabled_authors) == 2
        assert all(author.enabled for author in enabled_authors)

    def test_get_authors_by_category(self, temp_config_file):
        """测试根据分类获取作者"""
        manager = ConfigManager(config_path=temp_config_file)
        manager.load()

        video_authors = manager.get_authors_by_category(CategoryType.VIDEO)
        assert len(video_authors) == 1
        assert video_authors[0].name == "Author 1"

        podcast_authors = manager.get_authors_by_category(CategoryType.PODCAST)
        assert len(podcast_authors) == 1
        assert podcast_authors[0].name == "Author 2"

        # News 作者被禁用了，所以不应该返回
        news_authors = manager.get_authors_by_category(CategoryType.NEWS)
        assert len(news_authors) == 0

    def test_add_author(self, temp_config_file):
        """测试添加新作者"""
        manager = ConfigManager(config_path=temp_config_file)
        manager.load()

        initial_count = len(manager.authors)
        new_author = manager.add_author(
            name="New Author",
            url="https://example.com/new",
            category=CategoryType.VIDEO,
            enabled=True
        )

        assert len(manager.authors) == initial_count + 1
        assert new_author.name == "New Author"
        assert new_author in manager.authors

    def test_save_config(self, temp_config_file):
        """测试保存配置文件"""
        manager = ConfigManager(config_path=temp_config_file)
        manager.load()

        # 添加新作者
        manager.add_author(
            name="Saved Author",
            url="https://example.com/saved",
            category=CategoryType.NEWS,
            enabled=True
        )

        # 保存配置
        assert manager.save() is True

        # 重新加载配置验证保存成功
        manager2 = ConfigManager(config_path=temp_config_file)
        manager2.load()
        assert len(manager2.authors) == 4
        assert any(author.name == "Saved Author" for author in manager2.authors)

    def test_config_manager_repr(self, temp_config_file):
        """测试配置管理器的字符串表示"""
        manager = ConfigManager(config_path=temp_config_file)
        manager.load()
        repr_str = repr(manager)
        assert "ConfigManager" in repr_str
        assert "authors=3" in repr_str
        assert "enabled=2" in repr_str

    def test_load_invalid_json(self):
        """测试加载无效的JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("{invalid json content")
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(config_path=temp_path)
            with pytest.raises(json.JSONDecodeError):
                manager.load()
        finally:
            temp_path.unlink()

    def test_load_config_missing_authors(self):
        """测试加载缺少 authors 字段的配置"""
        config_data = {"settings": {"check_interval_minutes": 60}}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(config_path=temp_path)
            with pytest.raises(ValueError, match="配置文件缺少 'authors' 字段"):
                manager.load()
        finally:
            temp_path.unlink()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
