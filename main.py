import re
import sys
import threading
from pathlib import Path
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# 导入核心配置与业务逻辑
from config import TARGET_DIRECTORIES, IGNORE_FOLDER_NAMES
from core.scanner import scan_library
from ui.reporter import print_summary_report, generate_html_report

# 设置 UI 整体风格
ctk.set_appearance_mode("System")  # 跟随系统深浅色
ctk.set_default_color_theme("blue")


class TextRedirector:
    """拦截标准的 print 输出，并线程安全地重定向到 GUI 控制台"""

    def __init__(self, textbox):
        self.textbox = textbox
        self.buffer = ""
        # 基础色彩高亮
        self.textbox.tag_config("error", foreground="#ff4d4d")
        self.textbox.tag_config("success", foreground="#2ecc71")
        self.textbox.tag_config("warning", foreground="#f39c12")
        self.textbox.tag_config("info", foreground="#3498db")
        self.textbox.tag_config("system", foreground="#7f8c8d")

    def write(self, string):
        self.buffer += string
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self.textbox.after(0, self.process_line, line + "\n")

    def process_line(self, line):
        tag = "normal"
        if "❌" in line or "[需重刮削]" in line or "异常" in line:
            tag = "error"
        elif "✅" in line or "✔️" in line or "🎉" in line:
            tag = "success"
        elif "⚠️" in line or "⏭️" in line or "👻" in line:
            tag = "warning"
        elif "🚀" in line or "📊" in line or "📁" in line:
            tag = "info"
        elif "🛑" in line or "⏸️" in line or "▶️" in line or "---" in line or "===" in line:
            tag = "system"

        self.textbox.insert("end", line, tag)
        self.textbox.see("end")

    def flush(self):
        pass


class EpisodeMetaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("EpisodeMetaValidator - 媒体库元数据校验器 (© 2026 zhumengmeng 保留所有权利)")
        self.geometry("900x700")
        self.minsize(800, 600)

        # ==========================================
        # 🌟 设置窗口左上角的自定义 Logo 图标
        # ==========================================
        try:
            # 使用标准的 iconbitmap 加载 .ico 文件
            self.iconbitmap("logo.ico")
        except Exception as e:
            print(f"⚠️ [UI提示] 无法加载图标，请确保 logo.ico 存在于同级目录: {e}")
        # ==========================================

        # 全局状态控制 (事件锁)
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.stop_event = threading.Event()
        self.total_items = 0
        self.scanned_items = 0

        self.setup_ui()
        sys.stdout = TextRedirector(self.console_textbox)

    def setup_ui(self):
        # ==========================================
        # 1. 顶部配置区
        # ==========================================
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=20)

        # --- 目标扫描目录区 ---
        target_header = ctk.CTkFrame(input_frame, fg_color="transparent")
        target_header.pack(fill="x", padx=10, pady=(0, 0))

        ctk.CTkLabel(target_header, text="媒体库扫描目录 (支持多行或英文逗号隔开):", font=("", 14, "bold")).pack(
            side="left")
        ctk.CTkButton(target_header, text="📁 添加文件夹", width=100, height=28,
                      command=self.browse_folder).pack(side="right")

        self.txt_targets = ctk.CTkTextbox(input_frame, height=80)
        self.txt_targets.pack(fill="x", padx=10, pady=5)
        self.txt_targets.insert("1.0", "\n".join(TARGET_DIRECTORIES))

        # --- 忽略目录区 ---
        ctk.CTkLabel(input_frame, text="忽略的文件夹 (支持多行或英文逗号隔开):", font=("", 14, "bold")).pack(
            anchor="w", padx=10, pady=(10, 0))
        self.txt_ignores = ctk.CTkTextbox(input_frame, height=60)
        self.txt_ignores.pack(fill="x", padx=10, pady=5)
        self.txt_ignores.insert("1.0", ", ".join(IGNORE_FOLDER_NAMES))

        # ==========================================
        # 2. 中部控制台面板
        # ==========================================
        console_header = ctk.CTkFrame(self, fg_color="transparent")
        console_header.pack(fill="x", padx=20, pady=(0, 5))

        ctk.CTkLabel(console_header, text="实时控制台:", font=("", 14, "bold")).pack(side="left")

        self.btn_start = ctk.CTkButton(console_header, text="开始检查", font=("", 14, "bold"),
                                       command=self.start_scan)
        self.btn_start.pack(side="right")

        self.console_textbox = ctk.CTkTextbox(self, state="normal", font=("Consolas", 13))
        self.console_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def browse_folder(self):
        """打开系统选择文件夹对话框，并将路径追加到文本框"""
        folder_selected = filedialog.askdirectory(title="选择要扫描的媒体库目录")
        if folder_selected:
            clean_path = str(Path(folder_selected))
            current_text = self.txt_targets.get("1.0", "end").strip()
            if current_text:
                self.txt_targets.insert("end", f"\n{clean_path}")
            else:
                self.txt_targets.insert("1.0", clean_path)

    def parse_input(self, text):
        tokens = re.split(r'[,\n]', text)
        return [t.strip() for t in tokens if t.strip()]

    def start_scan(self):
        target_dirs = self.parse_input(self.txt_targets.get("1.0", "end"))
        ignore_dirs = self.parse_input(self.txt_ignores.get("1.0", "end"))

        if not target_dirs:
            messagebox.showwarning("参数错误", "请先添加至少一个目标扫描目录！")
            return

        # 统计目录数量
        self.total_items = 0
        valid_dirs = []
        for d in target_dirs:
            p = Path(d)
            if p.exists() and p.is_dir():
                valid_dirs.append(d)
                self.total_items += sum(1 for item in p.iterdir() if item.is_dir())
            else:
                messagebox.showerror("路径不存在", f"无法找到路径: {d}")
                return

        if self.total_items == 0:
            messagebox.showinfo("提示", "所选目录中没有发现任何子文件夹。")
            return

        # 初始化状态
        self.console_textbox.delete("1.0", "end")
        self.scanned_items = 0
        self.stop_event.clear()
        self.pause_event.set()

        self.btn_start.configure(state="disabled")

        self.show_progress_window()

        # 后台起线程
        threading.Thread(target=self.scan_thread_task, args=(valid_dirs, ignore_dirs), daemon=True).start()

    def show_progress_window(self):
        """居中显示模态进度弹窗"""
        self.progress_window = ctk.CTkToplevel(self)
        self.progress_window.title("扫描进度")

        # 绝对居中算法
        win_w, win_h = 450, 260
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (win_w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (win_h // 2)
        self.progress_window.geometry(f"{win_w}x{win_h}+{x}+{y}")

        self.progress_window.attributes('-topmost', True)
        self.progress_window.grab_set()
        self.progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

        self.lbl_scanning = ctk.CTkLabel(self.progress_window, text="正在初始化雷达...", font=("", 15),
                                         wraplength=400)
        self.lbl_scanning.pack(pady=(30, 10))

        # 进度条与百分比布局
        progress_frame = ctk.CTkFrame(self.progress_window, fg_color="transparent")
        progress_frame.pack(fill="x", padx=40, pady=10)

        self.progressbar = ctk.CTkProgressBar(progress_frame, height=12)
        self.progressbar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progressbar.set(0)

        self.lbl_pct = ctk.CTkLabel(progress_frame, text="0%", font=("", 14, "bold"), text_color="#3498db")
        self.lbl_pct.pack(side="right")

        # 按钮容器
        btn_frame = ctk.CTkFrame(self.progress_window, fg_color="transparent")
        btn_frame.pack(pady=20)

        self.btn_pause = ctk.CTkButton(btn_frame, text="⏸️ 暂停", fg_color="#e67e22", hover_color="#d35400", width=120,
                                       command=self.toggle_pause)
        self.btn_pause.pack(side="left", padx=10)

        self.btn_stop = ctk.CTkButton(btn_frame, text="🛑 提前终止", fg_color="#c0392b", hover_color="#922b21",
                                      width=120, command=self.stop_scan)
        self.btn_stop.pack(side="right", padx=10)

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.btn_pause.configure(text="▶️ 继续", fg_color="#27ae60", hover_color="#2ecc71")
            self.lbl_scanning.configure(text="⏸️ 扫描已挂起，等待指令...")
            print("\n" + "-" * 40)
            print("⏸️ [系统] 扫描已暂停...")
            print("-" * 40)
        else:
            self.pause_event.set()
            self.btn_pause.configure(text="⏸️ 暂停", fg_color="#e67e22", hover_color="#d35400")
            print("▶️ [系统] 扫描继续！\n")

    def stop_scan(self):
        """触发安全终止信号"""
        self.stop_event.set()
        self.pause_event.set()
        self.lbl_scanning.configure(text="🛑 正在进行安全终止，请稍候...", text_color="#e74c3c")
        self.btn_pause.configure(state="disabled")
        self.btn_stop.configure(state="disabled")

    def update_progress_callback(self, item_name):
        self.scanned_items += 1
        pct = self.scanned_items / self.total_items
        self.after(0, self._update_progress_ui, item_name, pct)

    def _update_progress_ui(self, item_name, pct):
        safe_pct = min(1.0, max(0.0, pct))
        self.lbl_scanning.configure(text=f"正在分析: {item_name}")
        self.progressbar.set(safe_pct)
        self.lbl_pct.configure(text=f"{int(safe_pct * 100)}%")

    def scan_thread_task(self, target_dirs, ignore_dirs):
        global_summary = {"perfect": [], "errors": [], "ignored": []}

        for directory in target_dirs:
            if self.stop_event.is_set():
                break
            scan_library(directory, global_summary, ignore_dirs,
                         self.pause_event, self.stop_event, self.update_progress_callback)

        self.after(0, self.on_scan_complete, global_summary)

    def on_scan_complete(self, global_summary):
        self.progress_window.destroy()
        self.btn_start.configure(state="normal")

        if self.stop_event.is_set():
            print("\n🛑 [系统] 扫描已终止！以下为已扫描部分的数据：")
        else:
            print("\n🎉 扫描全部完成！准备保存 HTML 报告...")

        print_summary_report(global_summary)

        # 触发弹窗保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = "Partial_" if self.stop_event.is_set() else ""
        default_filename = f"{prefix}MetaReport_{timestamp}.html"

        filepath = filedialog.asksaveasfilename(
            title="保存媒体库元数据质检报告",
            initialfile=default_filename,
            defaultextension=".html",
            filetypes=[("HTML 网页文件", "*.html"), ("所有文件", "*.*")]
        )

        if filepath:
            generate_html_report(global_summary, filepath)
            print(f"\n✅ 报告已成功保存至: {filepath}")
        else:
            print("\n⚠️ 用户取消了保存媒体库元数据质检报告。")


if __name__ == "__main__":
    app = EpisodeMetaApp()
    app.mainloop()