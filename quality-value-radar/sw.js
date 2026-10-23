const CACHE_NAME='qvr-v2-intrinsic-20261023';
const APP_SHELL=['./','./index.html','./styles.css','./app.js','./data/seed.js','./assets/icon.svg','./manifest.webmanifest'];
self.addEventListener('install',ev=>{ev.waitUntil(caches.open(CACHE_NAME).then(c=>c.addAll(APP_SHELL)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',ev=>{ev.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE_NAME).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',ev=>{const req=ev.request;if(req.method!=='GET')return;const url=new URL(req.url);if(url.origin!==location.origin)return;
if(url.pathname.endsWith('/data/quotes.json')||url.pathname.endsWith('/data/intrinsic.json')||url.pathname.endsWith('/app.js')||url.pathname.endsWith('/index.html')){ev.respondWith(fetch(req,{cache:'no-store'}).catch(()=>caches.match(req)));return;}
ev.respondWith(caches.match(req).then(m=>m||fetch(req).then(r=>r)));
});
