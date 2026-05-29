// progress.js - paper 答题进度 + 错题本 localStorage 自动持久化
// (2026-05-29 v8: 优化第二轮 - 老大要的"答题进度+错题本自动存")
(function(){
  if(typeof window==='undefined')return;
  var KEY_PROGRESS='cet4_paper_progress';
  var KEY_WRONG='cet4_wrong_book';

  function paperId(){
    var m=location.pathname.match(/paper-([0-9]{4}-[0-9]{2}(?:-[0-9]+|-combined)?)\.html/);
    return m?m[1]:location.pathname.split('/').pop().replace('.html','');
  }
  function loadAll(k){try{return JSON.parse(localStorage.getItem(k)||'{}');}catch(e){return{};}}
  function saveAll(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}

  function saveCurrent(){
    var pid=paperId();
    var ans={};
    document.querySelectorAll('.q[data-qid] input[type="radio"]:checked').forEach(function(r){
      var qid=r.closest('.q').getAttribute('data-qid');
      ans[qid]=r.value;
    });
    var all=loadAll(KEY_PROGRESS);
    all[pid]={answers:ans,ts:Date.now(),submitted:!!document.querySelector('.q.correct,.q.wrong')};
    saveAll(KEY_PROGRESS,all);
  }
  function restoreCurrent(){
    var pid=paperId();
    var all=loadAll(KEY_PROGRESS);
    var rec=all[pid];
    if(!rec||!rec.answers)return;
    Object.keys(rec.answers).forEach(function(qid){
      var ipt=document.querySelector('.q[data-qid="'+qid+'"] input[type="radio"][value="'+rec.answers[qid]+'"]');
      if(ipt)ipt.checked=true;
    });
    if(rec.submitted&&typeof submitPaper==='function')submitPaper();
    var hint=document.createElement('div');
    hint.style.cssText='margin:10px 0;padding:8px 12px;background:#fef3c7;border-left:3px solid #f59e0b;border-radius:6px;font-size:0.88rem;color:#92400e;';
    var d=new Date(rec.ts);
    hint.innerHTML='⏰ 上次作答已恢复 ('+d.toLocaleString('zh-CN',{hour12:false})+') · <button onclick="window.cet4ClearPaper()" style="margin-left:8px;padding:2px 10px;background:#dc2626;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;">清空重做</button>';
    var first=document.querySelector('main')||document.body;
    first.insertBefore(hint,first.firstChild);
  }
  window.cet4ClearPaper=function(){
    var pid=paperId();
    var all=loadAll(KEY_PROGRESS);
    delete all[pid];
    saveAll(KEY_PROGRESS,all);
    location.reload();
  };

  function recordWrong(){
    var pid=paperId();
    var wrong=loadAll(KEY_WRONG);
    if(!wrong[pid])wrong[pid]={items:[],ts:0};
    var items=[];
    document.querySelectorAll('.q.wrong[data-qid]').forEach(function(qEl){
      var qid=qEl.getAttribute('data-qid');
      var ca=(window.ANSWERS||{})[qid];
      var sel=qEl.querySelector('input[type="radio"]:checked');
      var ua=sel?sel.value:'(未答)';
      var stem=(qEl.querySelector('.qnum')?qEl.querySelector('.qnum').textContent:qid).trim();
      items.push({qid:qid,stem:stem,ua:ua,ca:ca});
    });
    wrong[pid]={items:items,ts:Date.now()};
    saveAll(KEY_WRONG,wrong);
  }

  // hook 提交/重置/选择 → 自动存
  var origSubmit=window.submitPaper;
  if(typeof origSubmit==='function'){
    window.submitPaper=function(){origSubmit.apply(this,arguments);saveCurrent();recordWrong();};
  }
  var origReset=window.resetPaper;
  if(typeof origReset==='function'){
    window.resetPaper=function(){origReset.apply(this,arguments);window.cet4ClearPaper();};
  }
  document.addEventListener('change',function(e){
    if(e.target&&e.target.type==='radio'&&e.target.closest('.q[data-qid]'))saveCurrent();
  });
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',restoreCurrent);
  } else {
    restoreCurrent();
  }
})();
