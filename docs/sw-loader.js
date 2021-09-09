if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
        navigator.serviceWorker.register('/sw.js').then(function (registration) {
            // Registration was successful
            console.log('ServiceWorker registration successful with scope: ', registration.scope);
            navigator.serviceWorker.getRegistrations().then((registrations) => {
                for (var r of registrations) {
                    if (r.scope.split('/', 4)[3] != '') {
                        console.log('removing outdated service worker', r)
                        r.unregister()
                    }
                }
            })
        }, function (err) {
            // registration failed :(
            console.log('ServiceWorker registration failed: ', err);
        });
    });
}
