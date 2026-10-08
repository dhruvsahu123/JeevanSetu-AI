const CACHE_NAME = 'jeevansetu-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/frontend/index.html',
  '/frontend/customer-dashboard.html',
  '/frontend/emergency-card.html',
  '/frontend/hospital-dashboard.html',
  '/frontend/ambulance-tracking.html',
  '/frontend/login.html',
  '/frontend/css/style.css',
  '/frontend/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Let dynamic API requests pass straight through to network
  if (event.request.url.includes('/api/')) {
    return;
  }
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request);
    })
  );
});