// 极简 DOM stub，用于验证脚本运行时无异常
const store = {};
function mkEl(id){
  return {
    id, innerHTML:'', textContent:'', disabled:false, style:{},
    classList:{_s:new Set(), add(x){this._s.add(x)}, remove(x){this._s.delete(x)},
      toggle(x,f){ f?this._s.add(x):this._s.delete(x); }, contains(x){return this._s.has(x)}},
    addEventListener(){}, scrollIntoView(){}, querySelectorAll(){return []}, querySelector(){return mkEl('x')},
    dataset:{}, closest(){return null}, focus(){}
  };
}
const els = {};
global.document = {
  getElementById(id){ return els[id] || (els[id]=mkEl(id)); },
  querySelectorAll(sel){ return []; },
  querySelector(sel){ return mkEl('q'); },
  addEventListener(){},
  body:{ classList:{ add(){}, remove(){}, toggle(){} } }
};
global.window = { scrollTo(){}, print(){} };
global.localStorage = { getItem:k=>store[k]||null, setItem:(k,v)=>store[k]=v, removeItem:k=>{delete store[k]} };
global.IntersectionObserver = class { constructor(){} observe(){} };
global.confirm = ()=>true;
global.setInterval = ()=>0;
global.clearInterval = ()=>{};
global.alert = ()=>{};

const target = process.argv[2] || 'exams/模考卷/金融专业真题模考卷（第一套）.html';
const html = require('fs').readFileSync(target,'utf8');
const src = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const ctx = src + `
;global.__T={DATA,ans,submit,scoreOf,fullOf,els:null};`;
eval(ctx);
const T=global.__T;

const body = els['body'].innerHTML;
const nq = (body.match(/<article class="q"/g)||[]).length;
const nexp = (body.match(/class="exp"/g)||[]).length;
const nopt = (body.match(/class="opt"/g)||[]).length;
console.log('渲染题目数:', nq, '| 解析块:', nexp, '| 选项按钮:', nopt);
console.log('答题卡格子:', (els['cardGrid'].innerHTML.match(/class="cell"/g)||[]).length);

// 模拟：全部按标准答案作答后交卷
T.DATA.qs.forEach(q=>{ T.ans[q.no] = q.ans; });
T.submit(true);
const res = els['result'].innerHTML;
const mm = res.match(/<div class="res-main">([\d.]+)<span>/);
console.log('全对总分:', mm && mm[1], '| 合格判定:', /合格</.test(res.replace(/未合格/,'')) ? '合格' : '?');
console.log('结果面板含"最需回炉":', res.indexOf('最需回炉')>0);
console.log('✅ 运行时无异常');
