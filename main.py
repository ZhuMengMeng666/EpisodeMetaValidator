from config import TARGET_DIRECTORIES, HTML_REPORT_DIR
from core.scanner import scan_library
from ui.reporter import print_summary_report, generate_html_report


def main():
    global_summary = {
        "perfect": [],
        "errors": [],
        "ignored": []
    }

    for directory in TARGET_DIRECTORIES:
        scan_library(directory, global_summary)

    # 1. 在终端打印一个简洁的结果
    print_summary_report(global_summary)

    # 2. 生成精美的本地 HTML 看板
    generate_html_report(global_summary, HTML_REPORT_DIR)


if __name__ == "__main__":
    main()