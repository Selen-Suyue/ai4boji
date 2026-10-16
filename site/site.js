'use strict';
let locale = 'zh-CN';
try { locale = localStorage.getItem('ai4boji.site.locale') || locale; } catch (_) {}
const texts = [...document.querySelectorAll('[data-en]')].map(el => ({el, zh:el.innerHTML, en:el.dataset.en}));
function translate() {
  const en = locale === 'en';
  document.documentElement.lang = en ? 'en' : 'zh-CN';
  texts.forEach(({el,zh,en:english}) => { el.innerHTML = en ? english : zh; });
  document.querySelector('#language').textContent = en ? '中文 / EN' : 'EN / 中文';
  document.querySelector('.art-center strong').textContent = en ? 'Every day' : '每一天';
  document.querySelectorAll('.step').forEach((el,i) => { el.textContent = en ? ['01 / UNDERSTAND','02 / PLAN','03 / ACT'][i] : ['01 / 理解','02 / 生成','03 / 行动'][i]; });
}
document.querySelector('#language').onclick=()=>{locale=locale==='en'?'zh-CN':'en';try{localStorage.setItem('ai4boji.site.locale',locale);}catch(_){}translate();};
translate();
