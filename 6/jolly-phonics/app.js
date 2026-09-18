(() => {
  const $ = id => document.getElementById(id);
  const cards = window.CARDS;
  const storeKey = 'jolly-phonics-v1';
  const defaults = {name:'', accent:'uk', gender:'female', autoplay:false, swipeHintSeen:false, history:[], session:{index:0,seen:[0],elapsed:0}};
  let saved;
  try { saved = {...defaults, ...JSON.parse(localStorage.getItem(storeKey) || '{}')}; } catch { saved = {...defaults}; }
  let index = Math.max(0,Math.min(cards.length-1,saved.session?.index||0));
  let seen = new Set(saved.session?.seen?.length?saved.session.seen:[0]);
  let elapsedBase = Number(saved.session?.elapsed)||0, activeSince=Date.now(), trackingActive=!document.hidden, completed=false, timerId, coachTimer, touchX=null, suppressCardTap=false;
  let swRegistration=null, installPrompt=null, reloadForUpdate=false, reportUrl=null;
  const voiceNames = {uk:'Британська', us:'Американська', female:'жіночий', male:'чоловічий'};

  function save(){ localStorage.setItem(storeKey, JSON.stringify(saved)); }
  function elapsedSeconds(){return elapsedBase+(trackingActive?(Date.now()-activeSince)/1000:0);}
  function saveProgress(){if(!completed)saved.session={index,seen:[...seen],elapsed:Math.round(elapsedSeconds())};save();}
  function voiceKey(){ return `${saved.accent}-${saved.gender}`; }
  function voiceLabel(){ return `${voiceNames[saved.accent]} · ${voiceNames[saved.gender]}`; }
  function fmt(seconds){ const m=Math.floor(seconds/60),s=Math.floor(seconds%60); return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`; }
  function localDate(iso){ return new Date(iso).toLocaleDateString('uk-UA',{day:'2-digit',month:'2-digit',year:'numeric'}); }
  function escapeHtml(value){ return value.replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
  function highlighted(word, grapheme){
    const options = grapheme.split('/'); let pos=-1, match='';
    for(const option of options){ const p=word.toLowerCase().indexOf(option); if(p>=0){pos=p;match=option;break;} }
    if(pos<0) return escapeHtml(word);
    return `${escapeHtml(word.slice(0,pos))}<span class="target">${escapeHtml(word.slice(pos,pos+match.length))}</span>${escapeHtml(word.slice(pos+match.length))}`;
  }
  function audioPath(i=index){ const number=String(cards[i].id).padStart(2,'0'); return `assets/audio/${voiceKey()}/${number}.mp3`; }
  async function play(i=index){ const audio=$('audio'); audio.src=audioPath(i); try{await audio.play();$('playBtn').classList.add('playing');}catch{$('playBtn').classList.remove('playing');} }
  function render(shouldPlay=false){
    const c=cards[index]; seen.add(index);
    $('groupLabel').textContent=`Група ${c.group}`; $('counter').textContent=`${index+1} / ${cards.length}`;
    $('progressBar').style.width=`${((index+1)/cards.length)*100}%`; $('grapheme').textContent=c.grapheme; $('ipa').textContent=c.ipa;
    $('illustration').src=c.illustration.replace(/^\//,''); $('illustration').alt=c.words.join(' і ');
    $('word').innerHTML=c.words.map(w=>highlighted(w,c.grapheme)).join(' · '); $('voiceLabel').textContent=voiceLabel();
    $('settingsVoice').textContent=voiceLabel(); $('prevBtn').disabled=index===0; $('nextBtn').textContent=index===cards.length-1?'Завершити ✓':'Далі →';
    $('originalImage').src=c.card.replace(/^\//,''); document.title=`${c.grapheme} — ${c.words.join(', ')} | Jolly Phonics`;
    saveProgress();
    if(shouldPlay && saved.autoplay) setTimeout(()=>play(),120);
  }
  function showSwipeCoach(){
    const coach=$('swipeCoach'); if(saved.swipeHintSeen||!coach)return;
    clearTimeout(coachTimer); coach.hidden=false; coach.classList.remove('leaving');
    coachTimer=setTimeout(()=>{coach.classList.add('leaving');setTimeout(()=>{coach.hidden=true;coach.classList.remove('leaving');},320);},5000);
  }
  function hideSwipeCoach(remember=false){
    const coach=$('swipeCoach'); if(!coach)return;
    clearTimeout(coachTimer); coach.classList.add('leaving');
    if(remember&&!saved.swipeHintSeen){saved.swipeHintSeen=true;save();}
    setTimeout(()=>{coach.hidden=true;coach.classList.remove('leaving');},320);
  }
  function move(delta){
    hideSwipeCoach(true);
    if(delta>0 && index===cards.length-1){ finish(); return; }
    const next=Math.max(0,Math.min(cards.length-1,index+delta)); if(next===index)return; index=next; render(true);
  }
  function finish(){
    const seconds=Math.max(1,Math.round(elapsedSeconds()));
    if(seen.size<cards.length){ alert(`Переглянуто ${seen.size} з 42 карток. Переглянь пропущені картки, щоб завершити коло.`); return; }
    const now=new Date(); const entry={completedAt:now.toISOString(),date:now.toLocaleDateString('sv-SE'),seconds,average:+(seconds/cards.length).toFixed(1),voice:voiceKey()};
    completed=true; saved.history.unshift(entry); saved.history=saved.history.slice(0,200); saved.session={index:0,seen:[0],elapsed:0}; save();
    const today=saved.history.filter(x=>x.date===entry.date).length;
    $('completeText').textContent=`Чудова робота, ${saved.name}!`; $('resultTime').textContent=fmt(seconds); $('resultAvg').textContent=`${entry.average} с`; $('resultCount').textContent=today;
    refreshHistory(); $('completeDialog').showModal();
  }
  function restart(){ completed=false; index=0; elapsedBase=0; activeSince=Date.now(); trackingActive=true; seen=new Set([0]); saved.session={index:0,seen:[0],elapsed:0}; save(); $('completeDialog').close(); render(false); }
  function setChoice(id,value){ document.querySelectorAll(`#${id} button`).forEach(b=>b.classList.toggle('active',b.dataset.value===value)); }
  function refreshSettings(){ $('studentName').value=saved.name; $('autoplay').checked=saved.autoplay; setChoice('accentChoice',saved.accent); setChoice('genderChoice',saved.gender); $('settingsVoice').textContent=voiceLabel(); refreshHistory(); }
  function refreshHistory(){
    const h=saved.history; const today=new Date().toLocaleDateString('sv-SE'); const todayCount=h.filter(x=>x.date===today).length;
    $('statsSummary').textContent=h.length?`${todayCount} сьогодні · ${h.length} усього`:'Ще немає завершених кіл';
    prepareReportLinks();
    if(!h.length)$('exportStatus').textContent='Кнопка стане активною після першого повного проходження.';
    else if($('exportStatus').textContent.startsWith('Кнопка'))$('exportStatus').textContent='';
    $('historyList').innerHTML=h.slice(0,8).map((x,i)=>`<div class="history-row"><span>${localDate(x.completedAt)} · #${h.length-i}</span><span>${fmt(x.seconds)}</span><span>${x.average} с/к.</span></div>`).join('');
  }
  function choose(type,value){ saved[type]=value; save(); refreshSettings(); render(false); }

  function setOfflineStatus(text, ready=false){
    const label=$('offlineStatus'); if(!label)return; label.textContent=text;
    $('offlineBtn').classList.toggle('ready',ready);
    if(ready)$('offlineBtn').textContent='Збережено офлайн ✓';
  }
  async function requestOfflineCache(){
    if(!swRegistration){setOfflineStatus('Офлайн-режим недоступний у цьому браузері');return;}
    setOfflineStatus('Завантажуємо картки й 4 голоси…');
    const worker=swRegistration.active||swRegistration.waiting||swRegistration.installing;
    worker?.postMessage({type:'CACHE_ALL'});
  }
  async function initPwa(){
    if(!('serviceWorker' in navigator)){setOfflineStatus('Браузер не підтримує офлайн-кеш');return;}
    try{
      swRegistration=await navigator.serviceWorker.register('sw.js',{scope:'./',updateViaCache:'none'});
      await navigator.serviceWorker.ready;
      navigator.serviceWorker.addEventListener('message',event=>{
        const data=event.data||{};
        if(data.type==='CACHE_PROGRESS') setOfflineStatus(`Збережено ${data.done} із ${data.total} ресурсів…`);
        if(data.type==='CACHE_COMPLETE') setOfflineStatus('Усі картки й голоси готові офлайн',true);
        if(data.type==='CACHE_ERROR') setOfflineStatus('Не все вдалося зберегти. Перевір інтернет і спробуй ще раз.');
        if(data.type==='UPDATE_READY'){
          setOfflineStatus(`Доступна версія ${data.version}`);
          $('offlineBtn').textContent='Оновити зараз';
          $('offlineBtn').onclick=()=>{reloadForUpdate=true;location.reload();};
        }
      });
      setOfflineStatus(navigator.onLine?'Готуємо повну офлайн-копію…':'Працюємо офлайн');
      requestOfflineCache();
      swRegistration.update().catch(()=>{});
      navigator.serviceWorker.addEventListener('controllerchange',()=>{if(reloadForUpdate)location.reload();});
      if(/iphone|ipad|ipod/i.test(navigator.userAgent)&&!navigator.standalone){$('installBtn').hidden=false;$('installBtn').textContent='Як встановити на iPhone / iPad';}
    }catch(error){setOfflineStatus('Не вдалося підготувати офлайн-копію');}
  }
  window.addEventListener('beforeinstallprompt',event=>{
    event.preventDefault();installPrompt=event;$('installBtn').hidden=false;
  });
  window.addEventListener('appinstalled',()=>{$('installBtn').hidden=true;installPrompt=null;});
  async function installApp(){
    if(installPrompt){await installPrompt.prompt();installPrompt=null;$('installBtn').hidden=true;return;}
    if(/iphone|ipad|ipod/i.test(navigator.userAgent))alert('У Safari натисни «Поділитися», а потім «На початковий екран».');
  }

  function csv(){
    const q=v=>`"${String(v).replaceAll('"','""')}"`; const rows=[['Учень','Дата','Час завершення','Тривалість, с','Середнє на картку, с','Акцент','Голос']];
    for(const x of saved.history){ const [accent,gender]=x.voice.split('-'); rows.push([saved.name,localDate(x.completedAt),new Date(x.completedAt).toLocaleTimeString('uk-UA'),x.seconds,x.average,voiceNames[accent],voiceNames[gender]]); }
    return '\ufeff'+rows.map(row=>row.map(q).join(';')).join('\r\n');
  }
  function prepareReportLinks(){
    if(reportUrl){URL.revokeObjectURL(reportUrl);reportUrl=null;}
    const links=[$('exportBtn'),$('completeExport')];
    if(!saved.history.length){links.forEach(link=>{link.removeAttribute('href');link.removeAttribute('download');link.setAttribute('aria-disabled','true');});return;}
    reportUrl=URL.createObjectURL(new Blob([csv()],{type:'text/csv;charset=utf-8'}));
    const filename=`jolly-phonics-${(saved.name||'student').replace(/\s+/g,'-')}.csv`;
    links.forEach(link=>{link.href=reportUrl;link.download=filename;link.setAttribute('aria-disabled','false');});
  }
  function exportReport(event){
    if(!saved.history.length){event.preventDefault();$('exportStatus').textContent='Спочатку заверши всі 42 картки.';return;}
    const message=`Звіт із ${saved.history.length} ${saved.history.length===1?'проходження':'проходжень'} завантажено.`;
    $('exportStatus').textContent=message; $('completeExportStatus').textContent=message;
  }

  $('offlineBtn').onclick=requestOfflineCache; $('installBtn').onclick=installApp;
  $('playBtn').onclick=()=>play(); $('audio').onended=()=>$('playBtn').classList.remove('playing'); $('audio').onpause=()=>$('playBtn').classList.remove('playing');
  $('prevBtn').onclick=()=>move(-1); $('nextBtn').onclick=()=>move(1); $('againBtn').onclick=restart; $('exportBtn').onclick=$('completeExport').onclick=exportReport;
  $('settingsBtn').onclick=()=>{refreshSettings();$('settingsDialog').showModal();}; $('originalBtn').onclick=()=>$('originalDialog').showModal(); $('closeOriginal').onclick=()=>$('originalDialog').close();
  $('studentName').onchange=e=>{saved.name=e.target.value.trim();save();}; $('autoplay').onchange=e=>{saved.autoplay=e.target.checked;save();};
  $('accentChoice').onclick=e=>{if(e.target.dataset.value)choose('accent',e.target.dataset.value);}; $('genderChoice').onclick=e=>{if(e.target.dataset.value)choose('gender',e.target.dataset.value);}; $('previewVoice').onclick=()=>play();
  $('setupForm').onsubmit=e=>{e.preventDefault(); const name=$('setupName').value.trim(); if(!name)return; saved.name=name;elapsedBase=0;activeSince=Date.now();trackingActive=true;saveProgress();$('setupDialog').close();setTimeout(showSwipeCoach,250);};
  $('setupDialog').addEventListener('cancel',e=>{if(!saved.name)e.preventDefault();});
  document.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;if(e.key==='ArrowRight')move(1);if(e.key==='ArrowLeft')move(-1);if(e.key===' '||(e.key==='Enter'&&document.activeElement===$('card'))) {e.preventDefault();play();}});
  $('card').addEventListener('click',e=>{if(e.target.closest('button,a'))return;if(suppressCardTap){suppressCardTap=false;return;}play();});
  $('card').addEventListener('touchstart',e=>{touchX=e.changedTouches[0].clientX;suppressCardTap=false;},{passive:true});
  $('card').addEventListener('touchend',e=>{if(touchX===null)return;const dx=e.changedTouches[0].clientX-touchX;suppressCardTap=Math.abs(dx)>12;if(Math.abs(dx)>55)move(dx<0?1:-1);touchX=null;},{passive:true});
  document.addEventListener('visibilitychange',()=>{if(document.hidden&&trackingActive){elapsedBase=elapsedSeconds();trackingActive=false;saveProgress();}else if(!document.hidden&&!trackingActive){activeSince=Date.now();trackingActive=true;}});
  window.addEventListener('pagehide',saveProgress);
  window.addEventListener('beforeunload',()=>{if(reportUrl)URL.revokeObjectURL(reportUrl);});
  timerId=setInterval(()=>$('timer').textContent=fmt(elapsedSeconds()),1000);
  refreshSettings(); render(false); if(!saved.name)$('setupDialog').showModal();else setTimeout(showSwipeCoach,400);
  initPwa();
})();
