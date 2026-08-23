/* GrowthOS service worker — caches the app shell only. */
const CACHE = "growthos-shell-v1";
const SHELL = ["/", "/manifest.webmanifest", "/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).catch(() => {}),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
      ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  // Never cache API responses — commercial data must stay fresh and real.
  if (event.request.url.includes("/api/")) return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request)),
  );
});
