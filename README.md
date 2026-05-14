# 🎬 EpisodeMetaValidator

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![UI](https://img.shields.io/badge/UI-CustomTkinter-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

**EpisodeMetaValidator** 是一款专为本地影音玩家（NAS / HTPC）打造的 **媒体库元数据校验器**。

它的核心目的是：帮你揪出庞大媒体库中那些**“刮削不完整”**的残次品。无论是缺失的 `.nfo` 描述文件、丢失的封面海报，还是目录结构嵌套异常，它都能精准扫出，并为你生成一份直观的可视化修复看板，专治媒体库强迫症。

---

## ✨ 项目特色与功能

### 🎯 深度元数据质检
*   **精准识别**：自动区分“电影”与“剧集（Season）”的不同元数据规范。
*   **异常捕获**：快速定位缺失 `.nfo`、缺失 `.jpg` 海报或存在幽灵文件夹的影视条目。
*   **灵活过滤**：支持自定义忽略系统生成的缓存或回收站文件夹（如 `@eaDir`, `#recycle`）。

### 🖥️ 极客风图形化界面 (GUI)
*   **现代交互**：基于 `CustomTkinter` 打造的深/浅色自适应界面。
*   **全局掌控**：内置极客风实时彩色日志控制台，红绿高亮，一目了然。
*   **任务打断**：支持多目录批量扫描，提供实时跳动的百分比进度条，并支持随时 **暂停 / 继续 / 提前终止**。

### 📊 交互式 HTML 质检报告
*   **直观看板**：扫描结束后，自动生成带数据统计的现代化 HTML 网页报告。
*   **优先级排序**：将扫描结果严格按照“需要修复”、“忽略/异常”、“完美无瑕”进行分层展示。

---

## 📸 界面一览

**主控面板与实时日志**
> ![Main UI](https://github.com/ZhuMengMeng666/EpisodeMetaValidator/blob/master/assets/UI.png)

**自动生成的元数据校验报告**
> ![HTML Report](https://github.com/ZhuMengMeng666/EpisodeMetaValidator/blob/master/assets/HtmlRetport.png)

---

## 🚀 极速运行

确保你的电脑已安装 Python 3.8+，然后执行以下命令即可启动：

```bash
# 1. 克隆项目
git clone [https://github.com/ZhuMengMeng666/EpisodeMetaValidator.git](https://github.com/ZhuMengMeng666/EpisodeMetaValidator.git)
cd EpisodeMetaValidator

# 2. 安装 UI 依赖
pip install customtkinter

# 3. 启动质检仪
python main.py

## 😊 未来展望
可能会对项目进行压缩，压缩为exe一件运行，免去琐碎的部署操作。
