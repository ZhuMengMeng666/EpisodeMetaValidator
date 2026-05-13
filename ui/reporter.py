def print_summary_report(summary):
    print("\n\n" + "★" * 60)
    print(" " * 18 + "📊 跨目录最终刮削质检报告 📊")
    print("★" * 60)

    print(f"\n✅ 【完美无瑕】 (共 {len(summary['perfect'])} 部/季):")
    if not summary['perfect']:
        print("   （无完美数据，革命尚未成功）")
    for item in summary['perfect']:
        print(f"   ✔️ {item}")

    print(f"\n❌ 【需要修复】 (共 {len(summary['errors'])} 部/季):")
    if not summary['errors']:
        print("   （太棒了！未发现任何刮削问题）")
    for err_group in summary['errors']:
        print(f"   ⚠️ {err_group['target']}")
        for issue in err_group['issues']:
            print(f"       └─ {issue}")

    if summary['ignored']:
        print(f"\n👻 【忽略/异常目录】 (共 {len(summary['ignored'])} 个):")
        for item in summary['ignored']:
            print(f"   - {item}")

    print("\n" + "★" * 60)