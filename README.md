# EpisodeMetaValidator 🎬📺

![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**EpisodeMetaValidator** 是一个轻量级、无第三方依赖的 Python 自动化本地媒体库质检工具。专为 Emby, Jellyfin, Plex 等媒体服务器的底层数据维护而设计。

它通过跨目录交叉扫描、精准身份定性以及深度 XML 解析，自动排查影视库中的“残缺刮削”、“空壳 NFO”以及“废弃目录”，做你本地媒体库的终极“质检员”。

---

## 📖 核心解决痛点

1. **空壳 NFO 侦测**：解决刮削器（如 TinyMediaManager）运行失败或网络异常导致的 NFO `<plot>` (剧情) 节点为空的问题。
2. **漏刮削排查**：发现目录中存在视频实体，但遗漏了 `.nfo` 或 `.jpg` 的隐藏文件。
3. **垃圾清理定位**：精准定位群晖 (`@eaDir`)、Windows 系统生成的垃圾隐藏文件夹或无视频的废弃空文件夹。

## ✨ 核心特性

- 🚀 **零依赖**：纯 Python 标准库实现（`os`, `re`, `pathlib`, `xml`），无需 `pip install` 任何第三方包，开箱即用。
- 🔀 **智能身份分流**：无需手动分类。程序会自动侦测目录特征（寻找 `Season` 文件夹或 `tvshow.nfo`），智能将其分流至“剧集查验引擎”或“电影查验引擎”。
- 📂 **多目录并发扫描**：支持同时挂载多个物理盘符或顶级目录（如同时扫描 `D:\TV` 和 `E:\Movies`）。
- 🛡️ **忽略黑名单拦截**：支持自定义忽略列表，遇到配置的系统垃圾文件夹秒速跳过，大幅提升扫描性能。
- 📊 **可视化总结面板**：告别杂乱的流水账日志，扫描结束后在终端输出分类清晰的结构化大屏报告（✅完美、❌需修复、👻忽略）。

## 📂 项目结构

本项目遵循高内聚、低耦合的现代软件工程原则设计：

```text
EpisodeMetaValidator/
│
├── main.py                  # 🚀 启动入口 (全局调度中心)
├── config.py                # ⚙️ 全局配置 (后缀库、忽略名单、目标目录池)
│
├── core/                    # 🧠 核心业务层
│   ├── __init__.py
│   ├── scanner.py           # 目录遍历引擎与分流路由
│   └── processor.py         # 电影/剧集定制化深度查验流水线
│
├── utils/                   # 🛠️ 纯函数工具箱 (无副作用)
│   ├── __init__.py
│   ├── file_helper.py       # 视频实体识别与集数正则提取
│   └── nfo_parser.py        # 专注于 XML 树的解析与错误捕获
│
└── ui/                      # 🖥️ 展现层
    ├── __init__.py
    └── reporter.py          # 终端可视化面板渲染与大盘点输出
