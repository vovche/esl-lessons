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
  await root.locator('.sim-review summary').click();
  assert.equal(await root.locator('.sim-review-item').count(),2);
  assert.match(await root.locator('.sim-review-item').first().innerText(),/варто повторити/);
  assert.match(await root.locator('.sim-review-item').last().innerText(),/вдалося з першого вибору/);
  await root.locator('.sim-source summary').click();
  assert.equal(await root.locator('.sim-source p').innerText(),learn.source);
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
   assert.equal(await root.locator('.sim-review').count(),0);
   if(i) assert.match(await root.locator('.sim-feedback').innerText(),/Завершити місію/);
   await root.getByRole('button',{name:i?'Завершити місію':'Наступний хід',exact:true}).click();
  }
  assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);
  await root.locator('.sim-review summary').click();
  assert((await root.locator('.sim-review-item').first().innerText()).includes(check.steps[0].hint));
  assert.equal(await root.locator('.sim-review-item').last().locator('.sim-note').count(),0);
  await root.locator('.sim-source summary').click();
  assert.equal(await root.locator('.sim-source p').innerText(),check.source);
  await page.setViewportSize({width:320,height:740});
  assert(await root.evaluate(el=>el.scrollWidth<=el.clientWidth+1));
  for(const summary of await root.locator('summary').all()) assert((await summary.boundingBox()).height>=44);
  await root.screenshot({path:`/tmp/esl-sim-${grade}-summary-mobile.png`});
  await root.getByRole('button',{name:'Пройти ще раз',exact:true}).click();
  await page.setViewportSize({width:1280,height:900});await root.screenshot({path:`/tmp/esl-sim-${grade}-desktop.png`});
  assert.equal(await root.locator('a[href*="teacher"],a[href*="key."]').count(),0);
  assert.deepEqual(errors,[]);console.log('PASS browser',grade,slug,'mobile/desktop, hints, pause, reload, draft, check, replay');await context.close();
 }
 for(const viewport of [{width:320,height:740},{width:844,height:390}]) {
  const context=await browser.newContext({viewport,isMobile:true,hasTouch:true});const page=await context.newPage();
  await page.route('**/*',route=>route.request().url().startsWith('http://127.0.0.1:8876/')?route.continue():route.abort());
  await page.goto('http://127.0.0.1:8876/9/future-forms-v2/',{waitUntil:'domcontentloaded'});
  await page.locator('.sim-launch:visible').click();
  const modal=page.locator('.sim-dialog');const root=modal.locator('[data-lesson-simulations]');
  await root.locator('[data-sim-load]').click();await root.getByRole('button',{name:'Почати місію',exact:true}).last().click();
  for(let i=0;i<2;i++) {await root.locator('.sim-choice').first().click();await root.getByRole('button',{name:i?'Завершити місію':'Наступний хід',exact:true}).click();}
  const scene=await page.locator('#sceneCounter').innerText();
  await root.locator('textarea').fill('My example.');await root.locator('textarea').press('m');await root.locator('textarea').press('ArrowRight');
  assert.equal(await page.locator('#sceneMapDialog').evaluate(el=>el.open),false);
  assert.equal(await page.locator('#sceneCounter').innerText(),scene);
  assert(await modal.evaluate(el=>el.scrollWidth<=el.clientWidth+1));
  await modal.screenshot({path:`/tmp/esl-sim-fullscreen-${viewport.width}.png`});
  await page.keyboard.press('Escape');assert.equal(await modal.evaluate(el=>el.open),false);
  assert(await page.locator('.sim-launch:visible').evaluate(el=>el===document.activeElement));
  await page.locator('.sim-launch:visible').click();assert(await root.locator('.sim-score').isVisible());
  await modal.getByRole('button',{name:'Повернутися до уроку',exact:true}).click();
  await context.close();console.log('PASS fullscreen missions',viewport.width,'portrait/landscape access, completion, typing isolation, close/reopen');
 }
 const context=await browser.newContext(); const page=await context.newPage();
 await page.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})});
 await page.route('**/simulations.json',r=>r.abort());
 await page.goto('http://127.0.0.1:8876/6/sb-hello/',{waitUntil:'domcontentloaded'});const root=page.locator('[data-lesson-simulations]');await root.locator('[data-sim-load]').click();await root.getByText('Не вдалося завантажити місії.',{exact:false}).waitFor();
 await page.unroute('**/simulations.json');await root.locator('[data-sim-load]').click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();await root.getByRole('button',{name:'Пауза',exact:true}).click();await root.getByRole('button',{name:'← Інші місії',exact:true}).click();await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();assert(await root.getByRole('button',{name:'Продовжити',exact:true}).isVisible());assert.match(await root.innerText(),/Браузер не зберігає поступ/);console.log('PASS network retry and blocked storage session resume with warning');
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
