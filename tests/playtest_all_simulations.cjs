// Full learner-path smoke test: every calendar mission + every public integration.
// Requires HTTP server on 8876 and Playwright on NODE_PATH. No production writes.
const {chromium}=require('playwright');
const fs=require('node:fs');const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch();const reports=[];
 await Promise.all([6,7,9].map(async grade=>{
  const data=JSON.parse(fs.readFileSync(`${grade}/simulations.json`));
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
  const page=await context.newPage();page.setDefaultTimeout(10000);
  const report={grade,lessons:0,games:0,routes:0,errors:[]};reports.push(report);
  page.on('pageerror',e=>report.errors.push(e.message));
  await page.route('**/*',r=>{const u=r.request().url();return u.startsWith('http://127.0.0.1:8876/')&&!['image','media','font'].includes(r.request().resourceType())?r.continue():r.abort()});
  const root=page.locator('[data-lesson-simulations]');const visited=new Set();
  async function load(slug){
   await page.goto(`http://127.0.0.1:8876/${grade}/${slug}/`,{waitUntil:'domcontentloaded'});
   // Disable only smooth scrolling for this bulk interaction check. Default-motion
   // layouts and transitions are covered by the separate student playtests.
   await page.addStyleTag({content:'html { scroll-behavior: auto !important; }'});
   if(await page.locator('.sim-launch:visible').count()) await page.locator('.sim-launch:visible').click();
   await root.locator('[data-sim-load]').click();await root.locator('.sim-select').waitFor();
   if(!visited.has(slug)){visited.add(slug);report.routes++;}
   assert(await root.evaluate(el=>el.scrollWidth<=el.clientWidth+1),'horizontal overflow');
  }
  for(const lesson of data.lessons){
   try{
    await load(lesson.slugs[0]);await root.locator('.sim-select').selectOption(lesson.id);
    for(const game of lesson.games){
     await root.getByRole('button',{name:'Почати місію',exact:true}).nth(game.mode==='learn'?0:1).click();
     for(let i=0;i<game.steps.length;i++){
      const step=game.steps[i];const wanted=game.mode==='check'&&i===0?'retry':'advance';
      await root.locator('.sim-choice').nth(step.choices.findIndex(c=>c.effect===wanted)).click();
      await root.locator('.sim-feedback').waitFor({state:'visible'});
      await root.getByRole('button',{name:i===game.steps.length-1?'Завершити місію':'Наступний хід',exact:true}).click();
     }
     assert((await root.locator('.sim-score').innerText()).includes(game.mode==='learn'?'2 із 2':'1 із 2'));
     await root.locator('.sim-review summary').click();assert.equal(await root.locator('.sim-review-item').count(),2);
     if(game.source){await root.locator('.sim-source summary').click();assert.equal(await root.locator('.sim-source p').innerText(),game.source);}
     else assert.equal(await root.locator('.sim-source').count(),0);
     assert(await root.evaluate(el=>el.scrollWidth<=el.clientWidth+1));
     report.games++;
     await root.getByRole('button',{name:'Обрати іншу місію',exact:true}).click();
    }
    report.lessons++;
    if(report.lessons%20===0) console.log(`Grade ${grade}: ${report.lessons}/${data.lessons.length} lessons completed`);
   }catch(e){report.errors.push(`${lesson.id}: ${e.message}`);console.error(lesson.id,e.message);await page.screenshot({path:`/tmp/esl-all-${lesson.id}-failure.png`}).catch(()=>{});}
  }
  for(const slug of new Set(data.lessons.flatMap(l=>l.slugs))) if(!visited.has(slug)){
   try{await load(slug)}catch(e){report.errors.push(`${slug}: ${e.message}`)}
  }
  await context.close();console.log(JSON.stringify(report));
 }));
 await browser.close();fs.writeFileSync('/tmp/esl-all-browser-results.json',JSON.stringify(reports,null,2));
 assert(reports.every(r=>r.errors.length===0),'Browser failures; see /tmp/esl-all-browser-results.json');
})().catch(e=>{console.error(e);process.exitCode=1});
