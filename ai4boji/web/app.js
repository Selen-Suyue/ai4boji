/* AI4薄肌 — buildless UI; every write uses the same validated core as Codex. */
'use strict';
const $ = (selector) => document.querySelector(selector);
const E = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let lang = 'zh-CN';
try { lang = localStorage.getItem('ai4boji.locale') || lang; } catch (_) { /* Storage can be disabled. */ }
if (!['zh-CN', 'en'].includes(lang)) lang = 'zh-CN';
let S, view = 'today', chosenDate = '', editingLog = null, editingMemory = null, toastTimer;
let chartSpecs = [], chartObservers = [];
const t = (zh, en) => lang === 'zh-CN' ? zh : en;
const L = (value) => value && typeof value === 'object' && 'zh-CN' in value ? value[lang] : (value ?? '');
const weekdays = () => t(['一','二','三','四','五','六','日'], ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']);
const statusName = (status) => ({completed:t('完成','Completed'),partial:t('部分完成','Partial'),rest:t('休息','Rest'),skipped:t('跳过','Skipped'),unknown:t('未记录','Unrecorded')})[status] || status;
function toast(message, error = false) {
  clearTimeout(toastTimer); const el = $('#toast'); el.textContent = message;
  el.className = error ? 'error' : ''; el.hidden = false;
  toastTimer = setTimeout(() => { el.hidden = true; }, error ? 10000 : 4500);
}
async function api(path, data) {
  if (window.AI4BOJI_PREVIEW) return window.AI4BOJI_PREVIEW(path, data);
  const options = data === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':$('meta[name="csrf-token"]').content},body:JSON.stringify(data)};
  const response = await fetch('/api/' + path, options);
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || t('操作失败','Request failed'));
  return result;
}
async function refresh() {
  S = await api('state' + (chosenDate ? '?date=' + encodeURIComponent(chosenDate) : ''));
  if (!S.profile) view = 'profile';
  render();
}
async function action(work, button) {
  if (button) button.disabled = true;
  try { await work(); } catch(error) { toast(error.message, true); }
  finally { if (button?.isConnected) button.disabled = false; }
}
function field(label, name, value='', type='text', extra='', full=false) {
  return `<label class="field ${full?'full':''}">${E(label)}<input name="${name}" type="${type}" value="${E(value)}" ${extra}></label>`;
}
function select(label, name, value, options, full=false) {
  return `<label class="field ${full?'full':''}">${E(label)}<select name="${name}">${options.map(([v,label])=>`<option value="${E(v)}" ${v===value?'selected':''}>${E(label)}</option>`).join('')}</select></label>`;
}
function intro(kicker,title,description,extra='') {
  return `<header class="page-intro"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p>${description}</p></div>${extra}</header>`;
}
function metrics() {
  const r=S.report;
  return `<div class="metrics"><div class="metric"><div class="label">${t('近 14 天 · 训练','TRAINING · LAST 14 DAYS')}</div><div class="value">${r.training_days}<span class="unit">${t('天','days')}</span></div><div class="small muted">${t('按实际记录统计','From your recorded activity')}</div></div><div class="metric"><div class="label">${t('已记录训练时间','RECORDED TRAINING TIME')}</div><div class="value">${r.total_minutes}<span class="unit">${t('分钟','min')}</span></div><div class="small muted">${r.unknown_duration_sessions ? r.unknown_duration_sessions+' '+t('次时长未知','sessions with unknown duration') : t('每一点投入都有意义','Small efforts add up')}</div></div><div class="metric"><div class="label">${t('有记录的日子','DAYS WITH RECORDS')}</div><div class="value">${r.recorded_days}<span class="unit">/ 14</span></div><div class="small muted">${r.unknown_days} ${t('天尚未记录','days remain unrecorded')}</div></div></div>`;
}
function calendar() {
  return `<div class="mini-calendar">${S.report.calendar.map(d=>`<button class="calendar-day ${d.status} ${d.date===S.date?'selected':''}" data-date="${d.date}" title="${d.date} · ${statusName(d.status)}" aria-label="${d.date} ${statusName(d.status)}">${Number(d.date.slice(-2))}</button>`).join('')}</div><div class="calendar-legend">${['completed','partial','rest','unknown'].map(s=>`<span><i class="swatch ${s}"></i>${statusName(s)}</span>`).join('')}</div>`;
}
function chart(points, unit, label) {
  if (!points.length) return `<div class="empty">${t('有记录后，变化会在这里慢慢显现。','Your progress will appear here as you add records.')}</div>`;
  const id=chartSpecs.length; chartSpecs.push({points,unit,label});
  return `<div class="chart-host" data-chart="${id}"></div>`;
}
function drawChart(points, unit, label, width) {
  const height=230,left=48,right=20,top=22,bottom=36;
  const values=points.map(p=>p.value), min=Math.min(...values), max=Math.max(...values), pad=Math.max((max-min)*.25, unit==='kg'?.3:1);
  const lo=min-pad,hi=max+pad;
  const times=points.map(p=>Date.parse(p.date+'T12:00:00Z')),a=Math.min(...times),b=Math.max(...times);
  const x=i=>a===b?width/2:left+(times[i]-a)/(b-a)*(width-left-right);
  const y=v=>top+(hi-v)/(hi-lo)*(height-top-bottom);
  const axes=[0,.5,1].map(f=>{const v=lo+(hi-lo)*f;return `<line class="grid-line" x1="${left}" x2="${width-right}" y1="${y(v)}" y2="${y(v)}"/><text x="${left-10}" y="${y(v)+4}" text-anchor="end">${v.toFixed(1)}</text>`;}).join('');
  const tickIndices=[...new Map([0,Math.floor((points.length-1)/2),points.length-1].map(i=>[times[i],i])).values()];
  return `<svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="${E(label)}"><title>${E(label)}</title><text x="${left}" y="12">${E(unit)}</text>${axes}<polyline class="plot-line" points="${points.map((p,i)=>`${x(i)},${y(p.value)}`).join(' ')}"/>${points.map((p,i)=>`<circle class="point" cx="${x(i)}" cy="${y(p.value)}" r="4"><title>${p.date}: ${p.value} ${E(unit)}</title></circle>`).join('')}${tickIndices.map(i=>`<text x="${x(i)}" y="${height-12}" text-anchor="${i===0?'start':i===points.length-1?'end':'middle'}">${points[i].date.slice(5).replace('-','/')}</text>`).join('')}</svg>`;
}
function planCard() {
  const row=S.plan, p=row?.payload;
  if (!p) return `<article class="card"><div class="empty"><div class="eyebrow">${t('从今天开始','START TODAY')}</div><h2>${t('为今天留一点运动时间','Make a little time for movement')}</h2><p>${t('先填写今日状态，再生成适合今天的安排。','Check in, then create a plan that fits your day.')}</p><div class="form-actions"><button class="button" data-generate>${t('生成今日计划','Create today’s plan')} ↗</button></div></div></article>`;
  return `<article class="card plan-card"><div class="plan-hero"><div class="orb" aria-hidden="true"></div><div class="eyebrow">${t('你的专属安排','YOUR DAILY PLAN')} · ${E(p.date)}</div><h2>${E(L(p.title))}</h2><p>${t('从适合你的起点，稳稳向前。','A steady step from where you are today.')}</p></div><div class="plan-content">${row.stale?`<div class="callout warning">${t('档案或记录已有更新。开始前请重新生成，查看最新安排。','Your profile or records changed. Refresh the plan before starting.')}</div>`:''}<div class="plan-meta"><span>${p.minutes} ${t('分钟以内','min or less')}</span><span>${p.exercises.length} ${t('个动作','exercises')}</span><span>${t('版本','Version')} ${row.revision}</span></div>${p.mode==='training'?`<p class="guidance">${E(L(p.warmup))}</p>${p.exercises.map((ex,i)=>`<div class="exercise"><span class="exercise-number">${String(i+1).padStart(2,'0')}</span><div><h3>${E(L(ex.name))}</h3><details><summary>${t('动作要点与替代','Form & alternative')}</summary><p>${E(L(ex.cue))}</p><p>${E(L(ex.alternative))}</p><p>${t('组间休息','Rest between sets')}: ${ex.rest_seconds} ${t('秒','sec')}</p></details></div><span class="sets">${ex.sets} × ${ex.reps}</span></div>`).join('')}<p class="guidance">${E(L(p.effort))}</p><p class="guidance">${E(L(p.cooldown))}</p>`:`<p class="guidance">${E(L(p.mode==='hold'?TEXT_HOLD():p.recovery))}</p>`}<div class="reason"><b>${t('为什么这样安排','Why this plan')}</b>${p.reasons.map(r=>E(L(r))).join('<br>')}</div></div><div class="plan-actions"><button class="button secondary small-button" data-generate>${t('更新安排','Refresh plan')} ↻</button><button class="button" data-view="records">${t('记录实际完成','Log what you did')} ↗</button></div></article>`;
}
function TEXT_HOLD(){return {'zh-CN':'今天暂不自动安排力量训练。先确认疼痛或限制，再讨论适合你的活动。','en':'Automatic strength planning is paused. Clarify pain or restrictions before choosing suitable activity.'};}
function checkinCard() {
  const p=S.checkin?.payload||{};
  return `<article class="card"><div class="card-header"><h2>${t('今天感觉怎么样？','How are you today?')}</h2><span class="sub">${t('约 30 秒','ABOUT 30 SEC')}</span></div><form id="checkin-form"><div class="form-grid">${field(t('睡眠 / 小时','Sleep / hours'),'sleep_hours',p.sleep_hours??'','number','min="0" max="24" step="0.5"')}${field(t('可用时间 / 分钟','Time / minutes'),'minutes',p.minutes??S.profile?.payload.minutes??30,'number','min="5" max="90" required')}${select(t('精力','Energy'),'energy',String(p.energy??''),[['',t('尚未填写','Not reported')],...Array.from({length:5},(_,i)=>[String(i+1),`${i+1} · ${[t('很低','Very low'),t('偏低','Low'),t('一般','Okay'),t('不错','Good'),t('充沛','High')][i]}`])])}${select(t('酸痛程度','Soreness'),'soreness',String(p.soreness??''),[['',t('尚未填写','Not reported')],...Array.from({length:6},(_,i)=>[String(i),i===0?t('0 · 没有','0 · None'):i===5?t('5 · 明显','5 · High'):String(i)])])}${select(t('是否有疼痛或不适？','Any pain or discomfort?'),'pain',p.pain===undefined?'':String(p.pain),[['',t('尚未确认','Not confirmed')],['false',t('没有','No')],['true',t('有，先暂停训练','Yes, pause training')]],true)}</div><div class="form-actions"><button class="button" type="submit">${t('保存状态并更新计划','Save & update plan')}</button></div><p class="mini-note">${t('没填写的信息会保持未知，不会自动假设你状态良好。','Unreported details stay unknown; we won’t assume you feel well.')}</p></form></article>`;
}
function todayView() {
  const name=S.profile?.payload.name||'';
  return `${intro(t('一点一滴，积累改变','SMALL STEPS. LASTING CHANGE.'),t(`${E(name)}，今天也向前一点。`,`A little stronger today, ${E(name)}.`),t('把目标放在心里，把今天过得具体。你的安排会跟着真实状态一起调整。','Keep the goal in mind and make today concrete. Your plan adapts to the state you report.'),`<div class="intro-art"><span>↗</span>${t('按自己的节奏生长','GROW AT YOUR OWN PACE')}</div>`)}${metrics()}<div class="grid"><div class="stack-main">${planCard()}</div><div class="stack">${checkinCard()}<article class="card"><div class="card-header"><h2>${t('你的训练足迹','Your rhythm')}</h2><span class="sub">${t('近 14 天','LAST 14 DAYS')}</span></div>${calendar()}<p class="mini-note">${t('休息也是计划的一部分。未记录的日子，留给你补充。','Rest is part of the plan. Unrecorded days are yours to fill in.')}</p></article></div></div><article class="card nutrition-card"><div class="card-header"><h2>${t('今天，也好好吃饭','Make room for a good meal')}</h2><span class="sub">${t('饮食与恢复','FOOD & RECOVERY')}</span></div><p class="small muted">${E(L(S.plan?.payload.nutrition||{'zh-CN':'规律吃饭，关注能够坚持的习惯。','en':'Eat regularly and focus on habits you can sustain.'}))}</p>${S.profile?.payload.diet?`<p class="mini-note">${t('你的饮食习惯','Your food context')} · ${E(S.profile.payload.diet)}</p>`:''}</article>`;
}
function exerciseInput(item={}) {
  return `<div class="exercise-input"> <select class="ex-id" aria-label="${t('动作','Exercise')}">${Object.entries(S.catalog).map(([id,ex])=>`<option value="${id}" ${id===(item.exercise_id||'chair-squat')?'selected':''}>${E(L(ex.name))}</option>`).join('')}</select><input class="ex-sets" type="number" aria-label="${t('组数','Sets')}" min="1" max="20" value="${E(item.sets??'')}" required><input class="ex-reps" type="number" aria-label="${t('每组次数','Reps per set')}" min="1" max="100" value="${E(item.reps??'')}" required><input class="ex-load" type="number" aria-label="${t('每只哑铃重量 kg','Load per dumbbell kg')}" min="0" max="300" step="0.5" value="${E(item.load_kg??0)}" required><button type="button" class="remove-ex" aria-label="${t('移除此动作','Remove exercise')}">×</button></div>`;
}
function recordsView() {
  const p=editingLog?.payload||{};
  return `${intro(t('把真实发生的，留下来','MAKE YOUR EXPERIENCE COUNT'),t('记录每一次小小的坚持。','Make every small effort count.'),t('完成多少就记录多少。你也可以把自然语言反馈告诉 Codex，由它整理成记录。','Record what actually happened. You can also tell Codex in your own words and let it structure the record.'))}<div class="grid"><article class="card record-form"><div class="card-header"><h2>${editingLog?t('修改记录','Edit record'):t('添加记录','Add a record')}</h2><span class="sub">${t('实际完成','ACTUAL ACTIVITY')}</span></div><form id="log-form"><div class="form-grid">${field(t('日期','Date'),'date',p.date||S.date,'date','required')}${select(t('完成情况','Outcome'),'status',p.status||'completed',['completed','partial','rest','skipped'].map(v=>[v,statusName(v)]))}${field(t('实际训练 / 分钟，可留空','Training / minutes, optional'),'duration_min',p.duration_min??'','number','min="0" max="300"')}${field(t('主观难度 / 1–10，可留空','Effort / 1–10, optional'),'effort',p.effort??'','number','min="1" max="10"')}${field(t('体重 / kg，可留空','Weight / kg, optional'),'weight_kg',p.weight_kg??'','number','min="20" max="400" step="0.1"')}${field(t('腰围 / cm，可留空','Waist / cm, optional'),'waist_cm',p.waist_cm??'','number','min="30" max="300" step="0.1"')}${select(t('运动时是否疼痛？','Pain during activity?'),'pain',p.pain===undefined?'':String(p.pain),[['',t('未记录','Not reported')],['false',t('没有','No')],['true',t('有','Yes')]],true)}<label class="field full">${t('感受与备注','How it felt / notes')}<textarea name="note" maxlength="4000" placeholder="${t('例如：最后一组有点吃力，下次想早点开始。','For example: the last set felt hard; next time I want to start earlier.')}" >${E(p.note||'')}</textarea></label></div><div class="exercise-input exercise-head"><span>${t('动作（可选）','Exercise (optional)')}</span><span>${t('组','Sets')}</span><span>${t('次/组','Reps/set')}</span><span>kg</span><span></span></div><div id="exercise-rows">${(p.exercises||[]).map(exerciseInput).join('')}</div><button class="button ghost" id="add-exercise" type="button">+ ${t('添加实际完成的动作','Add an exercise you performed')}</button><p class="small muted">${t('同一行表示各组使用相同次数与重量；不同组可分行记录。徒手重量填 0。','A row groups sets with the same reps and load; use separate rows for different sets. Enter 0 for bodyweight.')}</p><div class="form-actions"><button class="button" type="submit">${editingLog?t('保存修改','Save changes'):t('保存记录','Save record')} ↗</button>${editingLog?`<button class="button secondary" id="cancel-edit" type="button">${t('取消','Cancel')}</button>`:''}</div></form></article><div class="stack"><article class="card"><div class="card-header"><h2>${t('最近记录','Recent records')}</h2><span class="sub">${S.logs.length} ${t('条','TOTAL')}</span></div>${S.logs.length?`<div class="table-wrap"><table class="table"><thead><tr><th>${t('日期 / 状态','Date / outcome')}</th><th>${t('分钟','Min')}</th><th>${t('操作','Action')}</th></tr></thead><tbody>${[...S.logs].reverse().slice(0,20).map(r=>`<tr><td>${r.date}<small>${statusName(r.payload.status)}</small></td><td>${r.payload.duration_min??'—'}</td><td><button class="text-button" data-edit-log="${E(r.id)}">${t('修改','Edit')}</button></td></tr>`).join('')}</tbody></table></div>`:`<div class="empty">${t('你的第一条记录会出现在这里。','Your first record will appear here.')}</div>`}<p class="mini-note">${t('修改会保留版本；重复提交同一条记录不会重复计数。','Edits retain previous versions. Resubmitting the same record won’t double-count it.')}</p></article></div></div>`;
}
function progressView() {
  const logs=S.logs.filter(r=>r.date>=S.report.start&&r.date<=S.date);
  const strength=logs.flatMap(r=>{const ex=r.payload.exercises.filter(e=>e.exercise_id==='chair-squat');return ex.length?[{date:r.date,value:ex.reduce((a,b)=>a+b.sets*b.reps,0)}]:[];});
  return `${intro(t('看见变化，也理解变化','SEE THE CHANGE. UNDERSTAND IT.'),t('进步，有自己的节奏。','Progress has its own rhythm.'),t('用真实记录观察长期变化。一次波动不定义你的努力。','Use real records to see change over time. One fluctuation doesn’t define your effort.'))}${metrics()}<div class="grid"><div class="stack-main"><article class="card"><div class="card-header"><h2>${t('体重记录','Weight records')}</h2><span class="sub">${t('原始测量 · kg','RAW MEASUREMENTS · kg')}</span></div>${chart(S.report.weights,'kg',t('体重随日期变化','Weight by date'))}<p class="chart-caption">${t('连线仅连接已记录的测量点，不填补缺失日期，也不预测未来。','Lines connect recorded measurements only. Missing dates are not filled and future values are not predicted.')}</p></article><article class="card"><div class="card-header"><h2>${t('坐椅深蹲 · 完成总次数','Chair squat · total repetitions')}</h2><span class="sub">${t('实际组数 × 次数','ACTUAL SETS × REPS')}</span></div>${chart(strength,t('次','reps'),t('坐椅深蹲实际总次数','Actual chair squat repetitions'))}<p class="chart-caption">${t('只比较同一动作的记录；更多次数并不总是意味着更合适。','Compare records of the same exercise; more repetitions are not always better.')}</p></article></div><div class="stack"><article class="card"><div class="card-header"><h2>${t('两周回顾','Two-week reflection')}</h2><span class="sub">${S.report.start.slice(5)} — ${S.report.end.slice(5)}</span></div>${calendar()}<p class="mini-note">${E(L(S.report.reflection))}</p><button class="button ghost" id="download-report">${t('下载回顾','Download reflection')} ↓</button></article><article class="card"><div class="card-header"><h2>${t('安排的来由','How your plans evolved')}</h2><span class="sub">${t('最近 5 次','LATEST 5')}</span></div><div class="timeline">${[...S.plans].filter(r=>r.date<=S.date).reverse().slice(0,5).map(r=>`<div class="timeline-item"><h3>${r.date} · ${E(L(r.payload.title))}</h3><p>${r.payload.reasons.map(v=>E(L(v))).join(' ')}</p><div class="small muted">${t('版本','Version')} ${r.revision} · ${r.payload.evidence_ids.length} ${t('条依据','source records')}</div></div>`).join('')||`<div class="empty">${t('生成计划后显示依据。','Create a plan to see its sources.')}</div>`}</div></article></div></div>`;
}
function profileView() {
  const p=S.profile?.payload||{}, m=editingMemory?.payload||{};
  const first=!S.profile;
  return `${intro(t('懂你，从真实的信息开始','PERSONAL GUIDANCE STARTS WITH YOU'),first?t('从认识你开始。','Let’s start with you.'):t('你的档案，始终由你掌握。','Your profile stays in your hands.'),first?t('几项基本信息，让第一份计划适合你的时间与条件。','A few details help the first plan fit your time and equipment.'):t('生活会变，档案也可以更新。明确的事实与 AI 推断分别保存。','Life changes; your profile can too. Reported facts and AI inferences are kept distinct.'))}<div class="${first?'onboarding':'grid'}"><article class="card"><div class="card-header"><h2>${t('个人档案','Your profile')}</h2><span class="sub">${t('本地保存','SAVED LOCALLY')}</span></div><form id="profile-form"><div class="form-grid">${field(t('称呼','Name'),'name',p.name||'','text','maxlength="80" required')}${field(t('年龄（18 岁及以上）','Age (18+)'),'age',p.age??'','number','min="18" max="100" required')}${field(t('你希望实现什么？','What would you like to achieve?'),'goal',p.goal||'','text','maxlength="500" required',true)}${field(t('单次可用时间 / 分钟','Time per session / min'),'minutes',p.minutes??30,'number','min="10" max="90" required')}${select(t('可用器械','Equipment'),'equipment',p.equipment||'bodyweight',[['bodyweight',t('徒手 + 稳固椅子','Bodyweight + stable chair')],['dumbbells',t('另有哑铃','Dumbbells available')]])}<div class="field full"><span>${t('每周训练日（选择 1–3 天）','Training weekdays (choose 1–3)')}</span><div class="weekdays">${weekdays().map((d,i)=>`<label class="weekday"><input type="checkbox" name="days" value="${i}" ${(p.days||[0,2,4]).includes(i)?'checked':''}>${d}</label>`).join('')}</div></div>${field(t('时区','Timezone'),'timezone',p.timezone||'Asia/Shanghai','text','required',true)}<label class="field full">${t('运动限制或需要注意的不适','Exercise restrictions or discomfort')}<textarea name="restrictions" maxlength="1000" placeholder="${t('如无已知限制，可留空。填写后会暂停自动力量安排。','Leave blank if none are known. Any restriction pauses automatic strength plans.')}">${E(p.restrictions||'')}</textarea></label><label class="field full">${t('饮食习惯与实际条件','Food habits and practical constraints')}<textarea name="diet" maxlength="1000" placeholder="${t('例如食堂、外卖、预算或饮食偏好','For example: cafeteria, takeout, budget or preferences')}">${E(p.diet||'')}</textarea></label></div><div class="form-actions"><button class="button" type="submit">${first?t('建立档案，开始今天','Create profile & start today'):t('保存档案','Save profile')} ↗</button></div><p class="profile-note">${t('首版提供成人新手的保守起步安排。未保存的信息不会被猜测；涉及疼痛和运动限制时，先确认合适的活动。','v0.1 provides conservative starter plans for adult beginners. Missing details are not guessed. Pain and restrictions require clarification before activity.')}</p></form></article>${first?'':`<div class="stack"><article class="card"><div class="card-header"><h2>${t('长期记忆','Long-term memory')}</h2><span class="sub">${S.memories.length} ${t('条','ITEMS')}</span></div>${S.memories.map(r=>`<div class="memory"><p>${E(r.payload.text)}</p><div class="memory-meta"><span>${E(({fact:t('事实','Fact'),preference:t('偏好','Preference'),inference:t('AI 推断','AI inference')})[r.payload.kind])} · ${r.payload.confirmed?t('用户已确认','User confirmed'):t('待确认','Unconfirmed')} · ${r.active?t('有效','Active'):t('已到期','Expired')}</span><div class="memory-actions"><button class="text-button" data-edit-memory="${E(r.id)}">${t('更正','Edit')}</button><button class="text-button danger" data-forget="${E(r.id)}">${t('删除','Delete')}</button></div></div></div>`).join('')||`<div class="empty">${t('记住那些对你重要的小细节。','Remember the little things that matter to you.')}</div>`}<p class="mini-note">${t('文字记忆供 Codex 理解与参考；本地自动计划读取上方档案与每日状态。删除会同时移除该记忆的历史版本。','Text memories inform Codex. Automatic local plans use structured profile and check-in fields. Deleting a memory also removes its revisions.')}</p><form id="memory-form"><div class="form-grid"><label class="field full">${editingMemory?t('更正记忆','Edit memory'):t('添加记忆','Add a memory')}<textarea name="text" maxlength="2000" required>${E(m.text||'')}</textarea></label>${select(t('类型','Type'),'kind',m.kind||'preference',[['preference',t('偏好','Preference')],['fact',t('事实','Fact')],['inference',t('AI 推断','AI inference')]])}${field(t('有效至（可留空）','Expires (optional)'),'expires',m.expires||'','date')}<label class="checkbox field full"><input name="confirmed" type="checkbox" ${m.confirmed?'checked':''}>${t('这是我确认的信息（AI 推断不可勾选）','I confirm this information (not for AI inferences)')}</label></div><div class="form-actions"><button class="button secondary" type="submit">${t('保存记忆','Save memory')}</button>${editingMemory?`<button class="button ghost" type="button" id="cancel-memory">${t('取消','Cancel')}</button>`:''}</div></form></article><article class="card"><h2>${t('数据属于你','Your data is yours')}</h2><p class="mini-note">${t('数据库在本机，无后台上传。交给 Codex 的内容会进入相应模型处理流程。','The database stays on this device, with no background uploads. Information shared with Codex enters its model-processing workflow.')}</p><button class="button ghost" id="export-data">${t('导出全部当前记录','Export all current records')} ↓</button></article></div>`}</div>`;
}
function render() {
  chartObservers.forEach(o=>o.disconnect());chartObservers=[];chartSpecs=[];
  document.documentElement.lang=lang;
  document.title='AI4薄肌';
  const views={today:todayView,records:recordsView,progress:progressView,profile:profileView};
  const nav=[['today',t('今日计划','Today')],['records',t('训练记录','Records')],['progress',t('进步趋势','Progress')],['profile',t('档案与记忆','Profile & memory')]];
  $('#app').innerHTML=`<div class="shell"><aside class="sidebar"><div class="brand"><span class="brandmark" aria-hidden="true">薄</span><div><strong>AI4薄肌</strong><small>${t('每天，靠近更好的自己','A LITTLE STRONGER, EVERY DAY')}</small></div></div><nav class="nav" aria-label="${t('主要导航','Main navigation')}">${nav.map(([id,label],i)=>`<button data-view="${id}" class="${view===id?'active':''}" ${view===id?'aria-current="page"':''} ${!S.profile&&id!=='profile'?'disabled':''}><span class="index">0${i+1}</span>${label}</button>`).join('')}</nav><div class="side-note"><div class="eyebrow">WITH CODEX</div><p>${t('“我今天只有 20 分钟。”<br>告诉 Codex，它会结合你的档案，安排下一步。','“I only have 20 minutes today.”<br>Tell Codex. It can use your saved profile to guide the next step.')}</p></div><div class="side-footer">v0.1.0 · ${t('本地优先 · 长期陪伴','Local first · Built for continuity')}</div></aside><main class="main"><div class="topbar"><div class="topbar-left"><span class="eyebrow">${t('个人训练空间','YOUR TRAINING SPACE')}</span><span class="pill ${S.demo?'demo-pill':''}"><i class="dot"></i>${S.demo?t('合成数据演示','Synthetic demo'):t('本地个人档案','Local profile')}</span></div><div class="topbar-right"><input class="date-input" id="selected-date" type="date" value="${S.date}" aria-label="${t('查看日期','View date')}"><button class="language" id="language">${lang==='zh-CN'?'EN / 中文':'中文 / EN'}</button></div></div>${views[view]()}<footer class="footer"><span>AI4薄肌 · ${t('让每一天的行动，都有迹可循。','Make every day’s effort count.')}</span><span>${t('一般健身支持 · 不替代医疗或康复指导','General fitness support · Not medical or rehabilitation care')}</span></footer></main></div>`;
  bind();
  if (window.AI4BOJI_PREVIEW) {
    const banner = document.createElement("div"); banner.className="preview-banner";
    banner.innerHTML=t('线上只读演示 · 所有数据均为合成示例。<a href="../#start">下载并在本地使用 →</a>','Read-only preview · All data is synthetic. <a href="../#start">Run locally →</a>');
    $(".main").prepend(banner);
    document.querySelectorAll("form input, form select, form textarea, form button, [data-generate], [data-forget], [data-edit-memory], [data-edit-log], #export-data").forEach(el=>el.disabled=true);
  }
}
function download(name, content, type) {
  const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');
  a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function bind() {
  document.querySelectorAll('[data-chart]').forEach(host=>{const spec=chartSpecs[Number(host.dataset.chart)];const draw=()=>{host.innerHTML=drawChart(spec.points,spec.unit,spec.label,Math.max(220,host.clientWidth));};draw();const observer=new ResizeObserver(draw);observer.observe(host);chartObservers.push(observer);});
  document.querySelectorAll('[data-view]').forEach(el=>el.onclick=()=>{view=el.dataset.view;render();window.scrollTo(0,0);});
  $('#language').onclick=()=>{lang=lang==='zh-CN'?'en':'zh-CN';try{localStorage.setItem('ai4boji.locale',lang);}catch(_){}render();};
  $('#selected-date').onchange=event=>action(async()=>{chosenDate=event.target.value;await refresh();});
  document.querySelectorAll('[data-date]').forEach(el=>el.onclick=()=>action(async()=>{chosenDate=el.dataset.date;view='today';await refresh();window.scrollTo(0,0);}));
  document.querySelectorAll('[data-generate]').forEach(el=>el.onclick=()=>action(async()=>{await api('plan',{date:S.date});await refresh();toast(t('安排已更新','Plan updated'));},el));
  const checkForm=$('#checkin-form');
  if(checkForm)checkForm.onsubmit=event=>{event.preventDefault();action(async()=>{
    const f=new FormData(checkForm),data={date:S.date,expected_revision:S.checkin?.revision||0};
    for(const key of ['sleep_hours','minutes','energy','soreness'])if(f.get(key)!=='')data[key]=Number(f.get(key));
    if(f.get('pain')!=='')data.pain=f.get('pain')==='true';
    if(S.checkin?.payload.note)data.note=S.checkin.payload.note;
    await api('checkin',data);await api('plan',{date:S.date});await refresh();toast(t('状态已保存，计划已更新','Check-in saved and plan updated'));
  },checkForm.querySelector('button[type=submit]'));};
  const profileForm=$('#profile-form');
  if(profileForm)profileForm.onsubmit=event=>{event.preventDefault();action(async()=>{
    const f=new FormData(profileForm),data=Object.fromEntries(f.entries());data.age=Number(data.age);data.minutes=Number(data.minutes);data.days=f.getAll('days').map(Number);data.locale=lang;data.expected_revision=S.profile?.revision||0;
    await api('profile',data);if(!S.profile){view='today';chosenDate='';}await refresh();toast(t('档案已保存','Profile saved'));
  },profileForm.querySelector('button[type=submit]'));};
  const logForm=$('#log-form');
  if(logForm){
    let submissionId=editingLog?.id||'log:'+crypto.randomUUID();
    $('#add-exercise').onclick=()=>{$('#exercise-rows').insertAdjacentHTML('beforeend',exerciseInput());};
    $('#exercise-rows').onclick=event=>{if(event.target.closest('.remove-ex'))event.target.closest('.exercise-input').remove();};
    if($('#cancel-edit'))$('#cancel-edit').onclick=()=>{editingLog=null;render();};
    logForm.onsubmit=event=>{event.preventDefault();action(async()=>{
      const f=new FormData(logForm),data={id:submissionId,date:f.get('date'),status:f.get('status'),duration_min:f.get('duration_min')===''?null:Number(f.get('duration_min')),note:f.get('note'),expected_revision:editingLog?.revision||0};
      for(const key of ['weight_kg','waist_cm','effort'])if(f.get(key)!=='')data[key]=Number(f.get(key));
      if(f.get('pain')!=='')data.pain=f.get('pain')==='true';
      data.exercises=[...document.querySelectorAll('#exercise-rows .exercise-input')].map(el=>({exercise_id:el.querySelector('.ex-id').value,sets:Number(el.querySelector('.ex-sets').value),reps:Number(el.querySelector('.ex-reps').value),load_kg:Number(el.querySelector('.ex-load').value)}));
      const saved=await api('log',data);editingLog=saved;await refresh();toast(t('已保存；你可以继续更正这条记录','Saved. You can continue editing this record'));
    },logForm.querySelector('button[type=submit]'));};
  }
  document.querySelectorAll('[data-edit-log]').forEach(el=>el.onclick=()=>{editingLog=S.logs.find(r=>r.id===el.dataset.editLog);render();$('.record-form').scrollIntoView({behavior:'instant'});});
  document.querySelectorAll('[data-edit-memory]').forEach(el=>el.onclick=()=>{editingMemory=S.memories.find(r=>r.id===el.dataset.editMemory);render();$('#memory-form').scrollIntoView({behavior:'instant'});});
  document.querySelectorAll('[data-forget]').forEach(el=>el.onclick=()=>action(async()=>{
    if(!window.confirm(t('永久删除这条记忆及其历史版本？','Permanently delete this memory and its revisions?')))return;
    await api('forget',{id:el.dataset.forget});editingMemory=null;await refresh();toast(t('记忆已删除','Memory deleted'));
  },el));
  const memoryForm=$('#memory-form');
  if(memoryForm){
    const memoryId=editingMemory?.id||'memory:'+crypto.randomUUID();
    if($('#cancel-memory'))$('#cancel-memory').onclick=()=>{editingMemory=null;render();};
    memoryForm.onsubmit=event=>{event.preventDefault();action(async()=>{
      const f=new FormData(memoryForm);await api('memory',{id:memoryId,text:f.get('text'),kind:f.get('kind'),confirmed:f.has('confirmed'),expires:f.get('expires')||null,expected_revision:editingMemory?.revision||0});editingMemory=null;await refresh();toast(t('记忆已保存','Memory saved'));
    },memoryForm.querySelector('button[type=submit]'));};
  }
  if($('#export-data'))$('#export-data').onclick=()=>action(async()=>{download('AI4薄肌-export.json',JSON.stringify(await api('export'),null,2),'application/json');});
  if($('#download-report'))$('#download-report').onclick=()=>{const r=S.report;download('AI4薄肌-'+S.date+'.md',`# AI4薄肌\n\n${r.start} → ${r.end}\n\n- ${t('训练天数','Training days')}: ${r.training_days}\n- ${t('训练分钟','Training minutes')}: ${r.total_minutes}\n- ${t('未记录天数','Unrecorded days')}: ${r.unknown_days}\n\n${L(r.reflection)}\n\n${t('记录依据','Source records')}: ${r.source_ids.join(', ')}\n`,'text/markdown');};
}
refresh().catch(error=>{ $('#app').innerHTML=`<main class="loading"><strong>AI4薄肌</strong><p>${t('无法读取本地服务。请确认服务仍在运行，再刷新页面。','Cannot reach the local service. Check that it is running, then reload.')}</p><p>${E(error.message)}</p></main>`; });
