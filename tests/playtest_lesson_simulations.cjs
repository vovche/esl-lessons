// Run with a local server on port 8876 and Playwright available via NODE_PATH.
const {chromium}=require('playwright');
const fs=require('node:fs'); const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true});
 for(const [grade,slug] of [[6,'sb-hello'],[7,'sb-u3-reading'],[9,'gerund']]){
  const context=await browser.newContext({viewport:{width:390,height:844}});const page=await context.newPage();const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>route.request().url().startsWith('http://127.0.0.1:8876/')?route.continue():route.abort());
  const data=JSON.parse(fs.readFileSync(`${process.cwd()}/${grade}/simulations.json`)); const lesson=data.lessons.find(l=>l.slugs.includes(slug));
  await page.goto(`http://127.0.0.1:8876/${grade}/${slug}/`,{waitUntil:'domcontentloaded'});
  const root=page.locator('[data-lesson-simulations]');await root.locator('[data-sim-load]').click();await root.locator('.sim-mode-card').first().waitFor();
  assert.equal(await root.locator('.sim-mode-card').count(),2);
  const overflow=await root.evaluate(el=>({width:el.getBoundingClientRect().width,scroll:el.scrollWidth,client:el.clientWidth}));assert(overflow.scroll<=overflow.client+1,JSON.stringify(overflow));
  await root.screenshot({path:`/tmp/esl-sim-${grade}-mobile.png`});
  await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();
  const learn=lesson.games.find(g=>g.mode==='learn');
  assert(await root.locator('.sim-skill-focus').isVisible());
  await root.locator('.sim-choice').nth(learn.steps[0].choices.findIndex(c=>c.effect==='retry')).click();
  await root.getByRole('button',{name:'Підказка',exact:true}).click();assert(await root.locator('.sim-note').isVisible());
  await root.locator('.sim-choice').nth(learn.steps[0].choices.findIndex(c=>c.effect==='advance')).click();
  await root.getByRole('button',{name:'Наступний хід',exact:true}).click();
  await root.getByRole('button',{name:'Пауза',exact:true}).click();assert.equal(await root.locator('.sim-choice').count(),0);
  await page.reload({waitUntil:'domcontentloaded'});await root.locator('[data-sim-load]').click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();
  await root.getByRole('button',{name:'Продовжити',exact:true}).click();assert.match(await root.locator('.sim-progress-label').innerText(),/2 із 2/);
  await root.locator('.sim-choice').nth(learn.steps[1].choices.findIndex(c=>c.effect==='advance')).click();await root.getByRole('button',{name:'Завершити місію',exact:true}).click();
  assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);
  await root.locator('.sim-reflection summary').click();
  assert((await root.locator('.sim-reflection').innerText()).includes(learn.reflection.prompt));
  assert.equal(await root.locator('.sim-reflection input,.sim-reflection textarea').count(),0);
  assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);
  await root.locator('textarea').fill('My own sentence.');await root.getByRole('button',{name:'Зберегти репліку',exact:true}).click();
  await root.getByRole('button',{name:'Обрати іншу місію',exact:true}).click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();assert.equal(await root.locator('textarea').inputValue(),'My own sentence.');
  await root.getByRole('button',{name:'Обрати іншу місію',exact:true}).click();await root.getByRole('button',{name:'Почати місію',exact:true}).nth(1).click();
  const check=lesson.games.find(g=>g.mode==='check');
  for(let i=0;i<2;i++){
   await root.locator('.sim-choice').nth(check.steps[i].choices.findIndex(c=>c.effect===(i?'advance':'retry'))).click();assert.equal(await root.getByRole('button',{name:'Підказка',exact:true}).count(),0);
   await root.getByRole('button',{name:i?'Завершити місію':'Наступний хід',exact:true}).click();
  }
  assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);
  await root.getByRole('button',{name:'Пройти ще раз',exact:true}).click();
  await page.setViewportSize({width:1280,height:900});await root.screenshot({path:`/tmp/esl-sim-${grade}-desktop.png`});
  assert.equal(await root.locator('a[href*="teacher"],a[href*="key."]').count(),0);
  assert.deepEqual(errors,[]);console.log('PASS browser',grade,slug,'mobile/desktop, hints, pause, reload, draft, check, replay');await context.close();
 }
 const context=await browser.newContext(); const page=await context.newPage();
 await page.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})});
 await page.route('**/simulations.json',r=>r.abort());
 await page.goto('http://127.0.0.1:8876/6/sb-hello/',{waitUntil:'domcontentloaded'});const root=page.locator('[data-lesson-simulations]');await root.locator('[data-sim-load]').click();await root.getByText('Не вдалося завантажити місії.',{exact:false}).waitFor();
 await page.unroute('**/simulations.json');await root.locator('[data-sim-load]').click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();await root.getByRole('button',{name:'Пауза',exact:true}).click();await root.getByRole('button',{name:'← Інші місії',exact:true}).click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();assert(await root.getByRole('button',{name:'Продовжити',exact:true}).isVisible());console.log('PASS network retry and blocked storage session resume');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
