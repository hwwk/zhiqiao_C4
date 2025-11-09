"""
快速测试新采集器
"""
from config_manager import ConfigManager, Author, CategoryType
from podcast_collector import PodcastCollector
from news_collector import NewsCollector

# 测试 Podcast 采集器
print("=" * 60)
print("测试 Podcast 采集器")
print("=" * 60)
podcast_author = Author(
    name="Lex Fridman Podcast",
    url="https://lexfridman.com/podcast/",
    category=CategoryType.PODCAST,
    enabled=True
)
podcast_collector = PodcastCollector(podcast_author)
print(f"RSS URL: {podcast_collector.rss_url}")
result = podcast_collector.collect(max_items=5)
print(f"Success: {result.success}")
if result.success:
    print(f"Items collected: {len(result.items)}")
    for item in result.items[:2]:
        print(f"  - {item.title}")
else:
    print(f"Error: {result.error_message}")

print("\n" + "=" * 60)
print("测试 News 采集器")
print("=" * 60)
news_author = Author(
    name="Simon Willison's Blog",
    url="https://simonwillison.net/",
    category=CategoryType.NEWS,
    enabled=True
)
news_collector = NewsCollector(news_author)
print(f"Feed URL: {news_collector.feed_url}")
result = news_collector.collect(max_items=5)
print(f"Success: {result.success}")
if result.success:
    print(f"Items collected: {len(result.items)}")
    for item in result.items[:2]:
        print(f"  - {item.title}")
else:
    print(f"Error: {result.error_message}")
