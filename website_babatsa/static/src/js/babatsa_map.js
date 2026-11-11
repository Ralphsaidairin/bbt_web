/* Babatsa · mapa de sucursales (/sucursales, views/website_sucursales_map_templates.xml).
   Al tocar una ciudad se resalta su ruta desde la matriz y se ven sus sucursales a la derecha.
   Cuenta cuántas están abiertas ahora con el estado que pone babatsa_open.js (se carga antes). */
(function () {
    "use strict";

    function init() {
        window.bbtMount(document.querySelector(".bbt-nmap-sec"), setup);
    }

    function setup(sec) {
        sec.classList.add("is-ready");
        var pins = sec.querySelectorAll(".bbt-nmap-pin");
        var panels = sec.querySelectorAll(".bbt-nmap-city");
        var routes = sec.querySelectorAll(".nm-route");
        var live = sec.querySelector(".bbt-nmap-live");

        function select(key) {
            pins.forEach(function (p) {
                var on = p.getAttribute("data-city") === key;
                p.classList.toggle("is-on", on);
                p.setAttribute("aria-pressed", on ? "true" : "false");
            });
            panels.forEach(function (p) {
                p.classList.toggle("is-on", p.getAttribute("data-city") === key);
            });
            routes.forEach(function (r) {
                r.classList.toggle("is-on", r.getAttribute("data-city") === key);
            });
        }

        // Ciudades con al menos una sucursal abierta y contador general
        function refreshOpen() {
            var open = 0;
            panels.forEach(function (panel) {
                var n = panel.querySelectorAll('.bbt-open[data-state="open"], .bbt-open[data-state="soon"]').length;
                open += n;
                var pin = sec.querySelector('.bbt-nmap-pin[data-city="' + panel.getAttribute("data-city") + '"]');
                if (pin) {
                    pin.classList.toggle("has-open", n > 0);
                }
            });
            if (live && sec.querySelector(".bbt-open[data-state]")) {
                live.querySelector("b").textContent = open;
                live.setAttribute("data-state", open ? "open" : "closed");
                live.hidden = false;
            }
        }

        pins.forEach(function (p) {
            p.addEventListener("click", function () {
                select(p.getAttribute("data-city"));
            });
            p.addEventListener("keydown", function (ev) {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    select(p.getAttribute("data-city"));
                }
            });
        });
        var hub = sec.querySelector(".bbt-nmap-pin.is-hub") || pins[0];
        if (hub) {
            select(hub.getAttribute("data-city"));
        }
        refreshOpen();
        window.setInterval(refreshOpen, 60000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
