"""CET-4 Archive site builder — 复用 gaoshu-textbook 的 md→html 转换 + 折叠答案."""
import os, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC_DIR = os.path.join(os.path.dirname(__file__), "content")
OUT_DIR = os.path.dirname(__file__)

BOX_MARKERS = {
    "::ex": "box-example", "::tip": "box-intuition", "::warn": "box-pitfall",
    "::note": "box-def", "::answer": "box-answer",
}


def escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_inline(s):
    s = escape(s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    out = []
    lines = md.split("\n")
    in_p = False
    in_ul = False
    ul_tag = "ul"
    in_box = None
    in_ans = False
    for line in lines:
        line = line.rstrip()
        box_open = re.match(r"^(::ex|::tip|::warn|::note|::answer)\s*(.*)$", line)
        if box_open:
            if in_p: out.append("</p>"); in_p = False
            if in_ul: out.append(f"</{ul_tag}>"); in_ul = False
            in_box = BOX_MARKERS[box_open.group(1)]
            rest = box_open.group(2).strip()
            if in_box == "box-answer":
                summary = format_inline(rest) if rest else "📖 点击查看答案 / 解析"
                out.append(f'<details class="box-answer"><summary>{summary}</summary>')
            else:
                out.append(f'<div class="{in_box}">')
                if rest:
                    out.append(f"<p>{format_inline(rest)}</p>")
            continue
        # 在 ::ex 内自动识别"**答案**:"/"**解析**:" 折叠
        if in_box == "box-example" and re.match(r"^\*\*(答案|解析|参考答案)\*\*[::]?", line):
            if in_p: out.append("</p>"); in_p = False
            if in_ul: out.append(f"</{ul_tag}>"); in_ul = False
            if not in_ans:
                out.append('<details class="box-answer"><summary>📖 点击查看答案 / 解析</summary>')
                in_ans = True
            after = re.sub(r"^\*\*(答案|解析|参考答案)\*\*[::]?\s*", "", line).strip()
            if after:
                out.append(f"<p>{format_inline(after)}</p>")
            continue
        if line.strip() == "::end" and in_box:
            if in_p: out.append("</p>"); in_p = False
            if in_ul: out.append(f"</{ul_tag}>"); in_ul = False
            if in_box == "box-example" and in_ans:
                out.append("</details>")
                in_ans = False
            if in_box == "box-answer":
                out.append("</details>")
            else:
                out.append("</div>")
            in_box = None
            continue
        if not line.strip():
            if in_p: out.append("</p>"); in_p = False
            if in_ul: out.append(f"</{ul_tag}>"); in_ul = False
            continue
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            if in_p: out.append("</p>"); in_p = False
            if in_ul: out.append(f"</{ul_tag}>"); in_ul = False
            level = len(m.group(1))
            content = format_inline(m.group(2))
            slug = re.sub(r"[^a-z0-9]+", "-", m.group(2).lower()).strip("-")[:60]
            out.append(f'<h{level} id="{slug}">{content}</h{level}>')
            continue
        if line.startswith("> "):
            if in_p: out.append("</p>"); in_p = False
            out.append(f"<blockquote>{format_inline(line[2:])}</blockquote>")
            continue
        if re.match(r"^[-*]\s", line):
            if in_p: out.append("</p>"); in_p = False
            if not in_ul:
                out.append("<ul>"); in_ul = True; ul_tag = "ul"
            out.append(f"<li>{format_inline(line[2:])}</li>")
            continue
        m2 = re.match(r"^(\d+)\.\s+(.+)$", line)
        if m2:
            if in_p: out.append("</p>"); in_p = False
            if not in_ul:
                out.append("<ol>"); in_ul = True; ul_tag = "ol"
            out.append(f"<li>{format_inline(m2.group(2))}</li>")
            continue
        if in_ul:
            out.append(f"</{ul_tag}>"); in_ul = False
        if not in_p:
            out.append("<p>"); in_p = True
        out.append(format_inline(line))
    if in_p: out.append("</p>")
    if in_ul: out.append(f"</{ul_tag}>")
    if in_box:
        if in_ans: out.append("</details>")
        out.append("</details>" if in_box == "box-answer" else "</div>")
    return "\n".join(out)


def build_toc(html):
    items = []
    for m in re.finditer(r'<(h[23])\s+id="([^"]+)">([^<]+)</\1>', html):
        items.append((m.group(1), m.group(2), m.group(3)))
    return items


HEAD_SCRIPT = """<script>
function toggleAllAnswers() {
  var btn = document.getElementById('ans-toggle-all');
  var allDetails = document.querySelectorAll('details.box-answer');
  var anyClosed = Array.from(allDetails).some(function(d){ return !d.open; });
  allDetails.forEach(function(d){ d.open = anyClosed; });
  btn.textContent = anyClosed ? '🔽 全部收起答案' : '📖 全部展开答案';
}
</script>"""


def page_html(title, body, toc_sidebar):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} · CET-4 Archive</title>
<link rel="stylesheet" href="./style.css">
{HEAD_SCRIPT}
</head>
<body>
<header>
  <h1>CET-4 Archive</h1>
  <p class="tagline">{escape(title)}</p>
  <nav>
    <a href="./index.html">← 首页</a>
    <button id="ans-toggle-all" onclick="toggleAllAnswers()" style="background:transparent;border:1px solid rgba(255,216,156,0.4);color:#ffd89c;padding:4px 14px;border-radius:4px;font-size:0.85rem;cursor:pointer;font-family:inherit;margin-left:8px;">📖 全部展开答案</button>
  </nav>
</header>
<div class="layout">
{toc_sidebar}
<main class="textbook">
{body}
</main>
</div>
<footer>
  <p>本站所有题目均为站长原创的仿真练习,**不复现教育部考试中心真题**。真题请购买官方授权出版物。</p>
</footer>
</body>
</html>
"""


def main():
    if not os.path.isdir(SRC_DIR):
        os.makedirs(SRC_DIR, exist_ok=True)
    pages = sorted(f for f in os.listdir(SRC_DIR) if f.endswith(".md"))
    toc = []
    for fn in pages:
        path = os.path.join(SRC_DIR, fn)
        md = open(path, encoding="utf-8").read()
        title_match = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
        title_text = title_match.group(1) if title_match else fn
        slug = fn.replace(".md", "")
        html_body = md_to_html(md)
        toc_items = build_toc(html_body)
        toc_sidebar = '<aside class="toc-sidebar"><h3>本页目录</h3><ul>'
        for level, sid, txt in toc_items:
            cls = "h2" if level == "h2" else "h3"
            toc_sidebar += f'<li><a class="{cls}" href="#{sid}">{escape(txt)}</a></li>'
        toc_sidebar += "</ul></aside>"
        with open(os.path.join(OUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(page_html(title_text, html_body, toc_sidebar))
        toc.append({"slug": slug, "title": title_text, "chars": len(md)})
        print(f"built {slug}.html ({len(md)} chars md)")
    # index
    PAGE_DESC = {
        "2024-06": "2024 年 6 月考试 — 题型结构 / 考点话题 / 原创仿真模拟卷 / 答案解析",
        "2024-12": "2024 年 12 月考试 — 同上",
        "2025-06": "2025 年 6 月考试 — 同上",
        "2025-12": "2025 年 12 月考试 — 同上",
        "2026-06": "2026 年 6 月考试 — 同上",
        "methodology": "解题方法论 — 写作模板 / 翻译四步法 / 阅读定位 / 听力技巧",
        "vocabulary": "高频核心词汇表 — 4500 词分类索引 + 例句",
    }
    toc_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CET-4 Archive · 英语四级备考站</title>
<link rel="stylesheet" href="./style.css">
</head>
<body>
<header>
  <h1>CET-4 Archive</h1>
  <p class="tagline">2024 至今英语四级备考资料站 — 题型 / 考点 / 原创仿真模拟 / 方法论</p>
</header>
<main class="textbook-toc">
<h2>历次考试</h2>
<ul class="ch-list">
"""
    for t in toc:
        desc = PAGE_DESC.get(t["slug"], "")
        toc_html += (f'<li><a href="./{t["slug"]}.html">{escape(t["title"])}</a>'
                     f' <span class="meta">({t["chars"]:,} 字符)</span>'
                     f'<div class="ch-desc">{escape(desc)}</div></li>\n')
    toc_html += """</ul>
<h2>编写说明</h2>
<ul>
<li>本站所有题目均为站长 <strong>原创的 CET-4 风格仿真练习</strong>,不复现教育部考试中心真题原文(版权所有)</li>
<li>真题请购买新东方 / 华研外语 / 星火等出版社的官方授权题集</li>
<li>每场考试页面含:题型结构 + 当次考点话题方向 + 4 部分自创模拟卷 + 折叠答案解析 + 官方真题购买指引</li>
<li>共通方法论页 + 4500 高频词汇分类索引</li>
<li>点击右上角 <strong>"📖 全部展开答案"</strong> 一键查看所有解析(再点收起)</li>
</ul>
</main>
<footer>
  <p>站长原创备考资料 · 2026-05</p>
</footer>
</body>
</html>
"""
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(toc_html)
    print("built index.html")


if __name__ == "__main__":
    main()
