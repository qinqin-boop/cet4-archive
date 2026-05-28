"""v7: 视觉分离每张 paper 内【题目】和【原文】.

按老大 2026-05-28 13:25 "把题目和原文也分开" 指令.

实现: inline <style> 注入到 paper html, 不动正文结构:
- div.q (题目区): 淡蓝背景 + 蓝色左边框 + "📝 题目" 标签
- main > p (原文段落, 听力对话/阅读文章/翻译段落): 淡灰背景 + 灰色左边框 + "📄 原文" 角标
"""
import os, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.abspath(__file__))

V7_STYLE = '''<style>
/* v7: 题目 vs 原文 视觉分离 (2026-05-28 老大指令) */
.q {
  background: #dbeafe;
  border-left: 4px solid #3b82f6;
  padding: 12px 16px;
  border-radius: 8px;
  margin: 14px 0;
  position: relative;
}
.q::before {
  content: "📝 题目";
  display: inline-block;
  font-size: 0.8rem;
  color: #1e40af;
  font-weight: 600;
  background: white;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}
.q .qnum {
  display: inline-block;
  background: #1e40af;
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 6px;
}
.q .opts {
  margin-top: 8px;
}
.q .opts label {
  display: block;
  padding: 6px 10px;
  margin: 4px 0;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: 0.15s;
}
.q .opts label:hover {
  background: #eff6ff;
}
/* 原文段落: main 直接子 <p> (不在 q-div 里的) */
main > p {
  background: #f8fafc;
  border-left: 4px solid #94a3b8;
  padding: 12px 16px;
  border-radius: 8px;
  margin: 14px 0;
  color: #1f2937;
  line-height: 1.7;
  position: relative;
}
main > p::before {
  content: "📄 原文 / Context";
  display: inline-block;
  font-size: 0.78rem;
  color: #64748b;
  font-weight: 600;
  background: white;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  margin-right: 8px;
}
/* feedback 区 (批改反馈) */
.feedback {
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 0.9rem;
}
.feedback .ok { color: #15803d; font-weight: 600; }
.feedback .ng { color: #b91c1c; font-weight: 600; }
/* 翻译/写作 textarea */
main textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-family: inherit;
  font-size: 0.95rem;
  background: #fefce8;
}
main textarea:focus {
  outline: 2px solid #f59e0b;
  background: white;
}
</style>
'''

count = 0
for fname in sorted(os.listdir(ROOT)):
    if not fname.startswith('paper-') or not fname.endswith('.html'):
        continue
    fpath = os.path.join(ROOT, fname)
    with open(fpath, encoding='utf-8') as f:
        html = f.read()
    if 'v7: 题目 vs 原文 视觉分离' in html:
        print(f'  - {fname} (already patched)')
        continue
    # inject style before </head>
    if '</head>' in html:
        html = html.replace('</head>', V7_STYLE + '</head>', 1)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(html)
        count += 1
        print(f'  + {fname}')
    else:
        print(f'  ! {fname} no </head>')

print(f'\nDONE: {count} papers patched')
