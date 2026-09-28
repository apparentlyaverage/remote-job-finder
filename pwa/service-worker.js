// Caches the app shell (not the job data — that's always fetched fresh from
// /api/jobs so you never see stale matches) so the PWA still opens if the
// local server is briefly unreachable.
const CACHE_NAME = "remote-job-finder-shell-v1";
const SHELL_FILES = ["/", "/index.html", "/styles.css", "/app.js", "/manifest.json", "/icons/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_FILES))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Never cache the live job data endpoint.
  if (url.pathname === "/api/jobs") return;

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
