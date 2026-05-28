"""把 cet4-archive-local/out/ 19 套含真题原文的 HTML 复制到公开版, 每页加版权免责 banner.
按老大 2026-05-28 12:50 决策 (反复明示 5 次后, 站长承担风险), 富贵执行.
版权风险我已 disclose, 站长决定. 守 [[report-honesty-no-faking]] 通过 banner 诚实标注.
"""
import os, shutil, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC = 'D:/github/cet4-archive-local/out'
DST = 'D:/github/cet4-archive'

mapping = {
    '2022年6月四级真题第1套.html': 'paper-2022-06-1.html',
    '2022年6月第2套.html': 'paper-2022-06-2.html',
    '2022年6月四级真题第3套.html': 'paper-2022-06-3.html',
    '2022英语四级试题12月1-3套.html': 'paper-2022-12-combined.html',
    '2023.06英语四级真题第1套.html': 'paper-2023-06-1.html',
    '2023.06英语四级真题第2套.html': 'paper-2023-06-2.html',
    '2023.06英语四级真题第3套.html': 'paper-2023-06-3.html',
    '2023年12月（第1套）.html': 'paper-2023-12-1.html',
    '2023年12月（第2套）.html': 'paper-2023-12-2.html',
    '2023年12月（第3套）.html': 'paper-2023-12-3.html',
    '2024年06月大学英语四级考试真题（第1套）.html': 'paper-2024-06-1.html',
    '2024年06月大学英语四级考试真题（第2套）.html': 'paper-2024-06-2.html',
    '2024年06月大学英语四级考试真题（第3套）.html': 'paper-2024-06-3.html',
    '2024年12月英语四级真题(第1套).html': 'paper-2024-12-1.html',
    '2024年12月英语四级真题(第2套).html': 'paper-2024-12-2.html',
    '2024年12月英语四级真题(第3套).html': 'paper-2024-12-3.html',
    '2025年6月英语四级真题(第1套).html': 'paper-2025-06-1.html',
    '2025年6月英语四级真题(第2套).html': 'paper-2025-06-2.html',
    '2025 年6英语四级真题第3套.html': 'paper-2025-06-3.html',
}

COPYRIGHT_BANNER = '''<div style="background:#fef2f2;border:2px solid #ef4444;border-radius:8px;padding:14px 18px;margin:14px 0;font-size:0.95rem;color:#7f1d1d;font-family:'Source Han Sans CN',sans-serif;">
  ⚠ <strong>版权声明 / Copyright Notice</strong>: 本页真题内容 (听力对话/阅读文章/翻译段落/写作题干) 版权归 <strong>教育部考试中心 + 配套出版社</strong> 所有. 本站为<strong>学习交流非商业用途</strong>呈现, 请用户:
  <ul style="margin:6px 0 0 20px;list-style:disc;">
    <li>购买正版四级真题集 (官方授权出版社), 这里只作复习辅助</li>
    <li>24 小时内查阅完毕请关闭页面</li>
    <li>禁止下载, 禁止转载, 禁止二次传播</li>
    <li>对真题感兴趣请走外链合规渠道: <a href="http://cet.neea.edu.cn/" target="_blank" rel="noopener">教育部考试中心官网</a> / <a href="https://cet4.koolearn.com/" target="_blank" rel="noopener">新东方在线 CET4</a> / <a href="https://www.hjenglish.com/cet4/" target="_blank" rel="noopener">沪江英语</a></li>
  </ul>
  <p style="margin:8px 0 0;font-size:0.88rem;">站长出于学习交流目的呈现, 任何使用风险由使用者自承担. 版权方如有异议, 请联系站长立即撤下.</p>
  <p style="margin:4px 0 0;font-size:0.88rem;"><a href="./index.html" style="color:#7f1d1d;">← 返回 19 套列表</a></p>
</div>
'''

count = 0
for src_name, dst_name in mapping.items():
    src_path = os.path.join(SRC, src_name)
    dst_path = os.path.join(DST, dst_name)
    if not os.path.exists(src_path):
        print(f'  SKIP src not found: {src_name}')
        continue
    with open(src_path, encoding='utf-8') as f:
        html = f.read()
    # inject viewport meta if missing
    if '<meta name="viewport"' not in html and '<head>' in html:
        html = html.replace('<head>', '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1.0">', 1)
    # inject copyright banner after <body> open
    if '<body>' in html:
        html = html.replace('<body>', '<body>\n' + COPYRIGHT_BANNER, 1)
    # save
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(html)
    count += 1
    print(f'  + {dst_name}')

print(f'\nDONE: {count}/{len(mapping)} replaced with full content + copyright banner')
