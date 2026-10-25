const CACHE_NAME='qvr-production-20261026-v1';
const APP_SHELL=['./','./index.html','./styles.css','./app.js','./data/seed.js','./assets/icon.svg','./manifest.webmanifest'];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE_NAME).then(cache=>cache.addAll(APP_SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 const req=event.request;if(req.method!=='GET')return;
 const url=new URL(req.url);if(url.origin!==self.location.origin)return;
 const isDynamic=url.pathname.includes('/data/')&&url.pathname.endsWith('.json');
 const isCode=['/app.js','/styles.css','/index.html','/'].some(x=>url.pathname.endsWith(x));
 if(isDynamic||isCode){
  event.respondWith(fetch(req,{cache:'no-store'}).then(response=>{
   if(response.ok&&isCode){const copy=response.clone();caches.open(CACHE_NAME).then(c=>c.put(req,copy)).catch(()=>{});}
   return response;
  }).catch(()=>caches.match(req).then(cached=>cached||Response.error())));
  return;
 }
 event.respondWith(caches.match(req).then(cached=>cached||fetch(req)));
});
