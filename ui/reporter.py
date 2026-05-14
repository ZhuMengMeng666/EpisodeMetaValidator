import os
import urllib.parse


def format_path_link(path):
    """将物理路径格式化为现代终端或浏览器支持的超链接格式 (仅用于终端打印)"""
    abs_path = str(path.resolve()).replace('\\', '/')
    encoded_path = urllib.parse.quote(abs_path, safe='/:')
    if not encoded_path.startswith('/'):
        return f"file:///{encoded_path}"
    return f"file://{encoded_path}"


def print_summary_report(summary):
    """终端简约打印版（已去除文件位置路径）"""
    print("\n\n" + "★" * 60)
    print(" " * 18 + "📊 跨目录最终刮削质检报告 📊")
    print("★" * 60)

    # 1. 优先级最高：需要修复板块
    print(f"\n❌ 【需要修复】 (共 {len(summary['errors'])} 部/季):")
    if not summary['errors']: print("   （太棒了！未发现任何刮削问题）")
    for err_group in summary['errors']:
        # 仅输出剧集/电影名字
        print(f"   ⚠️ {err_group['target']}")
        for issue in err_group['issues']:
            print(f"       └─ {issue}")

    # 2. 优先级其次：忽略/异常板块
    if summary['ignored']:
        print(f"\n👻 【忽略/异常目录】 (共 {len(summary['ignored'])} 个):")
        # 仅输出文件夹名字
        for item in summary['ignored']: print(f"   - {item['text']}")

    # 3. 优先级最低：完美无瑕板块
    print(f"\n✅ 【完美无瑕】 (共 {len(summary['perfect'])} 部/季):")
    if not summary['perfect']: print("   （无）")
    for item in summary['perfect']: print(f"   ✔️ {item['text']}")

    print("\n" + "★" * 60)



def generate_html_report(summary, file_path):
    """生成现代化的交互式 HTML 报告 (由 GUI 直接传入绝对路径)"""
    from datetime import datetime
    import os

    report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建 HTML 内容 (内嵌精美 CSS 样式)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>EpisodeMetaValidator 质检看板</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.05); }}
            h1 {{ text-align: center; color: #2c3e50; margin-bottom: 5px; }}
            .subtitle {{ text-align: center; color: #95a5a6; font-size: 0.9em; margin-bottom: 30px; }}

            /* 顶部卡片布局及交互特效 */
            .dashboard {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .card {{ flex: 1; text-align: center; padding: 25px; margin: 0 10px; border-radius: 10px; color: white; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease; }}
            .card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.15); }}
            .card-perfect {{ background: linear-gradient(135deg, #2ecc71, #27ae60); opacity: 0.9; }}
            .card-error {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
            .card-ignore {{ background: linear-gradient(135deg, #bdc3c7, #95a5a6); }}
            .card .number {{ font-size: 2.5em; display: block; margin-top: 10px; }}

            /* 列表内容样式 */
            h2 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 40px; color: #34495e; padding-top: 20px; }}
            .list-item {{ padding: 15px; border-bottom: 1px solid #f1f1f1; transition: background-color 0.3s; }}
            .list-item:hover {{ background-color: #fcfcfc; }}

            /* 弹性布局：让标题和按钮处于同一行，左右排开 */
            .item-header {{ display: flex; justify-content: space-between; align-items: center; }}
            .item-title {{ font-weight: bold; font-size: 1.1em; }}

            /* 按钮样式 */
            .btn-copy {{ padding: 5px 12px; color: white; background-color: #e67e22; border: none; border-radius: 4px; font-size: 0.85em; transition: 0.3s; cursor: pointer; font-family: inherit; font-weight: 500; }}
            .btn-copy:hover {{ background-color: #d35400; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}

            .error-list {{ margin-top: 10px; padding-left: 20px; color: #e74c3c; font-size: 0.95em; list-style-type: square; margin-bottom: 0; }}
            .footer {{ text-align: center; margin-top: 40px; color: #bdc3c7; font-size: 0.85em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 媒体库全局质检看板</h1>
            <div class="subtitle">生成时间：{report_time}</div>

            <!-- 统计卡片：加入了点击平滑滚动跳转事件 -->
            <div class="dashboard">
                <div class="card card-error" onclick="document.getElementById('section-errors').scrollIntoView({{behavior: 'smooth'}});">
                    需要修复 <span class="number">{len(summary['errors'])}</span>
                </div>
                <div class="card card-ignore" onclick="document.getElementById('section-ignored').scrollIntoView({{behavior: 'smooth'}});">
                    忽略/异常 <span class="number">{len(summary['ignored'])}</span>
                </div>
                <div class="card card-perfect" onclick="document.getElementById('section-perfect').scrollIntoView({{behavior: 'smooth'}});">
                    校验正确 <span class="number">{len(summary['perfect'])}</span>
                </div>
            </div>
    """

    # 1. 错误列表渲染 (加入了 id="section-errors" 锚点)
    if summary['errors']:
        html_content += "<h2 id='section-errors'>❌ 需要修复的项目</h2>"
        for err in summary['errors']:
            # 转义绝对路径中的反斜杠，以防 JavaScript 字符串解析报错
            raw_path = str(err['path'].resolve()).replace('\\', '\\\\')

            html_content += f"""
            <div class="list-item">
                <div class="item-header">
                    <div class="item-title">⚠️ {err['target']}</div>
                    <button onclick="navigator.clipboard.writeText('{raw_path}').then(() => alert('✅ 路径已复制！\\n\\n请按下 Win + E 打开资源管理器，并在地址栏粘贴即可直达。'))" class="btn-copy">📋 一键复制路径</button>
                </div>
                <ul class="error-list">
            """
            for issue in err['issues']:
                html_content += f"<li>{issue}</li>"
            html_content += "</ul></div>"

    # 2. 忽略列表渲染 (加入了 id="section-ignored" 锚点)
    if summary['ignored']:
        html_content += "<h2 id='section-ignored'>👻 忽略 / 异常目录</h2>"
        for item in summary['ignored']:
            raw_path = str(item['path'].resolve()).replace('\\', '\\\\')

            html_content += f"""
            <div class="list-item">
                <div class="item-header">
                    <div class="item-title" style="color:#7f8c8d;">{item['text']}</div>
                    <button onclick="navigator.clipboard.writeText('{raw_path}').then(() => alert('✅ 路径已复制！\\n\\n请按下 Win + E 打开资源管理器，并在地址栏粘贴即可直达。'))" class="btn-copy" style="background-color:#95a5a6;">📋 一键复制路径</button>
                </div>
            </div>
            """

    # 3. 完美列表渲染 (加入了 id="section-perfect" 锚点)
    if summary['perfect']:
        html_content += "<h2 id='section-perfect'>✅ 校验正确</h2>"
        for item in summary['perfect']:
            html_content += f"""
            <div class="list-item">
                <div class="item-header">
                    <div class="item-title" style="color:#27ae60;">✔️ {item['text']}</div>
                </div>
            </div>
            """

    html_content += """
            <div class="footer">EpisodeMetaValidator - Designed for Home Server</div>
        </div>
    </body>
    </html>
    """

    # 现在的 file_path 是由 GUI 文件弹窗直接决定的完整绝对路径
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)