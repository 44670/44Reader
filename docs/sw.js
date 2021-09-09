var CACHE_NAME = 'v20210322';

var urlsToCache = [
    '/favicon.ico',
	'/sw-loader.js',
    '/',
    '/localforage.js',
    '/decode.js',
    '/dark.css',
    '/icon.png',
	'/manifest.json',
];

self.addEventListener('install', function (event) {
    // Perform install steps
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            }).then(()=>{
				console.log('Cache downloaded')
				self.skipWaiting()
			})
    );
});


self.addEventListener('fetch', function (event) {
    event.respondWith(
        caches.match(event.request)
            .then(function (response) {
                // Cache hit - return response
                if (response) {
                    return response;
                }
                console.log('cache miss', event.request.url)
                return fetch(event.request);
            })
    );
});


self.addEventListener('activate', function (event) {
    console.log('activated, remove unused cache...')
    var cacheAllowlist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(function (cacheNames) {
            return Promise.all(
                cacheNames.map(function (cacheName) {
                    if (cacheAllowlist.indexOf(cacheName) === -1) {
						console.log(cacheName)
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
	clients.matchAll({includeUncontrolled:true,type:'window'}).then((arr) => {
		for (client of arr) {
			client.postMessage({type:'updated'})
		}
	})
});
