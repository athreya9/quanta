// QUANTA PWA Service Worker (Network First Strategy)
const CACHE_NAME = 'quanta-v2';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/') || e.request.url.includes('/extension/')) return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
