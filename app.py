"""
Web 应用主程序
使用 Flask 展示采集的内容
"""
from flask import Flask, render_template, jsonify
from pathlib import Path
from datetime import datetime
from data_storage import DataStorage
from config_manager import CategoryType

app = Flask(__name__)

# 数据存储管理器
storage = DataStorage()


def load_latest_data():
    """
    加载并合并采集数据

    策略：
    1. 加载最新的 collection 文件作为基础
    2. 对于失败的作者，尝试从历史 collection 文件中加载他们的数据
    3. 合并所有成功的数据，确保每个作者都有内容显示
    """
    # 获取所有 collection_*.json 文件（完整的采集结果）
    collection_files = storage.list_saved_files(pattern="collection_*.json")

    if not collection_files:
        return None

    # 加载最新的 collection 文件
    latest_file = collection_files[0]
    latest_data = storage.load_results(latest_file.name)

    if not latest_data:
        return None

    # 获取最新数据中失败的作者列表
    failed_authors = set()
    successful_authors = set()

    for result in latest_data.get('results', []):
        if not result.get('success'):
            failed_authors.add(result.get('author_name'))
        else:
            successful_authors.add(result.get('author_name'))

    # 如果有失败的作者，尝试从历史数据中加载
    if failed_authors:
        # 遍历历史 collection 文件（从第二个开始）
        for old_file in collection_files[1:]:
            if not failed_authors:  # 所有失败的作者都找到了历史数据
                break

            old_data = storage.load_results(old_file.name)
            if not old_data:
                continue

            # 查找失败作者的历史成功数据
            for result in old_data.get('results', []):
                author_name = result.get('author_name')
                if author_name in failed_authors and result.get('success'):
                    # 找到了历史成功数据，添加到最新数据中
                    # 先移除失败的条目
                    latest_data['results'] = [
                        r for r in latest_data['results']
                        if r.get('author_name') != author_name
                    ]
                    # 添加历史成功数据（标记为来自历史）
                    result['from_history'] = True
                    result['history_collected_at'] = old_data.get('collected_at')
                    latest_data['results'].append(result)

                    # 更新统计
                    latest_data['successful_authors'] = latest_data.get('successful_authors', 0) + 1
                    latest_data['failed_authors'] = latest_data.get('failed_authors', 0) - 1
                    latest_data['total_items'] = latest_data.get('total_items', 0) + len(result.get('items', []))

                    # 从失败列表中移除
                    failed_authors.remove(author_name)
                    successful_authors.add(author_name)

    return latest_data


def format_publish_date(date_str):
    """格式化发布时间"""
    if not date_str:
        return "未知时间"

    try:
        dt = datetime.fromisoformat(date_str)
        now = datetime.now()
        delta = now - dt

        if delta.days == 0:
            if delta.seconds < 3600:
                minutes = delta.seconds // 60
                return f"{minutes} 分钟前"
            else:
                hours = delta.seconds // 3600
                return f"{hours} 小时前"
        elif delta.days == 1:
            return "昨天"
        elif delta.days < 7:
            return f"{delta.days} 天前"
        else:
            return dt.strftime("%Y-%m-%d")
    except:
        return "未知时间"


@app.route('/')
def index():
    """首页"""
    data = load_latest_data()

    if not data:
        return render_template('index.html',
                               collected_at="暂无数据",
                               categories=[],
                               items=[],
                               total_items=0)

    # 整理数据
    all_items = []
    for result in data.get('results', []):
        if result.get('success'):
            for item in result.get('items', []):
                # 添加格式化的发布时间
                item['formatted_date'] = format_publish_date(item.get('publish_date'))
                all_items.append(item)

    # 按发布时间排序（最新的在前）
    all_items.sort(key=lambda x: x.get('publish_date', ''), reverse=True)

    # 统计分类
    categories = {
        'Video': {'name': 'Video', 'count': 0, 'icon': '🎥'},
        'Podcast': {'name': 'Podcast', 'count': 0, 'icon': '🎙️'},
        'News': {'name': 'News', 'count': 0, 'icon': '📰'}
    }

    for item in all_items:
        category = item.get('category')
        if category in categories:
            categories[category]['count'] += 1

    # 格式化采集时间
    collected_at = data.get('collected_at', '')
    if collected_at:
        try:
            dt = datetime.fromisoformat(collected_at)
            collected_at = dt.strftime("%Y年%m月%d日 %H:%M")
        except:
            pass

    return render_template('index.html',
                           collected_at=collected_at,
                           categories=list(categories.values()),
                           items=all_items,
                           total_items=len(all_items))


@app.route('/api/items')
def api_items():
    """API: 获取所有内容"""
    data = load_latest_data()

    if not data:
        return jsonify({'items': [], 'total': 0})

    all_items = []
    for result in data.get('results', []):
        if result.get('success'):
            for item in result.get('items', []):
                item['formatted_date'] = format_publish_date(item.get('publish_date'))
                all_items.append(item)

    # 按发布时间排序
    all_items.sort(key=lambda x: x.get('publish_date', ''), reverse=True)

    return jsonify({'items': all_items, 'total': len(all_items)})


@app.route('/api/items/<category>')
def api_items_by_category(category):
    """API: 按分类获取内容"""
    data = load_latest_data()

    if not data:
        return jsonify({'items': [], 'total': 0})

    filtered_items = []
    for result in data.get('results', []):
        if result.get('success') and result.get('category') == category:
            for item in result.get('items', []):
                item['formatted_date'] = format_publish_date(item.get('publish_date'))
                filtered_items.append(item)

    # 按发布时间排序
    filtered_items.sort(key=lambda x: x.get('publish_date', ''), reverse=True)

    return jsonify({'items': filtered_items, 'total': len(filtered_items)})


@app.template_filter('truncate_desc')
def truncate_desc(text, length=150):
    """截断描述文本"""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length] + "..."


if __name__ == '__main__':
    print("=" * 60)
    print("知桥 C4 - AI News 展示系统")
    print("=" * 60)
    print("\n服务器启动中...")
    print("访问地址: http://127.0.0.1:8080")
    print("按 Ctrl+C 停止服务器\n")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=8080)
