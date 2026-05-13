from config import TARGET_DIRECTORIES
from core.scanner import scan_library
from ui.reporter import print_summary_report


def main():
    # 初始化全局大盘点字典
    global_summary = {
        "perfect": [],
        "errors": [],
        "ignored": []
    }

    # 循环扫描所有配置的目录
    for directory in TARGET_DIRECTORIES:
        scan_library(directory, global_summary)

    # 扫描完毕，渲染报告
    print_summary_report(global_summary)


if __name__ == "__main__":
    main()