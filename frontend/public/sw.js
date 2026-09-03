// QUANTA PWA Service Worker for Push Alerts & Caching
const CACHE_NAME = 'quanta-v1';

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(['/', '/index.html', '/favicon.svg', '/quanta_logo.svg']);
    })
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/api/')) return; // Always network-first for API
  e.respondWith(
    caches.match(e.request).then((response) => {
      return response || fetch(e.request);
    })
  );
});
