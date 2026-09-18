const VERSION="1.0.3";
const CORE_CACHE=`jolly-core-${VERSION}`;
const ASSET_CACHE=`jolly-assets-${VERSION}`;
const CORE=['./','index.html','styles.css','app.js','data/cards.js','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','assets-manifest.json'];
let cacheAllPromise=null;

async function notify(message){
  const clientsList=await self.clients.matchAll({type:'window',includeUncontrolled:true});
  clientsList.forEach(client=>client.postMessage(message));
}
async function cacheAll(){
  const manifestResponse=await fetch('assets-manifest.json',{cache:'no-store'});
  const manifest=await manifestResponse.json();
  const cache=await caches.open(ASSET_CACHE);
  const urls=manifest.assets.map(item=>item.url).filter(url=>!CORE.includes(url));
  let done=0;
  for(let i=0;i<urls.length;i+=8){
    await Promise.all(urls.slice(i,i+8).map(async url=>{
      if(!(await cache.match(url))){
        const response=await fetch(url,{cache:'no-store'});
        if(!response.ok)throw new Error(`Could not cache ${url}`);
        await cache.put(url,response);
      }
      done+=1;
    }));
    await notify({type:'CACHE_PROGRESS',done,total:urls.length});
  }
  const oldAssets=(await caches.keys()).filter(key=>key.startsWith('jolly-assets-')&&key!==ASSET_CACHE);
  await Promise.all(oldAssets.map(key=>caches.delete(key)));
  await notify({type:'CACHE_COMPLETE',version:VERSION,total:urls.length});
}
function ensureCacheAll(){
  if(!cacheAllPromise)cacheAllPromise=cacheAll().finally(()=>{cacheAllPromise=null;});
  return cacheAllPromise;
}
self.addEventListener('install',event=>event.waitUntil(
  caches.open(CORE_CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting())
));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
  const keys=await caches.keys();
  const oldCore=keys.filter(key=>key.startsWith('jolly-core-')&&key!==CORE_CACHE);
  const isUpdate=oldCore.length>0||keys.some(key=>key.startsWith('jolly-assets-')&&key!==ASSET_CACHE);
  await Promise.all(oldCore.map(key=>caches.delete(key)));
  await self.clients.claim();
  if(isUpdate)await notify({type:'UPDATE_READY',version:VERSION});
  ensureCacheAll().catch(()=>notify({type:'CACHE_ERROR'}));
})()));
self.addEventListener('message',event=>{
  if(event.data?.type==='CACHE_ALL')event.waitUntil(ensureCacheAll().catch(()=>notify({type:'CACHE_ERROR'})));
});
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;
  if(event.request.mode==='navigate'){
    event.respondWith(fetch(event.request).then(response=>{
      caches.open(CORE_CACHE).then(cache=>cache.put('index.html',response.clone()));
      return response;
    }).catch(()=>caches.match('index.html')));
    return;
  }
  event.respondWith((async()=>{
    const core=await caches.open(CORE_CACHE);
    const assets=await caches.open(ASSET_CACHE);
    const current=await core.match(event.request)||await assets.match(event.request);
    if(current)return current;
    try{
      const response=await fetch(event.request);
      if(response.ok)await assets.put(event.request,response.clone());
      return response;
    }catch(error){
      const keys=await caches.keys();
      for(const key of keys.filter(name=>name.startsWith('jolly-assets-')&&name!==ASSET_CACHE)){
        const fallback=await (await caches.open(key)).match(event.request);
        if(fallback)return fallback;
      }
      throw error;
    }
  })());
});
