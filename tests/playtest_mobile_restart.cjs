// Real browser-process restarts with one persistent profile per case.
// Network loss uses a blocking local CONNECT proxy, without TLS interception.
// Mobile emulation is not evidence from physical Android/iOS devices.
// NODE_PATH=... GRADE=6 SIM_BROWSER=chromium node tests/playtest_mobile_restart.cjs
// Defaults: grades 6,7,9 × Chromium and WebKit against the published site.
const {chromium,webkit}=require('playwright');
const http=require('node:http'),net=require('node:net');
// Transport-level outage also blocks service-worker fetches. Playwright's offline
// flag differs between browser engines and is deliberately kept false here.
function createTransport(){
 let blocked=false,denied=0;const sockets=new Set();
 const track=s=>{sockets.add(s);s.on('close',()=>sockets.delete(s));return s;};
 const server=http.createServer((req,res)=>{track(req.socket);if(blocked){denied++;res.destroy();return;}const target=new URL(req.url);const upstream=http.request(target,{method:req.method,headers:req.headers},r=>{res.writeHead(r.statusCode,r.headers);r.pipe(res);});upstream.on('error',()=>res.destroy());req.pipe(upstream);});
 server.on('connect',(req,client,head)=>{track(client);if(blocked){denied++;client.destroy();return;}const [hostname,port]=req.url.split(':');const upstream=track(net.connect(Number(port)||443,hostname,()=>{if(blocked){denied++;client.destroy();upstream.destroy();return;}client.write('HTTP/1.1 200 Connection Established\r\n\r\n');if(head.length)upstream.write(head);client.pipe(upstream);upstream.pipe(client);}));upstream.on('error',()=>client.destroy());client.on('error',()=>upstream.destroy());});
 return{async start(){await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));return 'http://127.0.0.1:'+server.address().port;},toggle(value){blocked=value;for(const s of sockets)s.destroy();},denied:()=>denied,async close(){this.toggle(true);await new Promise(resolve=>server.close(resolve));}};
}
const transport=createTransport();
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const base=process.env.SIM_BASE_URL||'https://vovche.github.io/esl-lessons/';
const definitions={6:['sb-hello','g6-002'],7:['sb-u3-reading','g7-037'],9:['gerund','g9-023']};
const grades=(process.env.GRADE||'6,7,9').split(',').map(Number);
const engines=(process.env.SIM_BROWSER||'chromium,webkit').split(',');
const output=process.env.SIM_ARTIFACT_DIR||fs.mkdtempSync(path.join(os.tmpdir(),'esl-mobile-restart-'));
fs.mkdirSync(output,{recursive:true});
(async()=>{
const reports=[];const proxyURL=await transport.start();
for(const grade of grades)for(const engine of engines){
 const report={grade,engine,base,transport:'HTTP CONNECT proxy; Playwright offline:false always',emulationOnly:true,passed:false,stage:'initialization',screenshots:[]};reports.push(report);
 const dir=path.join(output,`${grade}-${engine}`);fs.mkdirSync(dir,{recursive:true});const profile=fs.mkdtempSync(path.join(os.tmpdir(),`esl-mobile-${grade}-${engine}-`));report.userDataDir=profile;
 let context,page;
 async function launch(offline){
  transport.toggle(offline);
  const type={chromium,webkit}[engine];assert(type,`Unsupported SIM_BROWSER: ${engine}`);
  context=await type.launchPersistentContext(profile,{headless:true,viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1,reducedMotion:'reduce',offline:false,proxy:{server:proxyURL},...(engine==='chromium'?{args:['--no-sandbox']}:{})});
  // Pass site requests through unchanged; isolate external media and disable the
  // browser HTTP cache so this test specifically exercises persisted SW caches.
  await context.route('**/*',route=>new URL(route.request().url()).origin===new URL(base).origin?route.continue():route.abort());
  context.setDefaultTimeout(30000);page=await context.newPage();page.on('pageerror',e=>report.pageErrors.push(e.message));report.browserVersion=context.browser().version();
 }
 async function close(){const browser=context.browser();await context.close();assert.equal(browser.isConnected(),false);context=null;report.closedProcesses=(report.closedProcesses||0)+1;}
 async function shot(name){const file=path.join(dir,name+'.png');await page.screenshot({path:file,fullPage:false});report.screenshots.push(file);}
 function root(){return page.locator('[data-lesson-simulations]');}
 async function load(){const launcher=page.getByRole('button',{name:'Ігрові місії',exact:true}).filter({visible:true});if(await launcher.count())await launcher.first().tap();await root().locator('[role="status"]').first().waitFor();await root().locator('[data-sim-load]').tap();await root().locator('select').waitFor();}
 async function offlineNavigate(url){
  await page.goto(url,{waitUntil:'domcontentloaded'});
  const networkReachable=await page.evaluate(async probe=>{try{await fetch(probe,{cache:'no-store'});return true}catch(_){return false}},new URL('simulations-sw.js?restart-probe='+Date.now(),base).href);
  assert.equal(networkReachable,false,'Offline launch must block an uncached network-only URL');
  const shell=await page.locator('.offline-page').count();report.offlineNavigations=report.offlineNavigations||[];report.offlineNavigations.push({originalDocument:shell?'mission-shell':'full-lesson-document',uncachedNetworkBlocked:true});
  assert(await page.locator('.offline-page').isVisible(),'A transport-blocked navigation must use the cached mission shell');
 }
 try{
  report.pageErrors=[];assert(definitions[grade],`Unsupported GRADE: ${grade}`);const slug=process.env.SIM_SLUG||definitions[grade][0],id=process.env.SIM_LESSON_ID||definitions[grade][1];report.id=id;const url=new URL(`${grade}/${slug}/`,base).href;report.url=url;
  report.stage='online preparation';await launch(false);
  const response=await context.request.get(new URL(`${grade}/simulations.json`,base).href);assert(response.ok());const json=await response.text();report.publishedJSONSHA256=crypto.createHash('sha256').update(json).digest('hex');const lesson=JSON.parse(json).lessons.find(l=>l.id===id);assert(lesson);const learn=lesson.games.find(g=>g.mode==='learn');
  await page.goto(url,{waitUntil:'domcontentloaded'});await load();await root().getByText('Місії готові до роботи без інтернету й перезавантаження',{exact:false}).waitFor();
  await root().locator('select').selectOption(id);await root().locator('.sim-mode-card').filter({hasText:'Разом із підказками'}).getByRole('button').tap();
  await root().locator('.sim-choice').nth(learn.steps[0].choices.findIndex(c=>c.effect==='retry')).tap();await root().getByRole('button',{name:'Підказка',exact:true}).tap();assert((await root().innerText()).includes(learn.steps[0].hint));await root().getByRole('button',{name:'Пауза',exact:true}).tap();await shot('01-before-process-close');await close();
  report.stage='first offline process relaunch';await launch(true);await offlineNavigate(url);await load();assert.equal(await root().locator('select').inputValue(),id);await root().getByRole('button',{name:'Продовжити місію',exact:true}).tap();assert.match(await root().innerText(),/Місію призупинено/);await root().getByRole('button',{name:'Продовжити',exact:true}).tap();assert((await root().innerText()).includes(learn.steps[0].hint));report.pausedWrongHintAfterProcessRestart=true;await shot('02-offline-restored-hint');
  for(let step=0;step<2;step++){await root().locator('.sim-choice').nth(learn.steps[step].choices.findIndex(c=>c.effect==='advance')).tap();await root().getByRole('button',{name:step?'Завершити місію':'Наступний хід',exact:true}).tap();}
  assert.match(await root().locator('.sim-score').innerText(),/1 із 2/);await root().locator('textarea').fill('My persistent offline draft.');await root().getByRole('button',{name:'Зберегти репліку',exact:true}).tap();await shot('03-offline-complete-draft');await close();
  report.stage='second offline process relaunch';await launch(true);await offlineNavigate(url);await load();assert.equal(await root().locator('select').inputValue(),id);await root().getByRole('button',{name:'Переглянути результат',exact:true}).tap();assert.match(await root().locator('.sim-score').innerText(),/1 із 2/);assert.equal(await root().locator('textarea').inputValue(),'My persistent offline draft.');report.completedScoreDraftAfterSecondRestart=true;await root().locator('textarea').scrollIntoViewIfNeeded();await shot('04-second-process-restored-draft');
  const hasOfflineReturn=await page.locator('[data-offline-return]').count();
  if(hasOfflineReturn){await page.locator('[data-offline-return]').tap();await page.getByText('Зв’язок поки недоступний.',{exact:false}).waitFor();assert(await page.locator('.offline-page').isVisible());report.failedReturnKeptGame=true;}else report.offlineReturnNotApplicable='Browser returned the full lesson document, not the mission-only shell';
  report.stage='reconnection';transport.toggle(false);if(hasOfflineReturn)await Promise.all([page.waitForNavigation({waitUntil:'domcontentloaded'}),page.locator('[data-offline-return]').tap()]);else await page.reload({waitUntil:'domcontentloaded'});assert.equal(await page.locator('.offline-page').count(),0);await load();assert.equal(await root().locator('select').inputValue(),id);await root().getByRole('button',{name:'Переглянути результат',exact:true}).tap();assert.equal(await root().locator('textarea').inputValue(),'My persistent offline draft.');assert.match(await root().locator('.sim-score').innerText(),/1 із 2/);report.reconnectedFullLessonWithState=true;await shot('05-reconnected-full-lesson');
  assert.deepEqual(report.pageErrors,[]);await close();report.stage='complete';report.blockedProxyConnections=transport.denied();report.passed=true;console.log('PASS',grade,engine,output);
 }catch(error){report.error=error.stack||String(error);if(page&&!page.isClosed())try{await shot('failure')}catch(_){};if(context)try{await close()}catch(_){};console.error('FAIL',grade,engine,report.stage,report.error);}
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({base,startedWithFreshProfiles:true,reports},null,2));
}
await transport.close();console.log('Evidence:',output);if(reports.some(r=>!r.passed))process.exitCode=1;
})().catch(async error=>{console.error(error);await transport.close().catch(()=>{});process.exitCode=1});
