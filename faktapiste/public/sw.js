// Faktapiste-sovelluksen service worker: sivut ja tyylit toimivat nopeasti, rajapinta haetaan aina verkosta.
const VERSIO = "fp-1";
const POHJA = ["/", "/tyyli.css", "/sovellus.js", "/ikoni-192.png", "/favicon.svg"];
self.addEventListener("install", e => { e.waitUntil(caches.open(VERSIO).then(c => c.addAll(POHJA)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== VERSIO).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin || u.pathname.startsWith("/api/")) return;
  // verkko ensin, välimuisti varalla (näin päivitykset näkyvät heti)
  e.respondWith(fetch(e.request).then(r => { const k = r.clone(); caches.open(VERSIO).then(c => c.put(e.request, k)); return r; }).catch(() => caches.match(e.request).then(r => r || caches.match("/"))));
});
