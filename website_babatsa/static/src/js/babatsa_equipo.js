/* Babatsa · "¿Qué lleva tu equipo?" (/tu-equipo, views/website_tu_equipo_templates.xml).
   Pestañas por equipo; al tocar una parte (en el dibujo o en la lista) se resalta en el dibujo,
   se atenúa lo demás y se abre su detalle. Sin JS (o en el constructor) todo se ve abierto. */
(function () {
    "use strict";

    function setupEquipo(eq) {
        var items = eq.querySelectorAll(".bbt-eq-part");
        var parts = eq.querySelectorAll(".bbt-eq-svg [data-part]:not(.bbt-eq-hot)");
        var hots = eq.querySelectorAll(".bbt-eq-hot");
        var told = false;

        function activate(key, scroll) {
            if (scroll && !told) {
                told = true;
                var guide = document.querySelector(".bbt-eq-guide .bbt-guide-text");
                if (guide) {
                    guide.textContent = "¿Ya sabes cuál es? Dale en «Mídela y pídela» y la mandas a tu sucursal con sus medidas.";
                    guide.parentNode.classList.add("is-talking");
                }
            }
            items.forEach(function (li) {
                var on = li.getAttribute("data-part") === key;
                li.classList.toggle("is-on", on);
                li.querySelector(".bbt-eq-item").setAttribute("aria-expanded", on ? "true" : "false");
                if (on && scroll && window.matchMedia("(max-width: 991px)").matches) {
                    li.scrollIntoView({ block: "nearest", behavior: "smooth" });
                }
            });
            parts.forEach(function (g) {
                var on = g.getAttribute("data-part") === key;
                g.classList.toggle("is-on", on);
                g.classList.toggle("is-dim", !on);
            });
            hots.forEach(function (h) {
                h.classList.toggle("is-on", h.getAttribute("data-part") === key);
            });
        }

        items.forEach(function (li) {
            li.querySelector(".bbt-eq-item").addEventListener("click", function () {
                activate(li.getAttribute("data-part"), false);
            });
        });
        hots.forEach(function (h) {
            h.addEventListener("click", function () {
                activate(h.getAttribute("data-part"), true);
            });
            h.addEventListener("keydown", function (ev) {
                if (ev.key === "Enter" || ev.key === " ") {
                    ev.preventDefault();
                    activate(h.getAttribute("data-part"), true);
                }
            });
        });
        if (items.length) {
            activate(items[0].getAttribute("data-part"), false);
        }
    }

    function init() {
        window.bbtMount(document.querySelector(".bbt-eq-sec"), setup);
    }

    function setup(root) {
        root.classList.add("is-ready");
        var tabs = root.querySelectorAll(".bbt-eq-tab");
        var equipos = root.querySelectorAll(".bbt-eq");
        equipos.forEach(setupEquipo);

        function show(name) {
            tabs.forEach(function (t) {
                var on = t.getAttribute("data-eq") === name;
                t.classList.toggle("is-on", on);
                t.setAttribute("aria-selected", on ? "true" : "false");
            });
            equipos.forEach(function (eq) {
                eq.classList.toggle("is-on", eq.getAttribute("data-eq") === name);
            });
        }
        tabs.forEach(function (t) {
            t.addEventListener("click", function () {
                show(t.getAttribute("data-eq"));
            });
        });
        show(tabs.length ? tabs[0].getAttribute("data-eq") : "");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
