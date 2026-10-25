/* Babatsa · aparición escalonada de bloques al hacer scroll y contador de cifras.
   No se anima en el constructor del sitio (el contenido debe verse siempre para editarlo),
   ni si el visitante pidió reducir movimiento. Sin JS el contenido se ve normal. */
(function () {
    "use strict";

    // Bloques sueltos que aparecen solos
    var SINGLE = [
        ".bbt-sec .bbt-eyebrow", ".bbt-sec .bbt-h2", ".bbt-apps .bbt-eyebrow", ".bbt-apps .bbt-h2",
        ".bbt-lead", ".bbt-serv-photo", ".bbt-map", ".bbt-apps-foot", ".bbt-routes", ".bbt-brands-note",
        ".bbt-about-photo", ".bbt-about-quote", ".bbt-about-vct", ".bbt-about-close .bbt-ctas",
        ".bbt-svc-quote", ".bbt-svc-n", ".bbt-svc-sub",
        // Cada hito / línea aparece al llegar a él, sin retraso escalonado
        ".bbt-tl-item", ".bbt-line",
    ].join(",");
    // Contenedores cuyos hijos aparecen uno tras otro
    var GROUPS = ".bbt-apps-grid, .bbt-serv-list, .bbt-stats, .bbt-brands, .bbt-pillars, .bbt-steps, .bbt-checks, .bbt-svc-pair";
    var STEP = 70; // ms entre hijos
    var MAX_DELAY = 560;

    function countUp(el) {
        var target = parseInt(el.textContent, 10);
        // Los años (1968) no se cuentan: se leen mejor fijos
        if (isNaN(target) || target > 999 || String(target) !== el.textContent.trim()) {
            return;
        }
        var start = null;
        var duration = 900;
        function frame(ts) {
            if (start === null) {
                start = ts;
            }
            var p = Math.min((ts - start) / duration, 1);
            el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
            if (p < 1) {
                window.requestAnimationFrame(frame);
            }
        }
        el.textContent = "0";
        window.requestAnimationFrame(frame);
    }

    // La línea del tiempo se va llenando conforme se hace scroll
    function timelineProgress() {
        var timelines = document.querySelectorAll(".bbt-tl");
        if (!timelines.length) {
            return;
        }
        var ticking = false;
        function update() {
            ticking = false;
            var anchor = window.innerHeight * 0.6;
            timelines.forEach(function (tl) {
                var rect = tl.getBoundingClientRect();
                var p = Math.max(0, Math.min(1, (anchor - rect.top) / rect.height));
                tl.style.setProperty("--bbt-tl-p", p.toFixed(3));
            });
        }
        function request() {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(update);
            }
        }
        window.addEventListener("scroll", request, { passive: true });
        window.addEventListener("resize", request);
        update();
    }

    function init() {
        var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (reduce || !("IntersectionObserver" in window) || window.frameElement ||
            document.body.classList.contains("editor_enable")) {
            return;
        }
        timelineProgress();
        var items = [];
        document.querySelectorAll(SINGLE).forEach(function (el) {
            items.push(el);
        });
        document.querySelectorAll(GROUPS).forEach(function (group) {
            Array.prototype.forEach.call(group.children, function (child, i) {
                child.style.setProperty("--bbt-d", Math.min(i * STEP, MAX_DELAY) + "ms");
                items.push(child);
            });
        });
        if (!items.length) {
            return;
        }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                var el = entry.target;
                el.classList.add("is-in");
                io.unobserve(el);
                var num = el.matches(".bbt-stat") ? el.querySelector("strong") : null;
                if (num) {
                    countUp(num);
                }
            });
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });

        items.forEach(function (el) {
            el.classList.add("bbt-rv");
            io.observe(el);
        });
        document.documentElement.classList.add("bbt-js");
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
