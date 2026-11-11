/* Babatsa · views/website_mostrador_templates.xml
   - Video del fundador: el reproductor (YouTube, Vimeo, Facebook o el archivo subido) se carga hasta que le dan play.
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
        document.querySelectorAll(".bbt-founder-media").forEach(function (media) {
            window.bbtMount(media, function () {
                var btn = media.querySelector(".bbt-founder-play");
                var preview = media.querySelector(".bbt-founder-preview");
                if (preview) {
                    setupPreview(media, preview);
                }
                if (btn) {
                    playOnClick(media, btn, preview);
                }
            });
        });
    }

    // Vista previa en gris y sin sonido: solo corre mientras la sección está a la vista
    // (y no se descarga si el visitante pidió reducir movimiento o ahorrar datos).
    function setupPreview(media, video) {
        video.addEventListener("loadedmetadata", function () {
            media.classList.toggle("bbt-founder-media--vertical", video.videoHeight > video.videoWidth);
        });
        var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        var saveData = navigator.connection && navigator.connection.saveData;
        if (reduce || saveData || !("IntersectionObserver" in window)) {
            video.preload = "metadata";
            video.src = video.getAttribute("data-src") + "#t=1";
            return;
        }
        new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (media.classList.contains("is-playing")) {
                    return;
                }
                if (entry.isIntersecting) {
                    if (!video.src) {
                        video.src = video.getAttribute("data-src");
                    }
                    video.play().catch(function () {});
                } else if (video.src) {
                    video.pause();
                }
            });
        }, { rootMargin: "200px 0px" }).observe(media);
    }

    function playOnClick(media, btn, preview) {
        btn.addEventListener("click", function () {
            if (preview) {
                // El mismo video pasa a color, desde el inicio y con sonido
                if (!preview.src) {
                    preview.src = preview.getAttribute("data-src");
                }
                preview.muted = false;
                preview.loop = false;
                preview.currentTime = 0;
                preview.controls = true;
                preview.removeAttribute("aria-hidden");
                media.classList.add("is-playing");
                btn.remove();
                preview.play().catch(function () {});
                return;
            }
            var iframe = document.createElement("iframe");
            iframe.src = btn.getAttribute("data-embed");
            iframe.title = "Historia de Babatsa contada por su fundador";
            iframe.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
            iframe.allowFullscreen = true;
            iframe.className = "bbt-founder-frame";
            btn.replaceWith(iframe);
        });
    }

    function setupDictionary() {
        window.bbtMount(document.querySelector(".bbt-dic"), setupDictionaryIn);
    }

    function setupDictionaryIn(sec) {
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
        setupVideo();
        setupDictionary();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
