import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

# ==========================================
# 配置区
# ==========================================
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.ts', '.rmvb', '.flv', '.wmv', '.webm'}


# ==========================================
# 1. 辅助方法：提取真实存在的视频集数
# ==========================================
def get_existing_video_episodes(season_folder_path, season_num):
    existing_episodes = set()
    for f in season_folder_path.iterdir():
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            ep_match = re.search(rf"(?i)S{season_num:02d}E(\d+)", f.name)
            if not ep_match:
                ep_match = re.search(r"(?i)S\d+E(\d+)", f.name)
            if ep_match:
                existing_episodes.add(int(ep_match.group(1)))
    return sorted(list(existing_episodes))


# ==========================================
# 2. 核心方法：剧集 NFO 深度检查
# ==========================================
def check_nfo_content(nfo_path):
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        plot_node = root.find('plot')

        if plot_node is not None:
            plot_text = plot_node.text
            if not plot_text or not plot_text.strip():
                print(f"    └─ ⚠️ [剧情缺失] {nfo_path.name} : <plot> 节点内容为空")
                return False
        else:
            print(f"    └─ ⚠️ [NFO节点缺失] {nfo_path.name} : 未找到 <plot> 节点")
            return False

        return True
    except ET.ParseError:
        print(f"    └─ ❌ [NFO损坏] {nfo_path.name} : 无法解析该 XML")
        return False
    except Exception as e:
        print(f"    └─ ❌ [读取错误] {nfo_path.name} : {str(e)}")
        return False


# ==========================================
# 3. 核心方法：电影 movie.nfo 深度检查
# ==========================================
def check_movie_nfo_content(nfo_path):
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()

        plot_node = root.find('plot')

        if plot_node is not None:
            plot_text = plot_node.text
            if not plot_text or not plot_text.strip():
                # print(f"    └─ ❌ [剧情缺失] {nfo_path.name} : <plot> 节点内容为空")
                return False
        else:
            # print(f"    └─ ❌ [NFO节点缺失] {nfo_path.name} : 未找到 <plot> 节点")
            return False

        return True
    except ET.ParseError:
        # print(f"    └─ ❌ [NFO损坏] {nfo_path.name} : 无法解析该 XML")
        return False
    except Exception as e:
        # print(f"    └─ ❌ [读取错误] {nfo_path.name} : {str(e)}")
        return False


# ==========================================
# 4. 业务逻辑：电影处理分支
# ==========================================
def process_movie(folder_path, folder_name):
    movie_nfo_path = folder_path / 'movie.nfo'

    # 检查文件夹内是否有真实的视频文件
    has_video = any(f.suffix.lower() in VIDEO_EXTENSIONS for f in folder_path.iterdir() if f.is_file())

    if not movie_nfo_path.exists():
        if not has_video:
            # 既没有 NFO，也没有视频，属于废弃/空文件夹
            print(f"⚠️ [未知异常] {folder_name} - 未找到任何特征 (无 Season, 无 nfo, 无视频)")
        else:
            # 被分流到电影区，有视频但没 NFO，直接报错重刮削
            print(f"🎬 [电影] {folder_name}")
            print(f"    └─ ❌ [完全缺失] 未找到 movie.nfo 文件，请重新刮削该电影")
    else:
        print(f"🎬 [电影] {folder_name}")
        is_valid = check_movie_nfo_content(movie_nfo_path)
        if not is_valid:
            print(f"    └─ ❌ [重刮削警告] 包含非法的 movie.nfo，请重新刮削该电影")


# ==========================================
# 5. 业务逻辑：剧集处理分支
# ==========================================
def process_tv_show(title, season_folders):
    for season_folder in season_folders:
        season_match = re.search(r"(?i)Season\s*(\d+)", season_folder.name)
        season_num = int(season_match.group(1)) if season_match else 0

        real_episodes = get_existing_video_episodes(season_folder, season_num)

        if not real_episodes:
            print(f"📺 [剧集异常] {title} ({season_folder.name}) - 未找到任何视频文件！")
            continue

        print(f"📺 [剧集] {title} - {season_folder.name} (共发现真实视频: {len(real_episodes)} 集)")

        episode_files = {ep: {'nfo': None, 'jpg': None} for ep in real_episodes}

        for f in season_folder.iterdir():
            if not f.is_file():
                continue

            ep_match = re.search(rf"(?i)S{season_num:02d}E(\d+)", f.name) or re.search(r"(?i)S\d+E(\d+)", f.name)
            if ep_match:
                ep_num = int(ep_match.group(1))
                if ep_num in episode_files:
                    ext = f.suffix.lower()
                    if ext == '.nfo':
                        episode_files[ep_num]['nfo'] = f
                    elif ext == '.jpg':
                        episode_files[ep_num]['jpg'] = f

        for ep in real_episodes:
            expected_name = f"{title} - S{season_num:02d}E{ep:02d} - 第 {ep} 集"
            ep_data = episode_files[ep]

            if not ep_data['nfo']:
                print(f"    └─ ❌ [完全缺失] 未找到 NFO 文件，请整集重新刮削 (.nfo 和 .jpg) : {expected_name}")
            else:
                is_nfo_valid = check_nfo_content(ep_data['nfo'])
                if not is_nfo_valid:
                    print(f"    └─ ❌ [重刮削警告] 包含非法 NFO，请整集重新刮削 (.nfo 和 .jpg) : {expected_name}")
                else:
                    if not ep_data['jpg']:
                        print(f"    └─ ❌ [缺少海报] NFO合法，但缺少 .jpg : {expected_name}")


# ==========================================
# 6. 主干扫描逻辑 (极简定性分流)
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
        match = re.match(r"^(.*?)(?:\s*\(\d{4}\))?$", folder_name)
        title = match.group(1).strip() if match else folder_name

        has_season = False
        has_tvshow_nfo = False
        season_folders = []

        # 遍历判定特征
        for sub_item in item.iterdir():
            if sub_item.is_dir() and re.match(r"(?i)^Season\s*\d+", sub_item.name):
                has_season = True
                season_folders.append(sub_item)
            elif sub_item.is_file() and sub_item.name.lower() == 'tvshow.nfo':
                has_tvshow_nfo = True

        # ====== 核心分流 ======
        # 只要存在 Season 或 tvshow.nfo，就判定为电视剧
        if has_season or has_tvshow_nfo:
            if not season_folders:
                # 容错：被 tvshow.nfo 确认为剧集，但忘了建 Season 文件夹
                print(f"📺 [剧集异常] {folder_name} - 存在 tvshow.nfo，但未找到 Season 文件夹！")
            else:
                process_tv_show(title, season_folders)
        else:
            # 既没有 Season 也没有 tvshow.nfo，统统交给电影处理逻辑去甄别
            process_movie(item, folder_name)


# ==========================================
# 7. 运行入口
# ==========================================
if __name__ == "__main__":
    # 替换为你实际的测试路径
    TARGET_DIRECTORY = r"N:\NasTool\movie"

    scan_library(TARGET_DIRECTORY)