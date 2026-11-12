// 极简 DOM stub：验证 render/judge/submit 不抛运行时错误
function El(tag){
  return {
    tagName: tag||'div', innerHTML:'', _text:'', dataset:{}, style:{}, children:[],
    classList:{ _s:new Set(),
      add(...c){c.forEach(x=>this._s.add(x))}, remove(...c){c.forEach(x=>this._s.delete(x))},
      toggle(c,f){ f?this._s.add(c):this._s.delete(c) }, contains(c){return this._s.has(c)} },
    set textContent(v){ this._text = String(v) }, get textContent(){ return this._text },
    set className(v){ this._cn = v }, get className(){ return this._cn||'' },
    addEventListener(){}, removeEventListener(){}, click(){},
    appendChild(c){this.children.push(c)}, getBoundingClientRect(){return {top:0,bottom:100,left:0,right:0}},
    remove(){}, querySelector(){ return El() },
  };
}
const CACHE = {};
global.document = {
  getElementById(id){ return CACHE[id] || (CACHE[id] = El()); },
  querySelector(){ return El(); },
  querySelectorAll(){ return []; },
  createElement(t){ return El(t); },
  addEventListener(){},
};
global.window = { scrollTo(){}, print(){}, addEventListener(){} };
global.localStorage = { _d:{}, getItem(k){return this._d[k]||null}, setItem(k,v){this._d[k]=v}, removeItem(k){delete this._d[k]} };
global.setTimeout = (f,t)=>0; global.clearTimeout=()=>{}; global.setInterval=()=>0; global.clearInterval=()=>{};
global.alert = ()=>{}; global.confirm = ()=>true;
global.URL = { createObjectURL:()=>'blob:x' };
global.Blob = function(){};
