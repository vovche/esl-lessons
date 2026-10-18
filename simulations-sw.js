/* A small, explicit offline cache for student missions, not whole lessons. */
'use strict';
// Bump this cache version whenever the offline shell/runtime changes. Install writes
// a separate bundle; an interrupted update must never overwrite the active bundle.
const CACHE_NAME = 'esl-missions-v2';
const PREVIOUS_CACHES = ['esl-missions-v1'];
const SITE = new URL('./', self.registration.scope);
const CORE_PATHS = ['offline-simulations.html', 'assets/offline-simulations.js', 'assets/lesson-simulations.js', 'assets/lesson-simulations.css', 'assets/lesson-theme.css'];
const CORE = CORE_PATHS.map(path => new URL(path, SITE).href);
const GRADES = new Set(['6', '7', '9']);
function gradeURL(grade) { return new URL(grade + '/simulations.json', SITE).href; }
async function network(request, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 4000);
  try { return await fetch(request, {...options, signal: controller.signal}); }
  finally { clearTimeout(timer); }
}
function validData(data, grade) {
  return data && data.version === 1 && String(data.grade) === grade && Array.isArray(data.lessons) && data.lessons.length > 0 &&
    data.lessons.every(lesson => Array.isArray(lesson.slugs) && lesson.slugs.every(slug => typeof slug === 'string') && Array.isArray(lesson.games) && lesson.games.length === 2);
}
async function storeCore(cache) {
  for (const url of CORE) {
    const response = await network(url, {cache: 'reload'});
    if (!response.ok) throw new Error('Mission files unavailable');
    await cache.put(url, response);
  }
}
self.addEventListener('install', event => {
  event.waitUntil((async () => { await storeCore(await caches.open(CACHE_NAME)); await self.skipWaiting(); })());
});
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    // Retain the previous bundle for still-open tabs and as a migration fallback.
    for (const grade of GRADES) await storedGrade(grade);
    await self.clients.claim();
  })());
});
async function storedGrade(grade) {
  const current = await caches.open(CACHE_NAME);
  const names = await caches.keys();
  for (const name of [CACHE_NAME, ...PREVIOUS_CACHES]) {
    if (!names.includes(name)) continue;
    const response = await (await caches.open(name)).match(gradeURL(grade));
    if (!response) continue;
    try {
      if (!validData(await response.clone().json(), grade)) continue;
      if (name !== CACHE_NAME) {
        try { await current.put(gradeURL(grade), response.clone()); } catch (_) { /* The previous cache remains usable. */ }
      }
      return response;
    } catch (_) { /* Ignore invalid old data and try the next cache. */ }
  }
}
self.addEventListener('message', event => {
  const data = event.data;
  if (!data || data.type !== 'PREPARE_MISSIONS' || !GRADES.has(String(data.grade))) return;
  const port = event.ports && event.ports[0];
  event.waitUntil((async () => {
    try {
      const grade = String(data.grade), cache = await caches.open(CACHE_NAME);
      if (!(await Promise.all(CORE.map(url => cache.match(url)))).every(Boolean)) await storeCore(cache);
      try {
        const response = await network(gradeURL(grade), {cache: 'reload'});
        if (!response.ok || !validData(await response.clone().json(), grade)) throw new Error('Mission data unavailable');
        await cache.put(gradeURL(grade), response);
      } catch (error) {
        const existing = await storedGrade(grade);
        if (!existing || !validData(await existing.json(), grade)) throw error;
      }
      if (!(await storedGrade(grade)) || !(await Promise.all(CORE.map(url => cache.match(url)))).every(Boolean)) throw new Error('Mission cache incomplete');
      if (port) port.postMessage({ok: true});
    } catch (_) { if (port) port.postMessage({ok: false}); }
  })());
});
async function cachedResource(request, grade) {
  const cache = await caches.open(CACHE_NAME);
  // Core files belong to one installed release. Do not mix a later partial
  // deployment into the active bundle via network-first resource requests.
  if (!grade) { const pinned = await cache.match(request.url); if (pinned) return pinned; }
  try {
    const response = await network(request);
    if (!response.ok || (grade && !validData(await response.clone().json(), grade))) throw new Error('Mission resource unavailable');
    try { await cache.put(request.url, response.clone()); } catch (_) { /* Online use still works if cache storage is full. */ }
    return response;
  } catch (error) { const cached = grade ? await storedGrade(grade) : await cache.match(request.url); if (cached) return cached; throw error; }
}
async function navigation(request) {
  const url = new URL(request.url);
  if (!url.pathname.startsWith(SITE.pathname)) return fetch(request);
  const relative = url.pathname.slice(SITE.pathname.length);
  const match = /^(6|7|9)\/([^/]+)\/(?:index\.html)?$/.exec(relative);
  if (!match) return fetch(request);
  try {
    const response = await network(request);
    if (!response.ok) throw new Error('Lesson unavailable');
    return response;
  } catch (error) {
    const cache = await caches.open(CACHE_NAME), stored = await storedGrade(match[1]);
    if (!stored) throw error;
    const data = await stored.json();
    if (!validData(data, match[1]) || !data.lessons.some(lesson => lesson.slugs.includes(match[2]))) throw error;
    const template = await cache.match(new URL('offline-simulations.html', SITE).href);
    if (!template) throw error;
    const base = SITE.pathname.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
    return new Response((await template.text()).replace('<base href="./">', '<base href="' + base + '">'), {headers: {'Content-Type': 'text/html; charset=utf-8'}});
  }
}
self.addEventListener('fetch', event => {
  const request = event.request, url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== SITE.origin) return;
  if (request.mode === 'navigate') { event.respondWith(navigation(request)); return; }
  const grade = [...GRADES].find(value => url.href === gradeURL(value));
  if (CORE.includes(url.href) || grade) event.respondWith(cachedResource(request, grade));
});
