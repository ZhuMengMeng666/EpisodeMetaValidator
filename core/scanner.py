import re
from pathlib import Path
from config import IGNORE_FOLDER_NAMES
from core.processor import process_tv_show, process_movie


def scan_library(root_dir, summary):
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"\n❌ 错误: 路径不存在跳过扫描 -> {root_dir}")
        return

    print(f"\n" + "=" * 60)
    print(f"🚀 正在扫描目录: {root_dir}")
    print("=" * 60)

    for item in root_path.iterdir():
        if not item.is_dir(): continue

        folder_name = item.name

        if folder_name in IGNORE_FOLDER_NAMES:
            print(f"⏭️ [跳过扫描] 命中忽略规则: {folder_name}")
            summary["ignored"].append(f"🚫 [用户跳过] {folder_name} (位于 {root_path.name})")
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
                summary["ignored"].append(f"📂 [结构错误剧集] {folder_name} (位于 {root_path.name})")
            else:
                process_tv_show(title, season_folders, summary)
        else:
            process_movie(item, folder_name, summary)