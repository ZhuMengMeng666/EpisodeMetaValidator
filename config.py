# 1. 视频后缀识别库
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.ts', '.rmvb', '.flv', '.wmv', '.webm'}

# 2. 忽略扫描的文件夹名称
IGNORE_FOLDER_NAMES = {
    'Tom.And.Jerry.DVDrip.x264.AC3.4Audios-shadow610',
    '物语系列',
}

# 3. 扫描目标目录配置
TARGET_DIRECTORIES = [
    r"N:\NasTool\cartoon",
    r"N:\NasTool\movie",
]

# 4. 📈 HTML 报告存储配置
# 如果不填绝对路径，"./reports" 会自动在当前项目下创建一个 reports 文件夹
HTML_REPORT_DIR = r"./reports"