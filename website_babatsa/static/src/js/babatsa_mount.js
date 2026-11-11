/* Babatsa · arranque seguro de las herramientas del sitio (Tu pieza, Tu equipo, mapa, etc.).
   Con sesión iniciada, Odoo 19 muestra el sitio dentro de un marco y, al pulsar "Editar", activa el
   constructor sobre la misma página (agrega body.editor_enable, sin recargar). Lo que el JS haya
   cambiado en el HTML se guardaría en la plantilla, así que bbtMount guarda una copia limpia del
   bloque antes de montarlo y la regresa en cuanto empieza la edición. */
(function () {
    "use strict";

    function editing() {
        return document.body.classList.contains("editor_enable");
    }

    var restores = [];
    var observer = null;

    function watch() {
        if (observer) {
            return;
        }
        observer = new MutationObserver(function () {
            if (!editing()) {
                return;
            }
            observer.disconnect();
            restores.forEach(function (restore) {
                restore();
            });
            restores = [];
        });
        observer.observe(document.body, { attributes: true, attributeFilter: ["class"] });
    }

    window.bbtMount = function (el, init) {
        if (!el || editing()) {
            return;
        }
        var pristine = el.cloneNode(true);
        init(el);
        restores.push(function () {
            if (el.isConnected) {
                el.replaceWith(pristine);
            }
        });
        watch();
    };
})();
