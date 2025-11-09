# 知桥 C4 - 多作者内容追踪系统

一个基于配置文件的多作者内容追踪系统，支持 Podcast、Video 和 News 等多种内容类型。自动采集作者主页的最新内容，提取标题、简介、封面图等信息，并保存为 JSON 格式。

## 功能特性

### 配置管理
- ✅ 支持通过 JSON 配置文件管理多个作者
- ✅ 支持三种内容分类：Podcast、Video、News
- ✅ 可以单独启用/禁用每个作者
- ✅ 程序启动时自动读取配置
- ✅ 完整的数据验证和错误处理

### 内容采集
- ✅ 自动采集配置的作者主页链接
- ✅ 提取内容标题、简介、发布时间
- ✅ 获取视频缩略图和文章封面图
- ✅ 支持筛选当天发布的最新内容
- ✅ 采集结果保存为 JSON 文件

### Web 展示
- ✅ 美观的 Web 界面展示采集内容
- ✅ 响应式设计，支持桌面/平板/手机
- ✅ 支持按分类筛选（Video/Podcast/News）
- ✅ 精美的卡片布局和渐变背景
- ✅ 键盘快捷键支持
- ✅ 点击卡片打开原文链接

### 技术特性
- ✅ 使用 uv 管理依赖和虚拟环境
- ✅ 包含 36 个单元测试，覆盖率高
- ✅ 支持 YouTube 频道（通过 RSS Feed）
- ✅ 可扩展的采集器架构，易于添加新平台

## 项目结构

```
zhiqiao_C4/
├── config.json              # 配置文件
├── config_manager.py        # 配置管理模块
├── content_model.py         # 内容数据模型
├── base_collector.py        # 采集器基类
├── youtube_collector.py     # YouTube 采集器
├── collector_manager.py     # 采集管理器
├── data_storage.py          # 数据存储模块
├── main.py                  # 配置演示程序
├── collect_demo.py          # 采集演示程序
├── app.py                   # Web 应用主程序
├── templates/               # HTML 模板目录
│   └── index.html          # 主页模板
├── static/                  # 静态文件目录
│   ├── css/style.css       # 样式文件
│   └── js/main.js          # JavaScript 文件
├── test_config_manager.py   # 配置测试
├── test_collector.py        # 采集测试
├── data/                    # 采集数据存储目录
├── pyproject.toml           # 项目配置
├── README.md                # 本文件
└── WEB_USAGE.md             # Web 功能使用说明
```

## 快速开始

### 1. 安装依赖

使用 uv 安装项目依赖：

```bash
uv sync
```

### 2. 配置作者

编辑 `config.json` 文件，添加您想要追踪的作者：

```json
{
  "authors": [
    {
      "name": "Patrick Oakley Ellis",
      "url": "https://www.youtube.com/@PatrickOakleyEllis",
      "category": "Video",
      "enabled": true
    }
  ],
  "settings": {
    "check_interval_minutes": 60,
    "max_items_per_author": 10
  }
}
```

### 3. 运行程序

查看配置管理功能：
```bash
uv run python main.py
```

运行内容采集：
```bash
uv run python collect_demo.py
```

启动 Web 界面：
```bash
uv run python app.py
```

然后在浏览器访问: [http://127.0.0.1:8080](http://127.0.0.1:8080)

### 4. 运行测试

运行所有测试（36 个测试）：
```bash
uv run pytest test_config_manager.py test_collector.py -v
```

只测试配置管理：
```bash
uv run pytest test_config_manager.py -v
```

只测试内容采集：
```bash
uv run pytest test_collector.py -v
```

## 配置文件说明

### 作者配置

每个作者包含以下字段：

- `name`: 作者名称（必填，不能为空）
- `url`: 作者主页链接（必填，必须以 http:// 或 https:// 开头）
- `category`: 内容分类（必填，可选值：`Podcast`、`Video`、`News`）
- `enabled`: 是否启用（可选，默认为 `true`）

### 全局设置

- `check_interval_minutes`: 检查间隔（分钟），默认 60
- `max_items_per_author`: 每个作者的最大条目数，默认 10

## 使用示例

### 1. 配置管理

```python
from config_manager import ConfigManager, CategoryType

# 创建配置管理器
config = ConfigManager()

# 加载配置文件
config.load()

# 获取所有启用的作者
enabled_authors = config.get_enabled_authors()

# 获取特定分类的作者
video_authors = config.get_authors_by_category(CategoryType.VIDEO)

# 添加新作者
new_author = config.add_author(
    name="新作者",
    url="https://example.com/author",
    category=CategoryType.PODCAST,
    enabled=True
)

# 保存配置
config.save()
```

### 2. 内容采集

```python
from config_manager import ConfigManager
from collector_manager import CollectorManager
from data_storage import DataStorage

# 加载配置
config = ConfigManager()
config.load()

# 创建采集管理器
collector_mgr = CollectorManager(config)

# 采集所有启用作者的内容
results = collector_mgr.collect_all()

# 只采集今天发布的内容
today_results = collector_mgr.collect_today_only()

# 保存结果
storage = DataStorage()
filepath = storage.save_results(results)
print(f"数据已保存到: {filepath}")
```

### 3. 数据存储

```python
from data_storage import DataStorage

storage = DataStorage()

# 保存完整结果
storage.save_results(results)

# 只保存今天的内容
storage.save_today_items_only(results)

# 按作者分别保存
author_files = storage.save_items_by_author(results)

# 保存摘要报告
storage.save_summary_report(results)

# 列出所有保存的文件
saved_files = storage.list_saved_files()

# 获取最新的文件
latest_file = storage.get_latest_file()
```

### 数据验证

配置管理器包含完整的数据验证：

- 作者名称不能为空
- URL 必须是有效的 HTTP/HTTPS 链接
- 分类必须是预定义的三种类型之一
- 检查间隔和最大条目数必须大于 0

## API 文档

### ConfigManager 类

配置管理器，负责加载和管理作者配置。

主要方法：
- `load()`: 加载配置文件
- `save()`: 保存配置到文件
- `get_enabled_authors()`: 获取所有启用的作者
- `get_authors_by_category(category)`: 根据分类获取作者
- `add_author(name, url, category, enabled)`: 添加新作者

### CollectorManager 类

采集管理器，统一管理所有内容采集器。

主要方法：
- `collect_all(max_items_per_author)`: 采集所有启用作者的内容
- `collect_today_only(max_items_per_author)`: 只采集今天发布的内容
- `collect_by_author(author_name, max_items)`: 采集指定作者的内容
- `get_collector_count()`: 获取采集器数量

### DataStorage 类

数据存储管理器，负责保存和加载采集结果。

主要方法：
- `save_results(results, filename)`: 保存采集结果
- `save_today_items_only(results, filename)`: 只保存今天的内容
- `save_items_by_author(results)`: 按作者分别保存
- `save_summary_report(results, filename)`: 保存摘要报告
- `load_results(filename)`: 加载采集结果
- `list_saved_files(pattern)`: 列出保存的文件
- `get_latest_file()`: 获取最新文件

### ContentItem 数据类

内容项数据模型。

主要属性：
- `title`: 标题
- `url`: 内容链接
- `author_name`: 作者名称
- `category`: 分类
- `description`: 简介
- `publish_date`: 发布时间
- `thumbnail_url`: 缩略图 URL
- `cover_image_url`: 封面图 URL

主要方法：
- `to_dict()`: 转换为字典
- `from_dict(data)`: 从字典创建
- `is_today()`: 是否是今天发布
- `get_primary_image()`: 获取主要图片

### CategoryType 枚举

支持的分类：
- `CategoryType.PODCAST`: 播客
- `CategoryType.VIDEO`: 视频
- `CategoryType.NEWS`: 新闻

## 测试覆盖

项目包含 36 个单元测试，覆盖以下方面：

### 配置管理测试（18 个）
- ✅ Author 数据类的创建和验证
- ✅ Settings 数据类的创建和验证
- ✅ 配置文件的加载和保存
- ✅ 作者的筛选和分类
- ✅ 错误处理（无效数据、文件不存在等）

### 内容采集测试（18 个）
- ✅ ContentItem 数据类的创建和验证
- ✅ CollectionResult 数据类的操作
- ✅ YouTube 采集器的功能
- ✅ 数据存储的各种场景
- ✅ 今天内容的筛选
- ✅ 文件的保存和加载

运行所有测试：

```bash
uv run pytest test_config_manager.py test_collector.py -v
```

## 技术栈

### 后端
- **Python 3.12+**: 主要编程语言
- **Flask 3.0+**: Web 框架
- **uv**: 现代化的 Python 依赖管理和虚拟环境工具
- **pytest**: 单元测试框架
- **requests**: HTTP 请求库
- **beautifulsoup4**: HTML 解析库
- **feedparser**: RSS/Atom Feed 解析库
- **lxml**: XML/HTML 处理库
- **python-dateutil**: 日期时间处理库

### 前端
- **HTML5**: 语义化标记
- **CSS3**: Grid + Flexbox 布局，动画效果
- **JavaScript (ES6+)**: 原生 JS，无框架依赖

## 采集数据格式

采集的数据以 JSON 格式保存，包含以下信息：

```json
{
  "collected_at": "2025-11-10T01:32:07",
  "total_authors": 1,
  "successful_authors": 1,
  "total_items": 10,
  "results": [
    {
      "author_name": "Patrick Oakley Ellis",
      "category": "Video",
      "success": true,
      "items": [
        {
          "title": "视频标题",
          "url": "https://youtube.com/watch?v=xxx",
          "description": "视频简介",
          "publish_date": "2025-10-17T21:01:28",
          "thumbnail_url": "https://i.ytimg.com/vi/xxx/hqdefault.jpg",
          "content_id": "xxx"
        }
      ]
    }
  ]
}
```

## 扩展新平台

系统采用可扩展的架构，添加新平台的采集器非常简单：

1. 继承 `BaseCollector` 类
2. 实现 `collect()` 方法
3. 在 `youtube_collector.py` 的 `create_collector()` 函数中添加平台判断

示例：

```python
from base_collector import BaseCollector
from content_model import ContentItem, CollectionResult

class PodcastCollector(BaseCollector):
    def collect(self, max_items=10):
        # 实现具体的采集逻辑
        items = []
        # ... 采集代码 ...
        return self._create_success_result(items)
```

## 开发计划

### 已完成 ✅
- [x] 配置文件管理系统
- [x] YouTube 内容采集
- [x] 数据存储和导出
- [x] 完整的单元测试（36 个）
- [x] Web UI 界面
- [x] 响应式设计
- [x] 分类筛选功能
- [x] 卡片布局和渐变背景

### 待开发 📋
- [ ] 添加 Podcast 平台支持（Apple Podcasts, Spotify）
- [ ] 添加新闻博客平台支持（RSS Feed）
- [ ] 实现定时采集任务
- [ ] 数据去重和增量更新
- [ ] 添加通知功能（有新内容时通知）
- [ ] 支持导出为其他格式（CSV, Markdown）
- [ ] Web 界面实时数据更新（WebSocket）
- [ ] 搜索功能
- [ ] 收藏功能
- [ ] 暗色模式

## Web 展示功能

详细的 Web 功能使用说明请查看 [WEB_USAGE.md](WEB_USAGE.md)

主要特性：
- 📰 精美的卡片式布局
- 🎨 动态渐变背景（无封面图时）
- 🔍 分类筛选功能
- ⌨️ 键盘快捷键支持
- 📱 完全响应式设计
- 🚀 流畅的动画效果

## 许可证

MIT
