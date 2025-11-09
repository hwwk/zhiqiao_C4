"""
内容采集演示程序
演示完整的内容采集流程
"""
import sys
from pathlib import Path

from config_manager import ConfigManager
from collector_manager import CollectorManager
from data_storage import DataStorage


def main():
    """主函数"""
    print("=" * 70)
    print("知桥 C4 - 内容采集系统")
    print("=" * 70)

    # 1. 加载配置
    print("\n[步骤 1] 加载配置文件...")
    config = ConfigManager()

    try:
        config.load()
        print(f"✓ 配置加载成功")
        print(f"  - 共有 {len(config.authors)} 个作者")
        print(f"  - 启用 {len(config.get_enabled_authors())} 个作者")
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return

    # 2. 创建采集管理器
    print("\n[步骤 2] 初始化采集管理器...")
    collector_mgr = CollectorManager(config)
    print(f"✓ 已创建 {collector_mgr.get_collector_count()} 个采集器")

    # 显示将要采集的作者
    print("\n将采集以下作者的内容:")
    for author in config.get_enabled_authors():
        print(f"  • {author.name} ({author.category.value})")
        print(f"    {author.url}")

    # 3. 执行采集
    print("\n" + "=" * 70)
    print("[步骤 3] 开始采集内容...")
    print("=" * 70)

    try:
        results = collector_mgr.collect_all()
    except Exception as e:
        print(f"\n✗ 采集过程出错: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. 保存数据
    print("\n" + "=" * 70)
    print("[步骤 4] 保存采集结果...")
    print("=" * 70)

    storage = DataStorage()

    try:
        # 保存完整结果
        filepath = storage.save_results(results)
        print(f"✓ 完整结果已保存: {filepath}")

        # 保存今天的内容
        today_filepath = storage.save_today_items_only(results)
        print(f"✓ 今天的内容已保存: {today_filepath}")

        # 保存摘要报告
        summary_filepath = storage.save_summary_report(results)
        print(f"✓ 摘要报告已保存: {summary_filepath}")

        # 按作者分别保存
        author_files = storage.save_items_by_author(results)
        if author_files:
            print(f"✓ 已按作者保存 {len(author_files)} 个文件")

    except Exception as e:
        print(f"✗ 保存数据失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. 显示详细结果
    print("\n" + "=" * 70)
    print("[步骤 5] 采集结果详情")
    print("=" * 70)

    for result in results:
        print(f"\n作者: {result.author_name}")
        print(f"分类: {result.category.value}")

        if result.success:
            print(f"状态: ✓ 成功")
            print(f"总内容: {len(result.items)} 条")

            today_items = result.get_today_items()
            if today_items:
                print(f"今天发布: {len(today_items)} 条")
                print("\n今天的内容:")
                for idx, item in enumerate(today_items, 1):
                    print(f"  {idx}. {item.title}")
                    print(f"     链接: {item.url}")
                    if item.thumbnail_url:
                        print(f"     缩略图: {item.thumbnail_url}")
                    if item.description:
                        desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
                        print(f"     简介: {desc}")
            else:
                print("今天没有新内容")

            # 显示最近的内容
            if result.items and not today_items:
                print("\n最近的内容:")
                for idx, item in enumerate(result.items[:3], 1):
                    print(f"  {idx}. {item.title}")
                    print(f"     发布时间: {item.publish_date.strftime('%Y-%m-%d %H:%M') if item.publish_date else '未知'}")
                    print(f"     链接: {item.url}")

        else:
            print(f"状态: ✗ 失败")
            print(f"错误: {result.error_message}")

    # 6. 最终汇总
    print("\n" + "=" * 70)
    print("采集完成汇总")
    print("=" * 70)

    successful = [r for r in results if r.success]
    total_items = sum(len(r.items) for r in successful)
    total_today = sum(len(r.get_today_items()) for r in successful)

    print(f"\n✓ 成功: {len(successful)}/{len(results)} 个作者")
    print(f"✓ 总内容: {total_items} 条")
    print(f"✓ 今天发布: {total_today} 条")
    print(f"\n数据已保存到: {storage.storage_dir}")

    # 列出所有保存的文件
    saved_files = storage.list_saved_files()
    if saved_files:
        print(f"\n已保存的文件 (最新的 5 个):")
        for filepath in saved_files[:5]:
            print(f"  • {filepath.name}")

    print("\n" + "=" * 70)
    print("程序运行完成")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
