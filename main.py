"""
主程序
演示配置文件的读取和使用
"""
from config_manager import ConfigManager, CategoryType


def main():
    """主函数"""
    print("=" * 60)
    print("知桥 C4 - 配置管理系统")
    print("=" * 60)

    # 创建配置管理器并加载配置
    config = ConfigManager()

    try:
        print("\n正在加载配置文件...")
        config.load()
        print(f"✓ 配置加载成功！")
        print(f"  - 共有 {len(config.authors)} 个作者")
        print(f"  - 启用 {len(config.get_enabled_authors())} 个作者")

    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        return
    except Exception as e:
        print(f"✗ 加载配置失败: {e}")
        return

    # 显示全局设置
    print("\n" + "-" * 60)
    print("全局设置:")
    print(f"  - 检查间隔: {config.settings.check_interval_minutes} 分钟")
    print(f"  - 每个作者最大条目数: {config.settings.max_items_per_author}")

    # 显示所有作者信息
    print("\n" + "-" * 60)
    print("所有作者列表:")
    print("-" * 60)

    for idx, author in enumerate(config.authors, 1):
        status = "✓ 启用" if author.enabled else "✗ 禁用"
        print(f"\n{idx}. {author.name}")
        print(f"   状态: {status}")
        print(f"   分类: {author.category.value}")
        print(f"   链接: {author.url}")

    # 按分类显示作者
    print("\n" + "=" * 60)
    print("按分类显示启用的作者:")
    print("=" * 60)

    for category in CategoryType:
        authors_in_category = config.get_authors_by_category(category)
        print(f"\n【{category.value}】({len(authors_in_category)} 个)")
        if authors_in_category:
            for author in authors_in_category:
                print(f"  - {author.name}")
                print(f"    {author.url}")
        else:
            print(f"  (暂无)")

    # 演示添加新作者
    print("\n" + "=" * 60)
    print("演示：添加新作者")
    print("=" * 60)

    new_author = config.add_author(
        name="示例新作者",
        url="https://example.com/new-author",
        category=CategoryType.VIDEO,
        enabled=True
    )
    print(f"✓ 已添加新作者: {new_author.name}")

    # 保存配置（可选，取消注释以启用）
    # print("\n正在保存配置...")
    # config.save()
    # print("✓ 配置已保存")

    print("\n" + "=" * 60)
    print("程序运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
