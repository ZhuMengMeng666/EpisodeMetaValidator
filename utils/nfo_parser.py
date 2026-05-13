import xml.etree.ElementTree as ET


def check_nfo_content(nfo_path):
    """检查剧集 NFO"""
    return _parse_nfo_plot(nfo_path)


def check_movie_nfo_content(nfo_path):
    """检查电影 NFO"""
    return _parse_nfo_plot(nfo_path)


# 提取出的公共方法，避免代码重复
def _parse_nfo_plot(nfo_path):
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