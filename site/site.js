'use strict';
let locale = 'zh-CN';
try { locale = localStorage.getItem('ai4boji.site.locale') || locale; } catch (_) {}
const texts = [...document.querySelectorAll('[data-en]')].map(el => ({el, zh:el.innerHTML, en:el.dataset.en}));
let previewView = 'today';
function updatePreview() {
  const frame = document.querySelector('#live-preview');
  frame.src = './demo/?embed=1&lang=' + (locale === 'en' ? 'en' : 'zh-CN') + '&view=' + previewView;
  frame.title = locale === 'en' ? 'AI4薄肌 — scrollable live preview' : 'AI4薄肌 — 可滚动的实时演示界面';
  document.querySelector('.preview-tabs').setAttribute('aria-label', locale === 'en' ? 'Choose preview page' : '选择演示页面');
  document.querySelectorAll('[data-preview]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.preview === previewView)));
}
document.querySelectorAll('[data-preview]').forEach(button => button.onclick = () => {previewView = button.dataset.preview; updatePreview();});
function translate() {
  const en = locale === 'en';
  document.documentElement.lang = en ? 'en' : 'zh-CN';
  texts.forEach(({el,zh,en:english}) => { el.innerHTML = en ? english : zh; });
  document.querySelector('#language').textContent = en ? '中文 / EN' : 'EN / 中文';
  document.querySelector('.art-center strong').textContent = en ? 'Every day' : '每一天';
  const motion = document.querySelector('#motion');
  motion.textContent = document.documentElement.classList.contains('motion-paused') ? (en ? 'Resume motion' : '开启动效') : (en ? 'Pause motion' : '暂停动效');
  document.querySelectorAll('.step').forEach((el,i) => { el.textContent = en ? ['01 / UNDERSTAND','02 / PLAN','03 / ACT'][i] : ['01 / 理解','02 / 生成','03 / 行动'][i]; });
  updatePreview();
}
document.querySelector('#language').onclick=()=>{locale=locale==='en'?'zh-CN':'en';try{localStorage.setItem('ai4boji.site.locale',locale);}catch(_){}translate();};
translate();
// Explicitly silent QA mode; the delivered film retains its soundtrack.
if (new URLSearchParams(location.search).get('quiet') === '1') document.querySelector('video').muted = true;

const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
function setPaused(paused) {
  document.documentElement.classList.toggle('motion-paused', paused);
  document.querySelector('#motion').setAttribute('aria-pressed', String(paused));
  document.querySelector('#motion').textContent = locale === 'en' ? (paused ? 'Resume motion' : 'Pause motion') : (paused ? '开启动效' : '暂停动效');
}
setPaused(reducedMotion.matches);
reducedMotion.addEventListener('change', event => setPaused(event.matches));
document.querySelector('#motion').onclick = () => setPaused(!document.documentElement.classList.contains('motion-paused'));
const reveals = document.querySelectorAll('.preview,.story h2,.steps article,.film .wrap,.start>div,.scope');
if ('IntersectionObserver' in window && !reducedMotion.matches) {
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) { entry.target.classList.add('revealed'); observer.unobserve(entry.target); }
  }), {threshold:.08});
  reveals.forEach(element => {element.classList.add('reveal');observer.observe(element);});
}
let scrollPending = false;
function updateScroll() {
  const total = document.documentElement.scrollHeight - innerHeight;
  document.querySelector('.reading-progress').style.transform = 'scaleX(' + (total > 0 ? scrollY / total : 0) + ')';
  scrollPending = false;
}
addEventListener('scroll', () => {if (!scrollPending) {scrollPending = true;requestAnimationFrame(updateScroll);}}, {passive:true});
updateScroll();
