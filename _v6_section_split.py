"""v6: 给 19 套 paper HTML 加题型分区 Section 标题. 让用户清晰看到听力/阅读/翻译/写作分块.
按老大 2026-05-28 12:55 "题目哪个部分请分好" 指令.

CET-4 题型分布:
- Q1-Q7   听力 Section A (短篇新闻 7 题)
- Q8-Q15  听力 Section B (长对话 8 题, 2 段 ×4)
- Q16-Q25 听力 Section C (听力篇章 10 题, 3 段)
- Q26-Q35 阅读 Section A (选词填空 15 选 10)
- Q36-Q45 阅读 Section B (长篇阅读匹配 10 题)
- Q46-Q55 阅读 Section C (仔细阅读 2 篇 ×5)
- 翻译 (1 段, textarea)
- 写作 (1 段, textarea)
"""
import os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
    (1,  '🔊 Part Ⅱ Listening Comprehension', '听力理解 (25 min · 25 题 · 248.5 分)'),
    (1,  '  Section A · 短篇新闻 News Report', '7 题 · 题 1-7 · 3 篇短文每篇 2-3 题'),
    (8,  '  Section B · 长对话 Long Conversation', '8 题 · 题 8-15 · 2 段对话每段 4 题'),
    (16, '  Section C · 听力篇章 Passage', '10 题 · 题 16-25 · 3 篇短文每篇 3-4 题'),
    (26, '📖 Part Ⅲ Reading Comprehension', '阅读理解 (40 min · 30 题 · 248.5 分)'),
    (26, '  Section A · 选词填空 Banked Cloze', '10 题 · 题 26-35 · 15 选 10'),
    (36, '  Section B · 长篇阅读匹配 Passage Matching', '10 题 · 题 36-45'),
    (46, '  Section C · 仔细阅读 Careful Reading', '10 题 · 题 46-55 · 2 篇短文每篇 5 题'),
]

SECTION_BANNER_TPL = '''<div style="background:linear-gradient(135deg,#1e40af,#0e7490);color:white;padding:14px 18px;border-radius:8px;margin:24px 0 12px;box-shadow:0 2px 8px rgba(30,64,175,0.2);">
  <h2 style="margin:0;color:white;font-size:1.25rem;border:none;padding:0;">{title}</h2>
  <p style="margin:4px 0 0;color:#dbeafe;font-size:0.9rem;">{sub}</p>
</div>
'''

TRANS_BANNER = '''<div style="background:linear-gradient(135deg,#15803d,#22c55e);color:white;padding:14px 18px;border-radius:8px;margin:24px 0 12px;box-shadow:0 2px 8px rgba(21,128,61,0.2);">
  <h2 style="margin:0;color:white;font-size:1.25rem;border:none;padding:0;">🌐 Part Ⅳ Translation</h2>
  <p style="margin:4px 0 0;color:#dcfce7;font-size:0.9rem;">翻译 (30 min · 1 段 · 106.5 分 · 段落汉译英 140-160 字)</p>
</div>
'''

WRITE_BANNER = '''<div style="background:linear-gradient(135deg,#9333ea,#c026d3);color:white;padding:14px 18px;border-radius:8px;margin:24px 0 12px;box-shadow:0 2px 8px rgba(147,51,234,0.2);">
  <h2 style="margin:0;color:white;font-size:1.25rem;border:none;padding:0;">✍ Part Ⅰ Writing</h2>
  <p style="margin:4px 0 0;color:#fae8ff;font-size:0.9rem;">写作 (30 min · 1 篇议论文 · 106.5 分 · 120-180 词)</p>
</div>
'''


def patch_html(html):
    # 1) 修旧 notice (本地私人 → 学习交流)
    html = re.sub(
        r'<div class="notice"[^>]*>\s*此页面由 extract\.py[^<]*</div>',
        '<div class="notice" style="background:#dbeafe;color:#1e40af;padding:10px 14px;border-radius:6px;margin:10px 0;font-size:0.92rem;">💡 学习交流站 · 题目按 CET-4 标准 4 大题型分区. 点 ABCD 单选作答, 写作翻译填 textarea, 最后提交批改.</div>',
        html, count=1
    )

    # 2) 在每个 Section 起始题前注入 Section banner
    # 找到 data-qid="Q<n>" 的 div, 在它之前插入 banner
    seen_starts = set()
    for q_start, title, sub in SECTIONS:
        if q_start in seen_starts:
            # 同一 Q 起始的多 banner (e.g. Q1 听力总标题 + Section A) 用累加
            continue
        # Q1 比较特殊 - 听力大区 + Section A 一起
        pass

    # 用更直接的方式: 在 paper 内, 找各题号位置, 插入对应 banner
    # listening 大区 + section A 一起放在 Q1 之前
    listen_banner = SECTION_BANNER_TPL.format(title=SECTIONS[0][1], sub=SECTIONS[0][2]) + \
                    SECTION_BANNER_TPL.format(title=SECTIONS[1][1], sub=SECTIONS[1][2])
    sec_b = SECTION_BANNER_TPL.format(title=SECTIONS[2][1], sub=SECTIONS[2][2])
    sec_c = SECTION_BANNER_TPL.format(title=SECTIONS[3][1], sub=SECTIONS[3][2])
    reading_banner = SECTION_BANNER_TPL.format(title=SECTIONS[4][1], sub=SECTIONS[4][2]) + \
                     SECTION_BANNER_TPL.format(title=SECTIONS[5][1], sub=SECTIONS[5][2])
    read_b = SECTION_BANNER_TPL.format(title=SECTIONS[6][1], sub=SECTIONS[6][2])
    read_c = SECTION_BANNER_TPL.format(title=SECTIONS[7][1], sub=SECTIONS[7][2])

    insertions = [
        (1, listen_banner),
        (8, sec_b),
        (16, sec_c),
        (26, reading_banner),
        (36, read_b),
        (46, read_c),
    ]

    for qid, banner in insertions:
        pattern = re.compile(rf'(<div class="q"\s+data-qid="Q{qid}">)', re.IGNORECASE)
        new_html, n = pattern.subn(banner + r'\1', html, count=1)
        if n > 0:
            html = new_html

    # 翻译/写作 banner — 一般在题 55 之后. 找 "Part Ⅳ Translation" 或 "translation" textarea 之前
    # 简单方案: 在含 'name="translation"' 或 'name="writing"' 的元素之前插入
    html = re.sub(r'(<[^>]+name="translation"|<[^>]+id="translation"|Part\s*[IVⅣ4]+\s*Translation)', TRANS_BANNER + r'\1', html, count=1, flags=re.IGNORECASE)
    html = re.sub(r'(<[^>]+name="writing"|<[^>]+id="writing"|Part\s*[IVⅠ1]+\s*Writing)', WRITE_BANNER + r'\1', html, count=1, flags=re.IGNORECASE)

    return html


count = 0
for fname in sorted(os.listdir(ROOT)):
    if not fname.startswith('paper-') or not fname.endswith('.html'):
        continue
    fpath = os.path.join(ROOT, fname)
    with open(fpath, encoding='utf-8') as f:
        html = f.read()
    new = patch_html(html)
    if new != html:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(new)
        count += 1
        # check how many banners inserted
        banner_count = new.count('linear-gradient(135deg')
        print(f'  + {fname} ({banner_count} banners)')
    else:
        print(f'  - {fname} (no change)')

print(f'\nDONE: {count} papers patched')
