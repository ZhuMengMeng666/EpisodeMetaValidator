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
    """返回元组: (是否合法, 错误原因)"""
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        plot_node = root.find('plot')

        if plot_node is not None:
            plot_text = plot_node.text
            if not plot_text or not plot_text.strip():
                print(f"    └─ ⚠️ [剧情缺失] {nfo_path.name} : <plot> 节点内容为空")
                return False, "<plot> 节点内容为空"
        else:
            print(f"    └─ ⚠️ [NFO节点缺失] {nfo_path.name} : 未找到 <plot> 节点")
            return False, "未找到 <plot> 节点"

        return True, ""
    except ET.ParseError:
        print(f"    └─ ❌ [NFO损坏] {nfo_path.name} : 无法解析该 XML")
        return False, "文件损坏(非标准XML)"
    except Exception as e:
        print(f"    └─ ❌ [读取错误] {nfo_path.name} : {str(e)}")
        return False, f"读取错误: {str(e)}"


# ==========================================
# 3. 核心方法：电影 NFO 深度检查
# ==========================================
def check_movie_nfo_content(nfo_path):
    """返回元组: (是否合法, 错误原因)"""
    try:
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        plot_node = root.find('plot')

        if plot_node is not None:
            plot_text = plot_node.text
            if not plot_text or not plot_text.strip():
                print(f"    └─ ❌ [剧情缺失] {nfo_path.name} : <plot> 节点内容为空")
                return False, "<plot> 节点内容为空"
        else:
            print(f"    └─ ❌ [NFO节点缺失] {nfo_path.name} : 未找到 <plot> 节点")
            return False, "未找到 <plot> 节点"

        return True, ""
    except ET.ParseError:
        print(f"    └─ ❌ [NFO损坏] {nfo_path.name} : 无法解析该 XML")
        return False, "文件损坏(非标准XML)"
    except Exception as e:
        print(f"    └─ ❌ [读取错误] {nfo_path.name} : {str(e)}")
        return False, f"读取错误: {str(e)}"


# ==========================================
# 4. 业务逻辑：电影处理分支 (重点升级区域)
# ==========================================
def process_movie(folder_path, folder_name, summary):
    # 1. 查找文件夹内的所有真实视频文件
    video_files = [f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
    has_video = len(video_files) > 0

    # 2. 检查 movie.nfo 是否存在
    movie_nfo_path = folder_path / 'movie.nfo'
    has_movie_nfo = movie_nfo_path.exists()

    # 3. 寻找与视频“同名”的 NFO 文件
    name_nfo_paths = []
    for video_file in video_files:
        # video_file.stem 获取不带后缀的名字，拼装成 .nfo
        expected_nfo = folder_path / f"{video_file.stem}.nfo"
        if expected_nfo.exists():
            name_nfo_paths.append(expected_nfo)

    # 去重（防止多视频匹配到同一个nfo）
    name_nfo_paths = list(set(name_nfo_paths))
    has_name_nfo = len(name_nfo_paths) > 0

    movie_errors = []

    # 情形 1：什么 NFO 都没有
    if not has_movie_nfo and not has_name_nfo:
        if not has_video:
            # 没视频也没NFO，废弃文件夹
            print(f"⚠️ [未知异常] {folder_name} - 未找到任何特征 (无 Season, 无 nfo, 无视频)")
            summary["ignored"].append(f"📂 [空/异常目录] {folder_name}")
            return
        else:
            # 有视频但没刮削
            print(f"🎬 [电影] {folder_name}")
            video_names = ", ".join([v.name for v in video_files])
            print(f"    └─ ❌ [完全缺失] 未找到 movie.nfo，也未找到与视频 ({video_names}) 同名的 .nfo 文件")
            movie_errors.append("未找到任何相关的 NFO 文件")

    # 情形 2：至少存在一个 NFO (movie.nfo 或 同名.nfo)
    else:
        print(f"🎬 [电影] {folder_name}")

        # 将存在的 nfo 都放入“待查清单”
        nfos_to_check = []
        if has_movie_nfo:
            nfos_to_check.append(movie_nfo_path)
        if has_name_nfo:
            nfos_to_check.extend(name_nfo_paths)

        # 遍历检查清单里的所有 nfo (如果两者都有，两个都会被检查)
        for nfo_path in nfos_to_check:
            is_valid, err_msg = check_movie_nfo_content(nfo_path)
            if not is_valid:
                print(f"    └─ ❌ [重刮削警告] {nfo_path.name} 非法 ({err_msg})")
                movie_errors.append(f"{nfo_path.name} 异常 ({err_msg})")

    # 录入总结报告
    if movie_errors:
        summary["errors"].append({"target": f"🎬 [电影] {folder_name}", "issues": movie_errors})
    else:
        summary["perfect"].append(f"🎬 [电影] {folder_name}")


# ==========================================
# 5. 业务逻辑：剧集处理分支
# ==========================================
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

        # 录入总结报告
        if season_errors:
            summary["errors"].append({"target": f"📺 [剧集] {title} - {season_folder.name}", "issues": season_errors})
        else:
            summary["perfect"].append(f"📺 [剧集] {title} - {season_folder.name}")


# ==========================================
# 6. 主干扫描逻辑
# ==========================================
def scan_library(root_dir):
    root_path = Path(root_dir)

    if not root_path.exists():
        print(f"错误: 路径不存在 {root_dir}")
        return

    print(f"开始扫描媒体库: {root_dir}")
    print("=" * 60)

    summary = {
        "perfect": [],
        "errors": [],
        "ignored": []
    }

    for item in root_path.iterdir():
        if not item.is_dir(): continue

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
                summary["ignored"].append(f"📂 [结构错误剧集] {folder_name} (无 Season)")
            else:
                process_tv_show(title, season_folders, summary)
        else:
            # 仅传递必要参数给 process_movie
            process_movie(item, folder_name, summary)

    # ==========================================
    # 7. 打印最终总结报告
    # ==========================================
    print("\n\n" + "★" * 60)
    print(" " * 18 + "📊 最终刮削质检报告 📊")
    print("★" * 60)

    print(f"\n✅ 【完美无瑕】 (共 {len(summary['perfect'])} 部/季):")
    if not summary['perfect']:
        print("   （无完美数据，革命尚未成功）")
    for item in summary['perfect']:
        print(f"   ✔️ {item}")

    print(f"\n❌ 【需要修复】 (共 {len(summary['errors'])} 部/季):")
    if not summary['errors']:
        print("   （太棒了！未发现任何刮削问题）")
    for err_group in summary['errors']:
        print(f"   ⚠️ {err_group['target']}")
        for issue in err_group['issues']:
            print(f"       └─ {issue}")

    if summary['ignored']:
        print(f"\n👻 【废弃/异常目录】 (共 {len(summary['ignored'])} 个):")
        for item in summary['ignored']:
            print(f"   - {item}")

    print("\n" + "★" * 60)


# ==========================================
# 运行入口
# ==========================================
if __name__ == "__main__":
    # 替换为你实际的测试路径
    TARGET_DIRECTORY = r"N:\NasTool\cartoon"

    scan_library(TARGET_DIRECTORY)