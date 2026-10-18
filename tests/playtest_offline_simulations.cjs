// Requires Playwright and Chromium. SIM_BASE_URL accepts a local or published site, including a project prefix.
const {chromium}=require('playwright');const assert=require('node:assert/strict');const fs=require('node:fs');
const base=process.env.SIM_BASE_URL||'http://127.0.0.1:8876/';
(async()=>{
 const browser=await chromium.launch();const reports=[];
 await Promise.all([[6,'sb-hello','g6-002'],[7,'sb-u3-reading','g7-037'],[9,'gerund','g9-023']].map(async([grade,slug,id])=>{
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
  // Isolate third-party embeds; all site resources and service workers use the real server.
  await context.route('**/*',route=>new URL(route.request().url()).origin===new URL(base).origin?route.continue():route.abort());
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const dataResponse=await context.request.get(new URL(`${grade}/simulations.json`,base).href);
  assert(dataResponse.ok());const lesson=(await dataResponse.json()).lessons.find(l=>l.id===id);assert(lesson);
  const url=new URL(`${grade}/${slug}/`,base).href;
  const root=page.locator('[data-lesson-simulations]');
  async function load(){await root.locator('[data-sim-load]').click();await root.locator('.sim-select').waitFor();}
  async function reload(){await page.reload({waitUntil:'domcontentloaded'});await load();assert.equal(await root.locator('select').inputValue(),id);}
  await page.goto(url,{waitUntil:'domcontentloaded'});await load();
  await root.getByText('Місії готові до роботи без інтернету й перезавантаження',{exact:false}).waitFor();
  await root.locator('select').selectOption(id);await root.getByRole('button',{name:'Почати місію',exact:true}).first().click();
  const learn=lesson.games[0];
  await root.locator('.sim-choice').nth(learn.steps[0].choices.findIndex(c=>c.effect==='retry')).click();
  await root.getByRole('button',{name:'Підказка',exact:true}).click();
  await root.getByRole('button',{name:'Пауза',exact:true}).click();await context.setOffline(true);await reload();
  assert(await page.locator('.offline-page').isVisible());
  await root.getByRole('button',{name:'Продовжити місію',exact:true}).click();
  assert.match(await root.innerText(),/Місію призупинено/);
  await root.getByRole('button',{name:'Продовжити',exact:true}).click();assert((await root.innerText()).includes(learn.steps[0].hint));
  for(let i=0;i<2;i++){await root.locator('.sim-choice').nth(learn.steps[i].choices.findIndex(c=>c.effect==='advance')).click();await root.getByRole('button',{name:i?'Завершити місію':'Наступний хід',exact:true}).click();}
  assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);await root.locator('textarea').fill('My offline draft.');await reload();
  await root.getByRole('button',{name:'Переглянути результат',exact:true}).click();assert.equal(await root.locator('textarea').inputValue(),'My offline draft.');
  await root.getByRole('button',{name:'Обрати іншу місію',exact:true}).click();await root.getByRole('button',{name:'Почати місію',exact:true}).click();
  const check=lesson.games[1];await root.locator('.sim-choice').nth(check.steps[0].choices.findIndex(c=>c.effect==='retry')).click();await reload();
  await root.getByRole('button',{name:'Продовжити місію',exact:true}).click();assert(await root.locator('.sim-choice').first().isDisabled());assert.equal(await root.getByRole('button',{name:'Підказка',exact:true}).count(),0);
  await root.getByRole('button',{name:'Наступний хід',exact:true}).click();await root.locator('.sim-choice').nth(check.steps[1].choices.findIndex(c=>c.effect==='advance')).click();await root.getByRole('button',{name:'Завершити місію',exact:true}).click();assert.match(await root.locator('.sim-score').innerText(),/1 із 2/);
  const tab=await context.newPage();await tab.goto(url,{waitUntil:'domcontentloaded'});await tab.locator('[data-sim-load]').click();assert.equal(await tab.locator('.sim-select').inputValue(),id);assert.equal(await tab.getByRole('button',{name:'Переглянути результат',exact:true}).count(),2);await tab.close();
  const keys=await page.evaluate(async()=>{const cache=await caches.open('esl-missions-v1');return(await cache.keys()).map(r=>r.url)});
  assert(keys.every(k=>!k.includes('/teacher/')&&!k.includes('jolly-phonics')));assert(keys.some(k=>k===new URL(`${grade}/simulations.json`,base).href));
  await page.locator('[data-offline-return]').click();await page.getByText('Зв’язок поки недоступний.',{exact:false}).waitFor();
  assert(await page.locator('.offline-page').isVisible());
  await context.setOffline(false);await page.locator('[data-offline-return]').waitFor({state:'visible'});await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),page.locator('[data-offline-return]').click()]);assert.equal(await page.locator('.offline-page').count(),0);await load();assert.equal(await root.locator('.sim-select').inputValue(),id);
  assert.deepEqual(errors,[]);reports.push({grade,id,offlineReload:true,pausedHint:true,firstChoiceLocked:true,draft:true,newTab:true,reconnection:true,offlineConnectionProbe:true});await context.close();console.log('PASS offline',grade,id,base);
 }));
 await browser.close();fs.writeFileSync('/tmp/esl-offline-results.json',JSON.stringify({base,reports},null,2));
})().catch(e=>{console.error(e);process.exit(1)});
