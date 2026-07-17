/* ═══════════════════════════════════════════════════
   OVERDRIVE SERVICE WORKER — PWA Cache & Offline
   Cache version: bump when static assets change
═══════════════════════════════════════════════════ */
const CACHE = 'overdrive-v1';
const STATIC = [
  '/static/css/overdrive.css',
  '/static/images/overdrive_logo.png',
  '/static/images/default_avatar.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,800&display=swap'
];

// Install: pre-cache static shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC).catch(() => {}))
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch strategy:
// - Static assets: cache-first
// - API/HTML: network-first with cache fallback
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Skip non-GET, chrome-extension, and cross-origin non-CDN requests
  if (e.request.method !== 'GET') return;
  if (url.protocol === 'chrome-extension:') return;

  const isStatic = url.pathname.startsWith('/static/') ||
    url.hostname.includes('cdn.jsdelivr.net') ||
    url.hostname.includes('cdnjs.cloudflare.com') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('fonts.googleapis.com');

  const isAPI = url.pathname.startsWith('/notifications') ||
    url.pathname.startsWith('/ai/') ||
    url.pathname.endsWith('/poll');

  if (isStatic) {
    // Cache first
    e.respondWith(
      caches.match(e.request).then(cached => cached ||
        fetch(e.request).then(resp => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(CACHE).then(c => c.put(e.request, clone));
          }
          return resp;
        })
      )
    );
  } else if (isAPI) {
    // Network only for real-time endpoints
    return;
  } else {
    // Network first, cache fallback for HTML pages
    e.respondWith(
      fetch(e.request).then(resp => {
        if (resp.ok && e.request.destination === 'document') {
          const clone = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return resp;
      }).catch(() => caches.match(e.request))
    );
  }
});

// Handle push notifications (if ever enabled)
self.addEventListener('push', e => {
  const data = e.data ? e.data.json() : { title: 'Overdrive', body: 'You have a new notification.' };
  e.waitUntil(
    self.registration.showNotification(data.title || 'Overdrive', {
      body: data.body || '',
      icon: '/static/images/overdrive_logo.png',
      badge: '/static/images/overdrive_logo.png',
      tag: 'overdrive-notif',
      renotify: true,
      data: { url: data.url || '/' }
    })
  );
});

self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(clients.openWindow(e.notification.data?.url || '/'));
});
