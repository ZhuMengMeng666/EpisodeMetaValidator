import re
from config import VIDEO_EXTENSIONS
from utils.file_helper import get_existing_video_episodes
from utils.nfo_parser import check_nfo_content, check_movie_nfo_content


def process_movie(folder_path, folder_name, summary):
    video_files = [f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
    has_video = len(video_files) > 0

    movie_nfo_path = folder_path / 'movie.nfo'
    has_movie_nfo = movie_nfo_path.exists()

    name_nfo_paths = []
    for video_file in video_files:
        expected_nfo = folder_path / f"{video_file.stem}.nfo"
        if expected_nfo.exists():
            name_nfo_paths.append(expected_nfo)

    name_nfo_paths = list(set(name_nfo_paths))
    has_name_nfo = len(name_nfo_paths) > 0

    movie_errors = []

    if not has_movie_nfo and not has_name_nfo:
        if not has_video:
            print(f"⚠️ [未知异常] {folder_name} - 未找到任何特征 (无 Season, 无 nfo, 无视频)")
            summary["ignored"].append({"text": f"📂 [空/异常目录] {folder_name}", "path": folder_path})
            return
        else:
            print(f"🎬 [电影] {folder_name}")
            reason = f"完全缺失 NFO (未找到 movie.nfo 或与视频同名的 .nfo)"
            print(f"    └─ ❌ [需重刮削] {reason}")
            movie_errors.append(f"[需重刮削] {reason}")
    else:
        print(f"🎬 [电影] {folder_name}")
        nfos_to_check = []
        if has_movie_nfo: nfos_to_check.append(movie_nfo_path)
        if has_name_nfo: nfos_to_check.extend(name_nfo_paths)

        for nfo_path in nfos_to_check:
            is_valid, err_msg = check_movie_nfo_content(nfo_path)
            if not is_valid:
                reason = f"{nfo_path.name} 异常 ({err_msg})"
                print(f"    └─ ❌ [需重刮削] {reason}")
                movie_errors.append(f"[需重刮削] {reason}")

    # 修改：将路径对象一并存入 summary
    if movie_errors:
        summary["errors"].append({"target": f"🎬 [电影] {folder_name}", "path": folder_path, "issues": movie_errors})
    else:
        summary["perfect"].append({"text": f"🎬 [电影] {folder_name}", "path": folder_path})


def process_tv_show(title, season_folders, summary):
    for season_folder in season_folders:
        season_match = re.search(r"(?i)Season\s*(\d+)", season_folder.name)
        season_num = int(season_match.group(1)) if season_match else 0

        real_episodes = get_existing_video_episodes(season_folder, season_num)

        if not real_episodes:
            print(f"📺 [剧集异常] {title} ({season_folder.name}) - 未找到任何视频文件！")
            summary["ignored"].append({"text": f"📂 [无视频剧集] {title} - {season_folder.name}", "path": season_folder})
            continue

        print(f"📺 [剧集] {title} - {season_folder.name} (共发现真实视频: {len(real_episodes)} 集)")

        episode_files = {ep: {'nfo': None, 'jpg': None} for ep in real_episodes}

        for f in season_folder.iterdir():
            if not f.is_file(): continue
            ep_match = re.search(rf"(?i)S{season_num:02d}E(\d+)", f.name) or re.search(r"(?i)S\d+E(\d+)", f.name)
            if ep_match:
                ep_num = int(ep_match.group(1))
                if ep_num in episode_files:
                    ext = f.suffix.lower()
                    if ext == '.nfo':
                        episode_files[ep_num]['nfo'] = f
                    elif ext == '.jpg':
                        episode_files[ep_num]['jpg'] = f

        season_errors = []

        for ep in real_episodes:
            ep_data = episode_files[ep]

            if not ep_data['nfo']:
                missing_items = ".nfo" if ep_data['jpg'] else ".nfo 和 .jpg"
                reason = f"第 {ep} 集 完全缺失 ({missing_items})"
                print(f"    └─ ❌ [需重刮削] {reason}")
                season_errors.append(f"[需重刮削] {reason}")
            else:
                is_nfo_valid, err_msg = check_nfo_content(ep_data['nfo'])
                if not is_nfo_valid:
                    reason = f"第 {ep} 集 NFO非法 ({err_msg})"
                    print(f"    └─ ❌ [需重刮削] {reason}")
                    season_errors.append(f"[需重刮削] {reason}")
                else:
                    if not ep_data['jpg']:
                        reason = f"第 {ep} 集 缺少 .jpg 海报"
                        print(f"    └─ ❌ [需重刮削] {reason}")
                        season_errors.append(f"[需重刮削] {reason}")

        # 修改：以具体出错的 season_folder 为精准跳转目标
        if season_errors:
            summary["errors"].append(
                {"target": f"📺 [剧集] {title} - {season_folder.name}", "path": season_folder, "issues": season_errors})
        else:
            summary["perfect"].append({"text": f"📺 [剧集] {title} - {season_folder.name}", "path": season_folder})