// Regression: an early touch must not target a button without its runtime listener.
const {chromium, webkit} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.SIM_BASE_URL || 'http://127.0.0.1:8876/';
(async () => {
  for (const engine of [chromium, webkit]) {
    const browser = await engine.launch();
    try {
      const context = await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block'});
      let release;
      const runtimeGate = new Promise(resolve => { release = resolve; });
      await context.route(new URL('assets/lesson-simulations.js', base).href, async route => { await runtimeGate; await route.continue(); });
      const url = new URL('6/sb-hello/', base).href;
      await context.route(url, route => route.fulfill({contentType:'text/html',body:fs.readFileSync('offline-simulations.html','utf8').replace('<base href="./">',`<base href="${base}">`)}));
      const page = await context.newPage();
      await page.goto(url,{waitUntil:'domcontentloaded'});
      const load = page.locator('[data-sim-load]');
      await load.waitFor({state:'visible'});
      assert(await load.isDisabled(), 'The loading control must be disabled before runtime is ready');
      assert.equal(await load.innerText(),'Готую ігри…');
      release();
      await page.waitForFunction(() => !document.querySelector('[data-sim-load]').disabled);
      await load.tap();
      await page.locator('.sim-select').waitFor();
      console.log('PASS delayed offline bootstrap',engine.name());
    } finally { await browser.close(); }
  }
})().catch(error => { console.error(error); process.exit(1); });
