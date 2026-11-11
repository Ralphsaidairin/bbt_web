/* Babatsa · "Abierta ahora" en las tarjetas de sucursal.
   Cada .bbt-open trae data-schedule = {tz, days: {"0": [[8, 18]], ...}, closed: ["2026-12-25"]}
   (0 = lunes; horas en decimal), armado desde el horario de trabajo de Odoo de la sucursal.
   La hora se calcula en la zona horaria de la sucursal, no en la del visitante. Se actualiza cada minuto. */
(function () {
    "use strict";

    var DAYS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

    // Fecha y hora actuales en la zona horaria de la sucursal
    function nowIn(tz) {
        var parts = {};
        new Intl.DateTimeFormat("en-US", {
            timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit", hourCycle: "h23",
        }).formatToParts(new Date()).forEach(function (p) {
            parts[p.type] = p.value;
        });
        // Fecha "local" representada en UTC para poder sumar días sin brincos de horario de verano
        var date = new Date(Date.UTC(+parts.year, +parts.month - 1, +parts.day));
        return { date: date, hour: +parts.hour + (+parts.minute) / 60 };
    }

    function iso(date) {
        return date.toISOString().slice(0, 10);
    }

    function fmtHour(h) {
        var hh = Math.floor(h);
        var mm = Math.round((h - hh) * 60);
        return hh + ":" + (mm < 10 ? "0" : "") + mm;
    }

    function fmtLeft(hours) {
        var mins = Math.max(1, Math.round(hours * 60));
        if (mins < 60) {
            return mins + " min";
        }
        var h = Math.floor(mins / 60);
        var m = mins % 60;
        return h + " h" + (m ? " " + m + " min" : "");
    }

    // Odoo: 0 = lunes … 6 = domingo; JS getUTCDay: 0 = domingo
    function blocksFor(schedule, date) {
        if (schedule.closed.indexOf(iso(date)) !== -1) {
            return null;
        }
        return schedule.days[String((date.getUTCDay() + 6) % 7)] || [];
    }

    function status(schedule) {
        var now = nowIn(schedule.tz);
        var today = blocksFor(schedule, now.date);
        var i;
        if (today) {
            for (i = 0; i < today.length; i++) {
                if (now.hour >= today[i][0] && now.hour < today[i][1]) {
                    var left = today[i][1] - now.hour;
                    return {
                        state: left <= 1 ? "soon" : "open",
                        text: left <= 1 ? "Cierra en " + fmtLeft(left) : "Abierta · cierra a las " + fmtHour(today[i][1]),
                    };
                }
            }
        }
        var prefix = today === null ? "Cerrada hoy por día festivo" : "Cerrada";
        for (var d = 0; d < 14; d++) {
            var day = new Date(now.date.getTime() + d * 86400000);
            var blocks = blocksFor(schedule, day) || [];
            for (i = 0; i < blocks.length; i++) {
                if (d > 0 || blocks[i][0] > now.hour) {
                    var when = d === 0 ? "hoy" : d === 1 ? "mañana" : "el " + DAYS[day.getUTCDay()];
                    return { state: "closed", text: prefix + " · abre " + when + " a las " + fmtHour(blocks[i][0]) };
                }
            }
        }
        return { state: "closed", text: prefix };
    }

    function init() {
        var items = [];
        document.querySelectorAll(".bbt-open[data-schedule]").forEach(function (el) {
            window.bbtMount(el, function () {
                track(el);
            });
        });
        function track(el) {
            try {
                var schedule = JSON.parse(el.getAttribute("data-schedule"));
                schedule.closed = schedule.closed || [];
                items.push({ el: el, schedule: schedule, text: el.querySelector(".bbt-open-text") });
            } catch (e) {
                el.hidden = true;
            }
        }
        if (!items.length) {
            return;
        }
        function render() {
            items.forEach(function (item) {
                var s = status(item.schedule);
                item.el.setAttribute("data-state", s.state);
                item.text.textContent = s.text;
            });
        }
        render();
        window.setInterval(render, 60000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
