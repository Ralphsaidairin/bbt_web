/* Babatsa · views/website_mostrador_templates.xml
   - Video del fundador: el reproductor (YouTube, Vimeo o Facebook) se carga hasta que le dan play.
   - "¿Cómo le dices tú?": busca lo que escribe el cliente entre los nombres de mostrador de cada
     término (sin acentos ni mayúsculas) y muestra hasta 3 coincidencias.
   En el constructor no se monta nada: todo queda visible para editar los textos. */
(function () {
    "use strict";

    var MAX_RESULTS = 3;
    var EXAMPLES = ["perica", "alemite", "rondana", "chicote", "pija", "estopero"];

    function norm(text) {
        return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
    }

    function setupVideo() {
        document.querySelectorAll(".bbt-founder-play[data-embed]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var iframe = document.createElement("iframe");
                iframe.src = btn.getAttribute("data-embed");
                iframe.title = "Historia de Babatsa contada por su fundador";
                iframe.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
                iframe.allowFullscreen = true;
                iframe.className = "bbt-founder-frame";
                btn.replaceWith(iframe);
            });
        });
    }

    function setupDictionary() {
        var sec = document.querySelector(".bbt-dic");
        if (!sec) {
            return;
        }
        sec.classList.add("is-ready");
        var input = sec.querySelector(".bbt-dic-input");
        var none = sec.querySelector(".bbt-dic-none");
        var items = Array.prototype.map.call(sec.querySelectorAll(".bbt-dic-item"), function (li) {
            return { el: li, aliases: li.getAttribute("data-aliases").split("|").map(norm) };
        });

        function score(item, q) {
            var best = 0;
            item.aliases.forEach(function (a) {
                if (a === q) {
                    best = Math.max(best, 3);
                } else if (a.indexOf(q) === 0 || q.indexOf(a) !== -1) {
                    best = Math.max(best, 2);
                } else if (q.length > 2 && a.indexOf(q) !== -1) {
                    best = Math.max(best, 1);
                }
            });
            return best;
        }

        function search() {
            var q = norm(input.value);
            var shown = [];
            if (!q) {
                shown = [items[0]];
            } else {
                shown = items.map(function (it) {
                    return { it: it, s: score(it, q) };
                }).filter(function (r) {
                    return r.s > 0;
                }).sort(function (a, b) {
                    return b.s - a.s;
                }).slice(0, MAX_RESULTS).map(function (r) {
                    return r.it;
                });
            }
            items.forEach(function (it) {
                var on = shown.indexOf(it) !== -1;
                it.el.hidden = !on;
                it.el.classList.toggle("is-new", on && !!q);
            });
            none.hidden = shown.length > 0;
            sec.classList.toggle("is-example", !q);
        }

        input.addEventListener("input", search);
        sec.querySelectorAll(".bbt-dic-chip").forEach(function (chip) {
            chip.addEventListener("click", function () {
                input.value = chip.getAttribute("data-q");
                search();
                input.focus();
            });
        });
        search();

        // El ejemplo del campo va cambiando mientras está vacío
        if (!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches)) {
            var i = 0;
            window.setInterval(function () {
                if (document.activeElement !== input && !input.value) {
                    i = (i + 1) % EXAMPLES.length;
                    input.placeholder = "Ej. " + EXAMPLES[i];
                }
            }, 2600);
        }
    }

    function init() {
        if (window.frameElement || document.body.classList.contains("editor_enable")) {
            return;
        }
        setupVideo();
        setupDictionary();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
