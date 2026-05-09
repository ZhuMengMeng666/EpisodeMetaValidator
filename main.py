import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET


# ==========================================
# 1. 核心检查：NFO 内容合法性验证
# ==========================================
def check_nfo_content(nfo_path):
    """
    检查单集 nfo 文件的具体内容，验证 tmdbid 是否合法。
    """
    try:
        # 尝试解析 XML (nfo) 文件
        tree = ET.parse(nfo_path)
        root = tree.getroot()

        # 查找 <tmdbid> 节点
        tmdbid_node = root.find('tmdbid')

        if tmdbid_node is not None:
            # 获取节点内的文本，并去掉首尾空格
            tmdbid_text = tmdbid_node.text

            if tmdbid_text:
                tmdbid_text = tmdbid_text.strip()
                # 核心判断：如果是纯英文字母 (例如 "None")
                if re.match(r"^[a-zA-Z]+$", tmdbid_text):
                    print(f"    └─ ⚠️ [NFO内容非法] {nfo_path.name} : tmdbid 内容为纯英文 '{tmdbid_text}'")
            else:
                # 节点存在但为空
                print(f"    └─ ⚠️ [NFO内容为空] {nfo_path.name} : <tmdbid> 节点无内容")

        else:
            print(f"    └─ ⚠️ [NFO节点缺失] {nfo_path.name} : 未找到 <tmdbid> 节点")

    except ET.ParseError:
        # 如果文件损坏，不是合法的 XML 格式
        print(f"    └─ ❌ [NFO损坏] {nfo_path.name} : 无法解析该文件，请检查是否为标准 XML 格式")
    except Exception as e:
        print(f"    └─ ❌ [读取错误] {nfo_path.name} : {str(e)}")


# ==========================================
# 2. 剧集处理逻辑 (寻找边界并逐集检查)
# ==========================================
def process_tv_show(title, season_folders):
    for season_folder in season_folders:
        # 提取当前是第几季
        season_match = re.search(r"(?i)Season\s*(\d+)", season_folder.name)
        season_num = int(season_match.group(1)) if season_match else 0

        # 获取该季文件夹下的所有文件
        files = [f for f in season_folder.iterdir() if f.is_file()]

        max_episode = 0
        episode_files = {}  # 结构：{ 集数: {'nfo': Path, 'jpg': Path} }

        # 遍历所有文件，寻找最大集数
        for f in files:
            # 寻找类似 S04E01 的特征
            ep_match = re.search(rf"(?i)S{season_num:02d}E(\d+)", f.name)
            if not ep_match:
                ep_match = re.search(r"(?i)S\d+E(\d+)", f.name)

            if ep_match:
                ep_num = int(ep_match.group(1))
                max_episode = max(max_episode, ep_num)

                if ep_num not in episode_files:
                    episode_files[ep_num] = {'nfo': None, 'jpg': None}

                ext = f.suffix.lower()
                if ext == '.nfo':
                    episode_files[ep_num]['nfo'] = f
                elif ext == '.jpg':
                    episode_files[ep_num]['jpg'] = f

        if max_episode == 0:
            print(f"📺 [剧集异常] {title} ({season_folder.name}) - 未找到任何包含 SxxExx 的文件")
            continue

        print(f"📺 [剧集] {title} - {season_folder.name} (判定共有 {max_episode} 集)")

        # 知道最大集数后，从第 1 集严格查到最大集数
        for ep in range(1, max_episode + 1):
            expected_name = f"{title} - S{season_num:02d}E{ep:02d} - 第 {ep} 集"
            ep_data = episode_files.get(ep, {'nfo': None, 'jpg': None})

            missing = []
            if not ep_data['nfo']:
                missing.append('.nfo')
            if not ep_data['jpg']:
                missing.append('.jpg')

            if missing:
                missing_str = " 和 ".join(missing)
                print(f"    └─ ❌ 缺少 {missing_str} : {expected_name}")
            else:
                # 既有 nfo 又有 jpg，触发 NFO 内容深度检查
                check_nfo_content(ep_data['nfo'])


# ==========================================
# 3. 主干扫描逻辑 (定性分析)
# ==========================================
def scan_library(root_dir):
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"错误: 路径不存在 {root_dir}")
        return

    print(f"开始扫描媒体库: {root_dir}")
    print("=" * 60)

    for item in root_path.iterdir():
        if not item.is_dir():
            continue

        folder_name = item.name

        # 提取剧名：去掉末尾的 "(年份)"
        match = re.match(r"^(.*?)(?:\s*\(\d{4}\))?$", folder_name)
        title = match.group(1).strip() if match else folder_name

        has_season = False
        has_movie_nfo = False
        season_folders = []

        # 遍历第一层，判断其身份
        for sub_item in item.iterdir():
            if sub_item.is_dir() and re.match(r"(?i)^Season\s*\d+", sub_item.name):
                has_season = True
                season_folders.append(sub_item)
            elif sub_item.is_file() and sub_item.name.lower() == 'movie.nfo':
                has_movie_nfo = True

        # 身份判定分流
        if has_season:
            process_tv_show(title, season_folders)
        elif has_movie_nfo:
            print(f"🎬 [电影正常] {folder_name} (包含 movie.nfo)")
        else:
            print(f"⚠️ [未知异常] {folder_name} - 既没有 Season 文件夹也没有 movie.nfo")


# ==========================================
# 4. 运行入口
# ==========================================
if __name__ == "__main__":
    # 在这里替换为你的真实路径
    TARGET_DIRECTORY = r"D:\测试挂削脚本"
    scan_library(TARGET_DIRECTORY)