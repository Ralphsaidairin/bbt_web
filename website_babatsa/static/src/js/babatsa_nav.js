/* Babatsa · encabezado en cápsula.
   - Se compacta al bajar y se esconde al seguir bajando; reaparece al subir.
   - En celular, el botón abre un panel que sube desde abajo (Esc, fondo o enlace lo cierran). */
(function () {
    "use strict";

    var HIDE_AFTER = 480; // px de scroll antes de permitir que se esconda

    function init() {
        var header = document.querySelector("header.bbt-nav-wrap");
        if (!header) {
            return;
        }
        var toggle = header.querySelector(".bbt-nav-toggle");
        var panel = header.querySelector(".bbt-nav-panel");
        var backdrop = header.querySelector(".bbt-nav-backdrop");
        // Dentro del constructor no se esconde: estorbaría al editar
        var inEditor = !!window.frameElement;

        // ---------- Scroll ----------
        var lastY = window.scrollY;
        var ticking = false;
        function onScroll() {
            ticking = false;
            var y = window.scrollY;
            header.classList.toggle("is-scrolled", y > 12);
            if (!inEditor && !header.classList.contains("is-open")) {
                var down = y > lastY + 4;
                var up = y < lastY - 4;
                if (down && y > HIDE_AFTER && !header.contains(document.activeElement)) {
                    header.classList.add("is-hidden");
                } else if (up || y <= HIDE_AFTER) {
                    header.classList.remove("is-hidden");
                }
            }
            lastY = y;
        }
        window.addEventListener("scroll", function () {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(onScroll);
            }
        }, { passive: true });
        // Si alguien navega con teclado hasta el menú, que se vea
        header.addEventListener("focusin", function () {
            header.classList.remove("is-hidden");
        });
        onScroll();

        // ---------- Panel de celular ----------
        if (!toggle || !panel) {
            return;
        }
        var closeTimer = null;
        function open() {
            window.clearTimeout(closeTimer);
            panel.hidden = false;
            backdrop.hidden = false;
            // Un frame para que la transición arranque desde el estado cerrado
            window.requestAnimationFrame(function () {
                header.classList.add("is-open");
            });
            toggle.setAttribute("aria-expanded", "true");
            document.documentElement.classList.add("bbt-nav-lock");
            var first = panel.querySelector("a");
            if (first) {
                first.focus({ preventScroll: true });
            }
        }
        function close(returnFocus) {
            header.classList.remove("is-open");
            toggle.setAttribute("aria-expanded", "false");
            document.documentElement.classList.remove("bbt-nav-lock");
            closeTimer = window.setTimeout(function () {
                panel.hidden = true;
                backdrop.hidden = true;
            }, 320);
            if (returnFocus) {
                toggle.focus();
            }
        }
        toggle.addEventListener("click", function () {
            if (header.classList.contains("is-open")) {
                close(false);
            } else {
                open();
            }
        });
        backdrop.addEventListener("click", function () {
            close(true);
        });
        panel.addEventListener("click", function (ev) {
            if (ev.target.closest("a")) {
                close(false);
            }
        });
        document.addEventListener("keydown", function (ev) {
            if (!header.classList.contains("is-open")) {
                return;
            }
            if (ev.key === "Escape") {
                close(true);
            } else if (ev.key === "Tab") {
                // Mantener el foco dentro del panel
                var focusables = panel.querySelectorAll("a, button");
                var first = focusables[0];
                var last = focusables[focusables.length - 1];
                if (ev.shiftKey && document.activeElement === first) {
                    ev.preventDefault();
                    last.focus();
                } else if (!ev.shiftKey && document.activeElement === last) {
                    ev.preventDefault();
                    first.focus();
                }
            }
        });
        // Si la ventana crece a escritorio con el panel abierto, se cierra
        window.matchMedia("(min-width: 992px)").addEventListener("change", function (mq) {
            if (mq.matches && header.classList.contains("is-open")) {
                close(false);
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
