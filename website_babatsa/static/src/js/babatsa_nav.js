/* Babatsa · encabezado propio (cápsula, doble barra o pantalla completa).
   - Se compacta al bajar y se esconde al seguir bajando; reaparece al subir.
   - El botón de menú abre el panel: en celular sube desde abajo; en "pantalla completa" cubre todo.
     Esc, el fondo o un enlace lo cierran.
   - Doble barra: "Productos" abre el mega menú (clic, Esc o clic afuera lo cierran). */
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

        // ---------- Mega menú (doble barra) ----------
        var megaToggle = header.querySelector(".bbt-mega-toggle");
        var mega = header.querySelector(".bbt-mega");
        function setMega(open) {
            header.classList.toggle("is-mega", open);
            megaToggle.setAttribute("aria-expanded", open ? "true" : "false");
        }
        if (megaToggle && mega) {
            megaToggle.addEventListener("click", function () {
                setMega(!header.classList.contains("is-mega"));
            });
            document.addEventListener("click", function (ev) {
                if (header.classList.contains("is-mega") && !megaToggle.contains(ev.target) && !mega.contains(ev.target)) {
                    setMega(false);
                }
            });
            document.addEventListener("keydown", function (ev) {
                if (ev.key === "Escape" && header.classList.contains("is-mega")) {
                    setMega(false);
                    megaToggle.focus();
                }
            });
            // Al bajar con el mega abierto, se cierra
            window.addEventListener("scroll", function () {
                if (header.classList.contains("is-mega") && window.scrollY > 200) {
                    setMega(false);
                }
            }, { passive: true });
        }

        // ---------- Panel de menú ----------
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
            // Esperar a que termine la animación de cierre (la de pantalla completa es la más larga)
            closeTimer = window.setTimeout(function () {
                panel.hidden = true;
                backdrop.hidden = true;
            }, 580);
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
        // Si la ventana crece a escritorio con el panel de celular abierto, se cierra
        // (en pantalla completa el panel también existe en escritorio)
        var isFull = header.classList.contains("bbt-nav--completo");
        window.matchMedia("(min-width: 992px)").addEventListener("change", function (mq) {
            if (!isFull && mq.matches && header.classList.contains("is-open")) {
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
