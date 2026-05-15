import re
from pathlib import Path
from core.processor import process_tv_show, process_movie


def is_ignored(item_path, ignore_folders):
    """增强版拦截器：同时支持纯文件夹名匹配、绝对路径匹配，且完全忽略大小写和斜杠差异"""
    # 将当前扫描到的文件夹名和绝对路径都转为小写，并统一斜杠
    name_lower = item_path.name.lower()
    abs_path_lower = str(item_path.resolve()).lower().replace('\\', '/')

    for ig in ignore_folders:
        # 将用户输入的忽略规则也转为小写，并统一斜杠
        ig_lower = ig.lower().replace('\\', '/')

        # 只要“文件夹名”或“完整路径”命中任意一个，立刻拦截
        if name_lower == ig_lower or abs_path_lower == ig_lower:
            return True

    return False


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
        # 1. UI 交互：暂停与终止拦截
        # ==================================
        if stop_event and stop_event.is_set():
            print(f"\n🛑 [系统] 接收到提前终止指令，正在退出目录: {root_dir}")
            return

        if pause_event:
            pause_event.wait()

        if progress_callback:
            progress_callback(item.name)

        # ==================================
        # 2. 核心防御：增强版名单过滤 (绝对在最前面)
        # ==================================
        if is_ignored(item, ignore_folders):
            print(f"⏭️ [跳过扫描] 命中忽略规则: {item.name}")
            summary["ignored"].append({"text": f"🚫 [用户跳过] {item.name}", "path": item})
            continue  # 只要命中，立刻跳出当前循环，绝不执行后续的 NFO 检查！

        # ==================================
        # 3. 开始实质性的结构校验与刮削质检
        # ==================================
        folder_name = item.name
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