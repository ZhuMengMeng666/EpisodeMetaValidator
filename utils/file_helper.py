import re
from config import VIDEO_EXTENSIONS

def get_existing_video_episodes(season_folder_path, season_num):
    """扫描季文件夹，根据真实存在的视频文件识别出实际拥有的集数"""
    existing_episodes = set()
    for f in season_folder_path.iterdir():
        if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS:
            ep_match = re.search(rf"(?i)S{season_num:02d}E(\d+)", f.name)
            if not ep_match:
                ep_match = re.search(r"(?i)S\d+E(\d+)", f.name)
            if ep_match:
                existing_episodes.add(int(ep_match.group(1)))
    return sorted(list(existing_episodes))