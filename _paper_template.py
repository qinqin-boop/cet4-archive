"""CET-4 原创仿真试卷生成器 v3 - 7 套 + 作答系统 + 自动批改."""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · CET-4 原创仿真试卷</title>
<link rel="stylesheet" href="./style.css">
<script>
// TTS 朗读
var currentUtter = null;
var currentBtn = null;
function play(btn) {{
  var txt = btn.parentElement.querySelector('.script-text').textContent;
  if (currentUtter) {{
    speechSynthesis.cancel();
    if (currentBtn) currentBtn.textContent = '🔊 播放朗读';
    var same = (currentBtn === btn);
    currentUtter = null; currentBtn = null;
    if (same) return;
  }}
  var u = new SpeechSynthesisUtterance(txt);
  u.lang = 'en-US'; u.rate = 0.92;
  var vs = speechSynthesis.getVoices();
  var ev = vs.find(function(v){{return v.lang.startsWith('en');}});
  if (ev) u.voice = ev;
  u.onend = function(){{ if (currentBtn) currentBtn.textContent = '🔊 播放朗读'; currentUtter = null; currentBtn = null; }};
  speechSynthesis.speak(u);
  currentUtter = u; currentBtn = btn;
  btn.textContent = '⏸ 停止';
}}

// 自动批改
window.ANSWERS = {answers_json};
function submitPaper() {{
  var qs = document.querySelectorAll('.q[data-qid]');
  var correct = 0, total = 0;
  qs.forEach(function(qEl){{
    var qid = qEl.getAttribute('data-qid');
    var correctAns = window.ANSWERS[qid];
    if (correctAns === undefined) return;
    total++;
    var selected = qEl.querySelector('input[type="radio"]:checked');
    var userAns = selected ? selected.value : '(未作答)';
    var isCorrect = (userAns === correctAns);
    if (isCorrect) correct++;
    qEl.classList.remove('correct','wrong');
    qEl.classList.add(isCorrect ? 'correct' : 'wrong');
    var feedback = qEl.querySelector('.feedback');
    if (feedback) {{
      feedback.style.display = 'block';
      feedback.innerHTML = isCorrect
        ? '<span class="ok">✓ 答对了!</span>'
        : '<span class="ng">✗ 答错. 你选了 <b>'+userAns+'</b>, 正确答案 <b>'+correctAns+'</b></span>';
    }}
    var ans = qEl.querySelector('.answer-block');
    if (ans) ans.style.display = 'block';
  }});
  // 主观题(翻译/写作) - 用户写完后展开标准答案对比
  document.querySelectorAll('.q.subjective').forEach(function(qEl){{
    var ans = qEl.querySelector('.answer-block');
    if (ans) ans.style.display = 'block';
    qEl.classList.add('submitted');
  }});
  // 总分
  var bar = document.getElementById('score-bar');
  if (bar) {{
    bar.style.display = 'block';
    var pct = total > 0 ? Math.round(correct/total*100) : 0;
    bar.innerHTML = '<strong>客观题得分:</strong> ' + correct + ' / ' + total + ' (' + pct + '%)  &nbsp;|&nbsp;  主观题答案已展开供对比';
  }}
  // 滚到顶
  window.scrollTo({{top:0, behavior:'smooth'}});
}}

function resetPaper() {{
  document.querySelectorAll('input[type="radio"]').forEach(function(r){{ r.checked = false; }});
  document.querySelectorAll('textarea').forEach(function(t){{ t.value = ''; }});
  document.querySelectorAll('.q').forEach(function(q){{ q.classList.remove('correct','wrong','submitted'); }});
  document.querySelectorAll('.feedback').forEach(function(f){{ f.style.display='none'; f.innerHTML=''; }});
  document.querySelectorAll('.answer-block').forEach(function(a){{ a.style.display='none'; }});
  var bar = document.getElementById('score-bar');
  if (bar) bar.style.display = 'none';
  window.scrollTo({{top:0, behavior:'smooth'}});
}}
</script>
</head>
<body>
<header>
  <h1>📄 {title}</h1>
  <p class="sub">CET-4 原创仿真试卷 · 作答 → 批改 → 看解析</p>
  <nav>
    <a href="./index.html">← 试卷列表</a>
  </nav>
</header>
<main>
<div class="notice">本卷所有题目均为站长原创仿真练习,<strong>不复现教育部考试中心真题原文</strong>。先作答 → 点底部「提交批改」→ 系统自动判分 + 显示标准答案与解析。</div>
<div id="score-bar" class="score-bar" style="display:none;"></div>
"""

FOOTER_BTNS = """
<div class="action-bar">
  <button class="btn-submit" onclick="submitPaper()">✅ 提交批改</button>
  <button class="btn-reset" onclick="resetPaper()">🔄 重置</button>
</div>
</main>
<footer><p>CET-4 原创仿真试卷 · {title}</p></footer>
</body>
</html>
"""


# === 题库 (全部站长原创, 不复现真题) ===
LISTEN = [
    {"script": "W: Have you decided which elective course to take next semester? M: I'm torn between Modern Art History and Introduction to Data Science. W: Why not pick the one that helps your future career? M: That makes sense. I'll go with data science then.",
     "q": "Which course will the man choose?",
     "opts": [("A","Modern Art History"),("B","Introduction to Data Science"),("C","Neither"),("D","Both")],
     "ans": "B", "exp": "男士最后明确 I'll go with data science。"},
    {"script": "M: I noticed you've been jogging every morning recently. W: Yes, I started a fitness plan three weeks ago. I want to run a half-marathon in October. M: That's impressive. Mind if I join you tomorrow morning? W: Not at all. Meet me at the park gate at six.",
     "q": "What will the two speakers do tomorrow morning?",
     "opts": [("A","Watch a marathon"),("B","Jog together"),("C","Have breakfast"),("D","Visit a park")],
     "ans": "B", "exp": "男士问 join,女士同意。"},
    {"script": "W: The library will be renovated starting next month. Where are we supposed to study? M: I heard the old gymnasium will be temporarily converted into a study area. W: Really? That's a long walk from the dorm. M: They'll run a shuttle bus every twenty minutes.",
     "q": "How will students travel to the temporary study area?",
     "opts": [("A","On foot"),("B","By bicycle"),("C","By shuttle bus"),("D","By taxi")],
     "ans": "C", "exp": "shuttle bus every twenty minutes。"},
    {"script": "M: My laptop has been running really slow lately. I'm thinking of buying a new one. W: Have you tried clearing the cache and uninstalling unused apps first? M: Not yet. Do you think that will make a real difference? W: It often does. Save your money before you buy anything new.",
     "q": "What does the woman suggest the man do?",
     "opts": [("A","Buy a new laptop"),("B","Try maintenance first"),("C","Borrow her laptop"),("D","Visit a repair shop")],
     "ans": "B", "exp": "Save your money before you buy anything new。"},
    {"script": "W: I'm submitting my thesis on Friday. Could you read the introduction tonight? M: Sorry, I have an exam tomorrow morning and need to focus. How about Thursday afternoon? W: That cuts it close, but it should work. M: Email it over and I'll give you detailed notes.",
     "q": "When will the man read the woman's introduction?",
     "opts": [("A","Tonight"),("B","Tomorrow morning"),("C","Thursday afternoon"),("D","Friday")],
     "ans": "C", "exp": "Thursday afternoon。"},
    {"script": "M: Did you finish the reading list for tomorrow's seminar? W: Honestly, I only got through half. The third article was so technical that I had to look up every other word. M: I had the same problem. Maybe we should form a study group to share notes. W: Great idea. Let's invite Lisa and Tom too.",
     "q": "What does the woman agree to do?",
     "opts": [("A","Skip the seminar"),("B","Form a study group"),("C","Read alone"),("D","Email the professor")],
     "ans": "B", "exp": "Great idea + Let's invite Lisa and Tom too。"},
    {"script": "W: I read that universities are now offering short, intensive courses during winter breaks. M: Yes, mini-terms. They typically last two to four weeks and focus on one topic. W: Sounds productive but exhausting. M: Some students love it for the focus, others find the pace too fast.",
     "q": "How long does a typical mini-term last?",
     "opts": [("A","One week"),("B","Two to four weeks"),("C","Six weeks"),("D","A full semester")],
     "ans": "B", "exp": "two to four weeks 直接命中。"},
    {"script": "M: I'm thinking of moving from the city to a smaller town after graduation. W: Won't that limit your job opportunities? M: Maybe, but housing is so much cheaper, and I value my free time more than a top salary. W: Different priorities, that's fair.",
     "q": "Why is the man considering moving?",
     "opts": [("A","To find more jobs"),("B","For cheaper housing and free time"),("C","To be near family"),("D","For better weather")],
     "ans": "B", "exp": "housing is so much cheaper + value my free time。"},
    {"script": "W: My phone battery dies before noon every day. M: How old is it? W: Three years. The screen is fine, but the battery just doesn't hold a charge. M: You could replace just the battery at a repair shop for much less than buying a new phone.",
     "q": "What does the man recommend?",
     "opts": [("A","Buying a new phone"),("B","Replacing just the battery"),("C","Carrying a power bank"),("D","Sending to manufacturer")],
     "ans": "B", "exp": "replace just the battery at a repair shop。"},
    {"script": "M: I want to start volunteering on weekends. Any suggestions? W: There's a community garden project that teaches low-income families to grow vegetables. M: That sounds rewarding. How many hours per week? W: Just three or four. They want consistent help rather than long shifts.",
     "q": "What volunteer commitment does the program prefer?",
     "opts": [("A","One full day each week"),("B","Long occasional shifts"),("C","Consistent 3-4 hours per week"),("D","Monthly meetings only")],
     "ans": "C", "exp": "consistent help + three or four hours per week。"},
    {"script": "W: Did you go to the career fair yesterday? M: Yes, but it was so crowded that I only managed to talk to two companies. W: Which ones impressed you? M: A small startup actually. The founder explained their product better than any big-firm recruiter.",
     "q": "Which company impressed the man most?",
     "opts": [("A","A small startup"),("B","A large corporation"),("C","A government agency"),("D","A consulting firm")],
     "ans": "A", "exp": "A small startup actually + founder explained better。"},
    {"script": "M: I haven't seen you in the cafeteria all week. W: I've been packing lunch from home to save money. M: How much are you saving? W: About fifty yuan a week. It adds up to over two thousand a year. M: That's a smart move. I might try it.",
     "q": "Why is the woman packing lunch?",
     "opts": [("A","She dislikes cafeteria food"),("B","To save about 50 yuan per week"),("C","She has dietary restrictions"),("D","Her schedule changed")],
     "ans": "B", "exp": "save money + fifty yuan a week 直接命中。"},
]

READING = [
    {"title": "Reading on Paper vs Screen",
     "passage": "A growing body of research suggests that the medium we read in shapes how deeply we understand. When students read long passages on paper, they tend to recall main arguments and supporting details with greater accuracy than when they read on a screen. Paper offers spatial cues — a reader remembers that a key idea appeared near the top of the left page — that screens lack. Scrolling encourages skimming, while turning pages encourages reflection. Screen reading is not without merits: searchability and digital annotation make it superior for research. The best approach matches medium to purpose: deep comprehension demands paper; fact lookup favors a tablet.",
     "qs": [
       ("research-suggests","What does research suggest about reading?",
        [("A","Paper is always better"),("B","Screen reading recalls more"),("C","Paper produces better recall of arguments"),("D","No difference")],
        "C", "首句直接给结论。"),
       ("why-paper","Why does paper assist comprehension?",
        [("A","Cheaper"),("B","Spatial cues + page-turning reflection"),("C","Higher resolution"),("D","Easier to carry")],
        "B", "原文两个原因。"),
       ("screen-good-for","For which task is screen reading well-suited?",
        [("A","Reading a novel"),("B","Memorizing poetry"),("C","Fact lookup"),("D","Long-term retention")],
        "C", "fact lookup favors a tablet。"),
       ("overall","Author's overall view?",
        [("A","Stop using tablets"),("B","Match medium to purpose"),("C","Screens are obsolete"),("D","Always read on paper")],
        "B", "match the medium to the reading purpose。"),
     ]},
    {"title": "Remote Work and Cities",
     "passage": "The rapid spread of remote work has changed how cities function. Office vacancy rates in major financial districts have reached levels not seen in decades, while suburban housing markets have boomed. Workers who once commuted ninety minutes are buying larger homes in quieter areas. Coffee shops and dry cleaners that depended on office foot traffic are struggling. Hybrid work — two or three days in office — is settling in as a new norm. Researchers find fully remote workers report higher loneliness, while fully in-office workers report less flexibility. A balanced rhythm offers the best of both worlds.",
     "qs": [
       ("vacancy","What is happening to office vacancy rates?",
        [("A","Falling to historic lows"),("B","Staying constant"),("C","Reaching levels not seen in decades"),("D","Unclear")],
        "C", "第二句明确。"),
       ("why-suburban","Why are workers buying suburban homes?",
        [("A","Better schools"),("B","Prioritize space and quieter areas"),("C","Cities banned new construction"),("D","Companies moved")],
        "B", "larger homes in quieter areas。"),
       ("struggling","Which businesses are struggling?",
        [("A","Online retailers"),("B","Coffee shops, dry cleaners near offices"),("C","Construction"),("D","Transit")],
        "B", "直接列举。"),
       ("hybrid","What is hybrid work?",
        [("A","Five days in office"),("B","Fully remote"),("C","2-3 days in office per week"),("D","Weekends only")],
        "C", "原文明确。"),
     ]},
    {"title": "Compound Interest for Young Investors",
     "passage": "For most young adults, the most powerful tool for building long-term wealth is the boringly simple habit of saving a consistent fraction of every paycheck and investing in low-cost index funds. Modest sums invested early grow dramatically over decades. Consider Anna who starts saving 200 dollars a month at age 22 for 43 years; Ben waits until 35 then contributes 400 a month for 30 years. Despite Ben contributing more, Anna ends up with substantially more because her money had more years to compound. The trickiest part of investing is psychological — staying invested during market downturns matters more than picking the right stocks.",
     "qs": [
       ("most-powerful","Most powerful wealth tool for young adults?",
        [("A","Stock picking"),("B","Real estate"),("C","Consistent saving + index funds"),("D","Side business")],
        "C", "原文首句明确。"),
       ("why-anna","Why does Anna end up with more savings?",
        [("A","Higher salary"),("B","More years to compound"),("C","Different fund choices"),("D","Lower fees")],
        "B", "money had more years to compound。"),
       ("anna-age","At what age did Anna start saving?",
        [("A","20"),("B","22"),("C","25"),("D","30")],
        "B", "原文 age 22。"),
       ("trickiest","What is the trickiest part of investing?",
        [("A","Math"),("B","Psychological - staying invested"),("C","Paperwork"),("D","Choosing brokers")],
        "B", "trickiest part of investing is psychological。"),
     ]},
    {"title": "AI and Job Markets",
     "passage": "The rapid advance of artificial intelligence is transforming the job market faster than earlier waves of automation. Unlike mechanical robots that replaced manual labor, modern AI can draft emails, summarize legal documents, and write computer code, threatening white-collar work once considered safe. However, AI tends to take over narrow sub-tasks rather than entire jobs. A copywriter may still be needed for creative direction even as AI generates first drafts. Workers most likely to thrive combine technical literacy with soft skills — communication, empathy, creative problem-solving.",
     "qs": [
       ("how-different","How is modern AI different from earlier automation?",
        [("A","Replaces manual labor only"),("B","Threatens white-collar work too"),("C","Slower"),("D","Only affects students")],
        "B", "原文对比说明。"),
       ("entire-jobs","Will AI eliminate entire jobs?",
        [("A","Yes, all routine jobs"),("B","Mostly takes over sub-tasks, jobs redesigned"),("C","No effect"),("D","Only manual jobs")],
        "B", "narrow sub-tasks rather than entire jobs。"),
       ("thrive-skills","Skills that help workers thrive?",
        [("A","Only coding"),("B","Technical literacy + soft skills"),("C","Only management"),("D","Only languages")],
        "B", "combine technical literacy with soft skills。"),
       ("tone","Author's overall tone?",
        [("A","Entirely pessimistic"),("B","Nuanced - risks + opportunities"),("C","Entirely optimistic"),("D","Indifferent")],
        "B", "承认 threats 也指 redesigned。"),
     ]},
    {"title": "Lifelong Learning",
     "passage": "The skills that earn a comfortable salary today may be obsolete in a decade. Automation and shifting job markets mean a diploma at 22 is no longer a lifetime ticket. Lifelong learning has moved from a nice-to-have to an essential survival skill. Fortunately, free online courses, podcasts, and communities of practice offer expert content at almost no cost. The challenge is no longer access but discipline. Setting aside five hours a week for deliberate study keeps one relevant, curious, and confident over decades of change.",
     "qs": [
       ("why-lifelong","Why is lifelong learning more important now?",
        [("A","Diplomas last forever"),("B","Skills can become obsolete within a decade"),("C","Universities are free"),("D","Jobs require no learning")],
        "B", "may be obsolete in a decade。"),
       ("access","Is access the biggest challenge today?",
        [("A","Yes, too expensive"),("B","No, the challenge is discipline"),("C","Yes, no resources"),("D","Yes, slow internet")],
        "B", "challenge is no longer access but discipline。"),
       ("hours","What weekly time commitment is suggested?",
        [("A","20 hours"),("B","5 hours of deliberate study"),("C","1 hour"),("D","40 hours")],
        "B", "five hours a week。"),
       ("obsolete","'Obsolete' means closest to:",
        [("A","New"),("B","Outdated / no longer useful"),("C","Famous"),("D","Expensive")],
        "B", "obsolete = no longer useful。"),
     ]},
    {"title": "Sleep Quality vs Quantity",
     "passage": "For decades the popular advice was simply to get eight hours of sleep. Recent research suggests sleep quality matters as much as quantity. Two people sleeping the same hours may wake with very different alertness depending on how much deep sleep and REM sleep they completed. Deep sleep, when the body repairs tissue and consolidates memories, makes up roughly twenty percent of a healthy cycle. A sleep cycle disturbed by noise, alcohol, or late screens loses deep sleep first. Researchers recommend keeping the bedroom between 18 and 20 Celsius, avoiding caffeine after noon, and dimming screens an hour before bed.",
     "qs": [
       ("determine-alertness","According to the passage, what determines morning alertness?",
        [("A","Total hours slept"),("B","Quality of sleep cycles"),("C","Age"),("D","Daytime naps")],
        "B", "quality matters as much as quantity。"),
       ("deep-sleep","Deep sleep is associated with all EXCEPT:",
        [("A","Tissue repair"),("B","Memory consolidation"),("C","Rapid eye movement"),("D","~20% of cycle")],
        "C", "REM ≠ deep sleep。"),
       ("recommend","What is recommended for sleep quality?",
        [("A","Sleep 9 hours"),("B","Keep room 18-20C and avoid afternoon caffeine"),("C","Sleep with light on"),("D","Pull all-nighters")],
        "B", "原文直接列出。"),
       ("main-idea","Main idea?",
        [("A","8 hours necessary for all"),("B","Quality matters as much as quantity"),("C","Students need 9+ hours"),("D","REM is the only important stage")],
        "B", "主旨。"),
     ]},
    {"title": "Short-Video Habits",
     "passage": "Short-video apps have captured the attention of nearly every college student. The appeal is easy to understand: bite-sized clips offer instant entertainment, while algorithms make each video feel personally relevant. However, the cost is real. Many students find their attention spans shrinking and study sessions interrupted every few minutes. The solution is not to abandon short videos entirely but to use them with discipline — setting daily time limits, deleting apps during exam weeks, and treating short videos as rewards rather than default activities.",
     "qs": [
       ("appeal","Why do short videos attract students?",
        [("A","They are educational"),("B","Bite-sized clips + algorithm relevance"),("C","They are free"),("D","Teachers recommend them")],
        "B", "bite-sized + algorithm。"),
       ("cost","What negative effect is mentioned?",
        [("A","Hurt eyesight"),("B","Shrinking attention spans"),("C","Loss of sleep"),("D","Lower grades automatically")],
        "B", "attention spans shrinking。"),
       ("solution","Author's suggested solution?",
        [("A","Abandon completely"),("B","Use with discipline - limits + rewards"),("C","Use unlimited"),("D","Block at university level")],
        "B", "use them with discipline。"),
       ("treat","How should short videos be treated?",
        [("A","Default activity"),("B","Rewards rather than defaults"),("C","Replacement for study"),("D","Group activity only")],
        "B", "treating short videos as rewards rather than default activities。"),
     ]},
]

TRANS = [
    ("春节是中国最重要的传统节日,通常在公历一月底或二月初到来。家人无论身在何处都会回到家中,共享团圆饭、贴春联、放鞭炮。",
     "The Spring Festival is the most important traditional Chinese holiday, typically falling in late January or early February. Wherever family members may be, they return home to share a reunion dinner, paste spring couplets, and set off firecrackers.",
     "春联 spring couplets / 鞭炮 firecrackers。"),
    ("中国书法是一种独特的视觉艺术,有三千多年的历史。它不仅是书写汉字的方式,也是表达情感、修养身心的途径。",
     "Chinese calligraphy is a unique visual art with more than three thousand years of history. It is not merely a way to write Chinese characters but also a means of expressing emotions and cultivating the body and mind.",
     "笔锋 brush pressure / 留白 negative space。"),
    ("近年来,中国在人工智能领域取得了显著进展。从智能语音助手到自动驾驶汽车,人工智能正在改变人们的生活和工作方式。",
     "In recent years, China has made remarkable progress in artificial intelligence. From smart voice assistants to self-driving cars, AI is transforming the way people live and work.",
     "显著进展 remarkable progress。"),
    ("中医是中国传统医学,有数千年的历史。它包括针灸、推拿、中草药等多种治疗方法。中医强调人与自然的和谐。",
     "Traditional Chinese Medicine (TCM) is a system of medicine with thousands of years of history. It includes acupuncture, tuina massage, and herbal medicine. TCM emphasizes harmony between humans and nature.",
     "针灸 acupuncture / 中草药 herbal medicine。"),
    ("近年来,中国的高等教育发展迅速。越来越多的学生有机会进入大学,留学的人数也持续增长。",
     "Higher education in China has developed rapidly. An increasing number of students have the opportunity to attend university, and the number studying abroad continues to grow.",
     "留学 studying abroad / 持续增长 continues to grow。"),
    ("丝绸之路是古代连接中国与中亚、西亚乃至欧洲的贸易通道。它不仅是商品流通的道路,也是文化、宗教和技术交流的桥梁。",
     "The Silk Road was an ancient network of trade routes connecting China with Central Asia, West Asia, and Europe. More than a route for goods, it served as a bridge for cultural, religious, and technological exchange.",
     "丝绸之路 The Silk Road / 桥梁 served as a bridge for。"),
    ("过去三十年,中国的城市化进程加快,数亿人从农村迁入城市。这种大规模的人口流动既带来了经济增长,也带来了挑战。",
     "Over the past three decades, China's urbanization has accelerated, with hundreds of millions moving from rural areas to cities. This large-scale movement has brought both economic growth and challenges.",
     "城市化 urbanization。"),
    ("中国的茶文化源远流长。无论是日常待客还是商务洽谈,泡一壶好茶都是表达尊重的方式。",
     "Chinese tea culture has a long history. Whether welcoming guests in daily life or negotiating in business settings, brewing a good pot of tea is a way to show respect.",
     "茶文化 tea culture。"),
    ("故宫位于北京市中心,曾是中国明清两代二十四位皇帝的居所。它始建于一四〇六年,占地超过七十二万平方米,共有近九千间房屋。",
     "The Forbidden City, located in the heart of Beijing, was once the residence of twenty-four emperors of the Ming and Qing dynasties. Construction began in 1406. It covers more than 720,000 square meters with nearly 9,000 rooms.",
     "故宫 The Forbidden City / 明清 Ming and Qing dynasties。"),
    ("京剧是中国最具代表性的传统戏剧形式之一,已有两百多年历史。它融合了唱、念、做、打四种基本表现手法。",
     "Peking Opera is one of the most iconic traditional Chinese theatrical forms, with more than two hundred years of history. It combines four basic performance techniques: singing, speech, acting, and martial arts.",
     "京剧 Peking Opera。"),
]

WRITE = [
    ("Write an essay (120-180 words) on \"The Importance of Reading in University Life\".",
     "In an era flooded with short videos, reading remains an irreplaceable habit. First, books cultivate deep thinking, training us to follow long structured arguments rather than scattered snippets. Second, beyond textbooks, students should explore biographies, popular science, and classic novels to broaden their worldview. Finally, a daily reading habit can be built by allocating thirty minutes before sleep. In short, reading is not a luxury but the quietest, most cost-effective investment a student can make.",
     "三段式套路。"),
    ("Write an essay (120-180 words) on \"The Influence of Short Videos on College Students\".",
     "Short-video apps have captured the attention of nearly every college student. Their appeal is easy to understand: bite-sized clips offer instant entertainment. However, the cost is real - shrinking attention spans and interrupted study sessions. The solution is not to abandon them entirely but to use them with discipline: setting daily limits, deleting apps during exam weeks, and treating them as rewards rather than defaults.",
     "现象-原因-对策。"),
    ("Write an essay (120-180 words) on \"Balancing Study and Leisure in College Life\".",
     "College life is short and students often fail to balance study and leisure. Too much study leads to burnout; too much leisure damages GPA. A practical strategy is to schedule one fixed non-work day per week for hobbies and to protect a few hours of deep-work time each weekday with notifications off. Real balance is a sustainable rhythm one can maintain for years.",
     "平衡话题。"),
    ("Write an essay (120-180 words) on \"Why Volunteer Work Matters to Young People\".",
     "Volunteer work teaches young people what no classroom can. While lectures explain theories, volunteering puts students face to face with strangers whose lives differ from their own. From these encounters grow empathy and organizational skills. A simple example: a campus program where students teach elderly community members how to make video calls. Even one Saturday morning per month can shape character.",
     "具体例子。"),
    ("Write an essay (120-180 words) on \"Should Universities Limit AI Tools in Writing Assignments?\".",
     "AI writing tools have forced universities to ask: how much help is too much? Banning AI altogether seems unrealistic; the technology is already part of professional life. Yet unrestricted use risks producing graduates who cannot write a single original sentence under pressure. A reasonable middle path distinguishes between core writing courses where AI should be off-limits, and editing or research stages where AI can speed routine work.",
     "中间立场。"),
    ("Write an essay (120-180 words) on \"The Role of Sports in University Life\".",
     "Regular sports matter as much as lectures. Physical activity improves not only fitness but also concentration and mood, both directly supporting academic performance. Joining a basketball team or running club expands one's social circle. The simplest entry is the lowest barrier: a thirty-minute jog three times a week, a campus yoga class, or weekend hiking. Sports are not a distraction from study but an investment.",
     "investment that pays off。"),
    ("Write an essay (120-180 words) on \"Why Lifelong Learning Matters More Than Ever\".",
     "The skills that earn a comfortable salary today may be obsolete in a decade. Automation and shifting job markets mean a diploma is no longer a lifetime ticket. Lifelong learning has moved from a nice-to-have to an essential survival skill. Free online courses make expert content accessible at almost no cost. Setting aside five hours a week for deliberate study keeps one relevant, curious, and confident over decades of change.",
     "obsolete / survival skill。"),
    ("Write an essay (120-180 words) on \"The Pros and Cons of Online Education\".",
     "Online education democratizes access: a student in a small town can attend lectures from a top professor halfway around the world. Flexibility lets learners study at their own pace. However, online learning has limits. Without classroom structure, many students struggle with self-discipline. Spontaneous discussions and the social side of campus life are difficult to replicate on a screen. The best approach is hybrid - combining online flexibility with some in-person interaction.",
     "Pros/cons 折中。"),
    ("Write an essay (120-180 words) on \"Travel and Personal Growth\".",
     "Travel does more than fill a photo album. Stepping outside one's daily routine forces a person to navigate new languages, foods, and customs. A first solo trip sharpens decision-making: one must read maps, manage money, and recover from inevitable mistakes alone. Even short trips broaden perspective. After eating with a local family abroad, one may question what 'ordinary food' means. Travel is not escape from real life but training for it.",
     "成长意义。"),
    ("Write an essay (120-180 words) on \"The Importance of Mental Health Awareness on Campus\".",
     "Behind busy schedules, mental health problems are quietly common among students. Pressure from grades, employment, and social comparison can accumulate into anxiety long before anyone notices. Universities have a clear responsibility: visible counseling services, peer-support groups, and stress workshops should be routine, not crisis-only. Students themselves can build small habits - adequate sleep, exercise, honest conversations - that prevent problems from growing. Asking for help is a sign of strength.",
     "心理健康。"),
    ("Write an essay (120-180 words) on \"The Choice Between Big Cities and Smaller Cities\".",
     "For young graduates the choice between a megacity and a smaller city is defining. Big cities offer rich opportunities and the energy of fast-paced life but bring brutal housing costs. Smaller cities offer affordable living, family ties, and slower pace. The right answer depends on personal priorities. A cutting-edge career may demand a top-tier city; family time and lower stress may flourish in a second-tier city where a comfortable home is within reach.",
     "选择类。"),
    ("Write an essay (120-180 words) on \"How to Develop Critical Thinking Skills\".",
     "The ability to evaluate what one reads has become more valuable than the ability to memorize it. Critical thinking is not a natural talent but a habit grown through deliberate practice. First, question sources: who wrote this, what evidence is offered. Second, consider opposing viewpoints honestly. Third, be willing to change one's own mind when better evidence appears. Without these habits even the most educated person becomes vulnerable to clever propaganda.",
     "step 1/2/3 结构。"),
]

# === 7 套试卷分配 (扩展自原 5 套) ===
PAPERS = [
    ("paper-2024-03", "2024 年 3 月延期场 · 试卷一",   [0,1],     0, [0,1], [0,1]),
    ("paper-2024-06", "2024 年 6 月 · 试卷二",         [2,3],     1, [2,3], [2,3]),
    ("paper-2024-12", "2024 年 12 月 · 试卷三",        [4,5,6],   2, [4,5], [4,5]),
    ("paper-2025-06", "2025 年 6 月 · 试卷四",         [7,8],     3, [6,7], [6,7]),
    ("paper-2025-12", "2025 年 12 月 · 试卷五",        [9,10],    4, [8,9], [8,9]),
    ("paper-2026-06", "2026 年 6 月 · 试卷六",         [11,0],    5, [0,2], [10,11]),
    ("paper-2026-12", "2026 年 12 月预测 · 试卷七",    [1,2,3],   6, [1,3], [0,4]),
]


def render_listen(idx_in_paper, item, qid):
    opts_html = ' '.join([f'<label><input type="radio" name="{qid}" value="{v}"> {v}. {t}</label>' for v,t in item['opts']])
    return f"""
<div class="q" data-qid="{qid}">
<span class="qnum">听力 题 {idx_in_paper}</span>
<div class="script">
<div class="script-text">{item['script']}</div>
<button class="play-btn" onclick="play(this)">🔊 播放朗读</button>
</div>
<p><strong>Q:</strong> {item['q']}</p>
<div class="opts">{opts_html}</div>
<div class="feedback" style="display:none;"></div>
<div class="answer-block" style="display:none;">
<p><strong>正确答案: {item['ans']}</strong></p>
<p><strong>解析:</strong> {item['exp']}</p>
</div>
</div>
"""


def render_reading_passage(rp, qid_prefix):
    out = [f'<h3>Passage: {rp["title"]}</h3>\n<div class="script"><div class="script-text">{rp["passage"]}</div></div>\n']
    for i, (qid_suffix, q, opts, ans, exp) in enumerate(rp['qs'], 1):
        full_qid = f"{qid_prefix}_{qid_suffix}"
        opts_html = ' '.join([f'<label><input type="radio" name="{full_qid}" value="{v}"> {v}. {t}</label>' for v,t in opts])
        out.append(f"""
<div class="q" data-qid="{full_qid}">
<span class="qnum">阅读 题 {i}</span>
<p><strong>{q}</strong></p>
<div class="opts">{opts_html}</div>
<div class="feedback" style="display:none;"></div>
<div class="answer-block" style="display:none;">
<p><strong>正确答案: {ans}</strong></p>
<p><strong>解析:</strong> {exp}</p>
</div>
</div>
""")
    return ''.join(out)


def render_trans(idx_in_paper, item, qid):
    cn, en, tip = item
    return f"""
<div class="q subjective" data-qid="{qid}">
<span class="qnum">翻译 题 {idx_in_paper}</span>
<p><strong>请将下列中文译成英文:</strong></p>
<p>{cn}</p>
<textarea rows="5" placeholder="请在此输入你的英文翻译..."></textarea>
<div class="answer-block" style="display:none;">
<p><strong>参考译文:</strong> <em>{en}</em></p>
<p><strong>解析:</strong> {tip}</p>
</div>
</div>
"""


def render_write(idx_in_paper, item, qid):
    topic, model, tip = item
    return f"""
<div class="q subjective" data-qid="{qid}">
<span class="qnum">写作 题 {idx_in_paper}</span>
<p><strong>{topic}</strong></p>
<textarea rows="8" placeholder="请在此输入你的作文 (120-180 词)..."></textarea>
<div class="answer-block" style="display:none;">
<p><strong>参考范文:</strong> <em>{model}</em></p>
<p><strong>解析:</strong> {tip}</p>
</div>
</div>
"""


def main():
    OUT = 'D:/github/cet4-archive'
    for slug, title, lstn_idx, read_idx, trans_idx, write_idx in PAPERS:
        # 收集客观题正确答案 → window.ANSWERS
        answers = {}
        body_parts = []
        body_parts.append('<h2>Section A · Listening</h2>')
        for i, li in enumerate(lstn_idx, 1):
            qid = f"L_{li}"
            answers[qid] = LISTEN[li]['ans']
            body_parts.append(render_listen(i, LISTEN[li], qid))
        body_parts.append('\n<h2>Section B · Reading</h2>')
        qid_prefix = f"R_{read_idx}"
        for qid_suffix, _, _, ans, _ in READING[read_idx]['qs']:
            answers[f"{qid_prefix}_{qid_suffix}"] = ans
        body_parts.append(render_reading_passage(READING[read_idx], qid_prefix))
        body_parts.append('\n<h2>Section C · Translation</h2>')
        for i, ti in enumerate(trans_idx, 1):
            body_parts.append(render_trans(i, TRANS[ti], f"T_{ti}"))
        body_parts.append('\n<h2>Section D · Writing</h2>')
        for i, wi in enumerate(write_idx, 1):
            body_parts.append(render_write(i, WRITE[wi], f"W_{wi}"))
        full = HEAD.format(title=title, answers_json=json.dumps(answers))
        full += '\n'.join(body_parts)
        full += FOOTER_BTNS.format(title=title)
        path = os.path.join(OUT, f'{slug}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(full)
        print(f'built {slug}.html ({len(answers)} 客观题, {len(trans_idx)+len(write_idx)} 主观题)')


if __name__ == '__main__':
    main()
