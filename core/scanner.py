import re
from pathlib import Path
from core.processor import process_tv_show, process_movie


# 🌟 新增了 stop_event 参数用于接收中断信号
def scan_library(root_dir, summary, ignore_folders, pause_event=None, stop_event=None, progress_callback=None):
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"\n❌ 错误: 路径不存在跳过扫描 -> {root_dir}")
        return

    print(f"\n" + "=" * 60)
    print(f"🚀 正在扫描目录: {root_dir}")
    print("=" * 60)

    for item in root_path.iterdir():
        if not item.is_dir(): continue

        # ==================================
        # 🌟 UI 交互核心：暂停拦截与终止拦截
        # ==================================
        if stop_event and stop_event.is_set():
            print(f"\n🛑 [系统] 接收到提前终止指令，正在退出目录: {root_dir}")
            return  # 直接跳出当前目录的扫描

        if pause_event:
            pause_event.wait()  # 如果触发了暂停，线程会在这里静止等待

        if progress_callback:
            progress_callback(item.name)  # 告诉 UI 当前正在扫哪个文件夹

        folder_name = item.name

        if folder_name in ignore_folders:
            print(f"⏭️ [跳过扫描] 命中忽略规则: {folder_name}")
            summary["ignored"].append({"text": f"🚫 [用户跳过] {folder_name}", "path": item})
            continue

        match = re.match(r"^(.*?)(?:\s*\(\d{4}\))?$", folder_name)
        title = match.group(1).strip() if match else folder_name

        has_season = False
        has_tvshow_nfo = False
        season_folders = []

        for sub_item in item.iterdir():
            if sub_item.is_dir() and re.match(r"(?i)^Season\s*\d+", sub_item.name):
                has_season = True
                season_folders.append(sub_item)
            elif sub_item.is_file() and sub_item.name.lower() == 'tvshow.nfo':
                has_tvshow_nfo = True

        if has_season or has_tvshow_nfo:
            if not season_folders:
                print(f"📺 [剧集异常] {folder_name} - 存在 tvshow.nfo，但未找到 Season 文件夹！")
                summary["ignored"].append({"text": f"📂 [结构错误剧集] {folder_name}", "path": item})
            else:
                process_tv_show(title, season_folders, summary)
        else:
            process_movie(item, folder_name, summary)