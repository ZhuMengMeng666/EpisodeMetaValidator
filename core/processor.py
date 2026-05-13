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
            summary["ignored"].append(f"📂 [空/异常目录] {folder_name} (位于 {folder_path.parent.name})")
            return
        else:
            print(f"🎬 [电影] {folder_name}")
            video_names = ", ".join([v.name for v in video_files])
            print(f"    └─ ❌ [完全缺失] 未找到 movie.nfo，也未找到与视频 ({video_names}) 同名的 .nfo 文件")
            movie_errors.append("未找到任何相关的 NFO 文件")
    else:
        print(f"🎬 [电影] {folder_name}")
        nfos_to_check = []
        if has_movie_nfo: nfos_to_check.append(movie_nfo_path)
        if has_name_nfo: nfos_to_check.extend(name_nfo_paths)

        for nfo_path in nfos_to_check:
            is_valid, err_msg = check_movie_nfo_content(nfo_path)
            if not is_valid:
                print(f"    └─ ❌ [重刮削警告] {nfo_path.name} 非法 ({err_msg})")
                movie_errors.append(f"{nfo_path.name} 异常 ({err_msg})")

    if movie_errors:
        summary["errors"].append({"target": f"🎬 [电影] {folder_name}", "issues": movie_errors})
    else:
        summary["perfect"].append(f"🎬 [电影] {folder_name}")


def process_tv_show(title, season_folders, summary):
    for season_folder in season_folders:
        season_match = re.search(r"(?i)Season\s*(\d+)", season_folder.name)
        season_num = int(season_match.group(1)) if season_match else 0

        real_episodes = get_existing_video_episodes(season_folder, season_num)

        if not real_episodes:
            print(f"📺 [剧集异常] {title} ({season_folder.name}) - 未找到任何视频文件！")
            summary["ignored"].append(f"📂 [无视频剧集] {title} - {season_folder.name}")
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
            expected_name = f"{title} - S{season_num:02d}E{ep:02d} - 第 {ep} 集"
            ep_data = episode_files[ep]

            if not ep_data['nfo']:
                print(f"    └─ ❌ [完全缺失] 未找到 NFO 文件，请整集重新刮削 (.nfo 和 .jpg) : {expected_name}")
                season_errors.append(f"第 {ep} 集 完全缺失 (.nfo 和 .jpg)")
            else:
                is_nfo_valid, err_msg = check_nfo_content(ep_data['nfo'])
                if not is_nfo_valid:
                    print(f"    └─ ❌ [重刮削警告] 包含非法 NFO，请整集重新刮削 (.nfo 和 .jpg) : {expected_name}")
                    season_errors.append(f"第 {ep} 集 NFO 非法 ({err_msg})")
                else:
                    if not ep_data['jpg']:
                        print(f"    └─ ❌ [缺少海报] NFO合法，但缺少 .jpg : {expected_name}")
                        season_errors.append(f"第 {ep} 集 缺少 .jpg 海报")

        if season_errors:
            summary["errors"].append({"target": f"📺 [剧集] {title} - {season_folder.name}", "issues": season_errors})
        else:
            summary["perfect"].append(f"📺 [剧集] {title} - {season_folder.name}")