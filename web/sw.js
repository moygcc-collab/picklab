// Service worker: permite instalar PickLab como app
// Siempre intenta bajar lo mas nuevo; si no hay internet usa lo guardado
var CACHE = "picklab-v2";
var ARCHIVOS = ["./", "index.html", "estilos.css", "app.js", "picks.js", "historial.js", "manifest.json", "icono-192.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ARCHIVOS); }));
  self.skipWaiting();
});

self.addEventListener("activate", function (e) {
  e.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request).then(function (respuesta) {
      var copia = respuesta.clone();
      caches.open(CACHE).then(function (c) { c.put(e.request, copia); });
      return respuesta;
    }).catch(function () {
      return caches.match(e.request);
    })
  );
});
