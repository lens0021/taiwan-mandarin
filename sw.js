// Network first (revalidating past the browser HTTP cache), falling back to cache, so updates arrive when online and the app still opens offline.
// numbers/audio/*.mp3 (6 MB) is not precached; each sprite is cached the first time it plays.
const CACHE = "tm-v29";
const FILES = ["./", "./index.html", "./tone/", "./tone/index.html", "./routine/", "./routine/index.html", "./routine/clips.js", "./numbers/", "./numbers/index.html", "./numbers/clips.js", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES))); self.skipWaiting(); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))); self.clients.claim(); });
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request, { cache: "no-cache" }).then(r => { const c = r.clone(); caches.open(CACHE).then(ca => ca.put(e.request, c)); return r; }).catch(() => caches.match(e.request)));
});
