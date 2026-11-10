/* Babatsa · "Tu pieza" (/tu-pieza, views/website_tu_pieza_templates.xml).
   - Cada tipo de pieza tiene sus medidas y un dibujo técnico que se redibuja con las proporciones
     que captura el cliente (un balero de 25/52 no se ve igual que uno de 40/52).
   - mm o pulgadas (acepta fracciones: 3/4, 1 1/2) con la conversión al lado.
   - La lista se manda al controlador /tu-pieza/enviar (CRM + folio) y, si la sucursal tiene
     WhatsApp, se abre el chat con el mensaje ya escrito.
   Dentro del constructor no se monta: el HTML generado se guardaría en la plantilla. */
(function () {
    "use strict";

    var MM_PER_IN = 25.4;
    var SVG_NS = "http://www.w3.org/2000/svg";

    var TYPES = {
        balero: { name: "Balero", dims: [
            { k: "d", label: "Diámetro interior", help: "El hueco donde entra el eje" },
            { k: "D", label: "Diámetro exterior" },
            { k: "B", label: "Ancho" },
        ] },
        reten: { name: "Retén", dims: [
            { k: "d", label: "Diámetro del eje", help: "El hueco del centro" },
            { k: "D", label: "Diámetro exterior" },
            { k: "B", label: "Ancho" },
        ] },
        banda: { name: "Banda", dims: [
            { k: "W", label: "Ancho de arriba" },
            { k: "H", label: "Alto" },
            { k: "L", label: "Largo por fuera", help: "Si está rota, mide de punta a punta" },
        ] },
        tornillo: { name: "Tornillo", dims: [
            { k: "M", label: "Diámetro" },
            { k: "L", label: "Largo sin cabeza" },
            { k: "P", label: "Paso de la rosca", pitch: true, help: "Distancia entre hilos (en pulgadas: hilos por pulgada)" },
        ] },
        manguera: { name: "Manguera", dims: [
            { k: "ID", label: "Diámetro interior" },
            { k: "L", label: "Largo" },
            { k: "P", label: "Presión de trabajo", fixed: "psi", help: "Viene impresa en la manguera" },
        ] },
        otra: { name: "Otra pieza", dims: [] },
    };

    // Lo que dice la mascota al elegir cada tipo de pieza
    var TIPS = {
        balero: "Mide el hueco del centro (d), el diámetro de afuera (D) y el ancho (B). Si trae un número grabado en la cara, anótalo: dice casi todo.",
        reten: "Mide el eje donde va, el diámetro de afuera y el ancho. Muchos retenes traen las medidas grabadas, por ejemplo 35-52-7.",
        banda: "Busca el número impreso en la banda (por ejemplo A-42): con eso basta. Si ya no se lee, mide el ancho de arriba y el largo por fuera.",
        tornillo: "Mide el grueso de la rosca, no de la cabeza. El largo se toma desde abajo de la cabeza hasta la punta.",
        manguera: "Mide por dentro, no por fuera. La presión casi siempre viene impresa en la manguera.",
        otra: "Tómale una foto junto a una regla o una moneda para que se vea el tamaño, y cuéntanos de qué equipo es.",
    };

    // ---------------------------------------------------------------- números y unidades
    function parseNum(str) {
        var s = String(str || "").trim().replace(",", ".");
        var m = s.match(/^(\d+(?:\.\d+)?)\s*(?:-|\s)\s*(\d+)\/(\d+)$/);
        if (m) {
            return +m[1] + m[2] / m[3];
        }
        m = s.match(/^(\d+)\/(\d+)$/);
        if (m) {
            return m[1] / m[2];
        }
        return /^\d+(\.\d+)?$/.test(s) ? parseFloat(s) : NaN;
    }

    function round(n, digits) {
        var f = Math.pow(10, digits);
        return String(Math.round(n * f) / f);
    }

    function unitLabel(dim, unit) {
        if (dim.fixed) {
            return dim.fixed;
        }
        if (dim.pitch) {
            return unit === "in" ? "hilos/pulg" : "mm";
        }
        return unit === "in" ? "pulg" : "mm";
    }

    // Convierte un valor capturado de una unidad a la otra (el paso en pulgadas es hilos por pulgada)
    function convert(dim, n, from) {
        if (dim.fixed || isNaN(n) || n <= 0) {
            return NaN;
        }
        if (dim.pitch) {
            return MM_PER_IN / n;
        }
        return from === "mm" ? n / MM_PER_IN : n * MM_PER_IN;
    }

    function clamp(n, lo, hi) {
        return Math.max(lo, Math.min(hi, n));
    }

    // ---------------------------------------------------------------- dibujo
    function el(tag, attrs, parent) {
        var node = document.createElementNS(SVG_NS, tag);
        Object.keys(attrs || {}).forEach(function (k) {
            node.setAttribute(k, attrs[k]);
        });
        if (parent) {
            parent.appendChild(node);
        }
        return node;
    }

    function Drawing(labels) {
        this.svg = el("svg", { viewBox: "0 0 520 300", class: "bbt-pz-svg" });
        var defs = el("defs", {}, this.svg);
        var marker = el("marker", { id: "bbt-pz-arrow", viewBox: "0 0 10 10", refX: "9", refY: "5",
            markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse" }, defs);
        el("path", { d: "M0 1L10 5L0 9z", class: "pz-arrow" }, marker);
        this.labels = labels;
    }
    Drawing.prototype.add = function (tag, attrs) {
        return el(tag, attrs, this.svg);
    };
    Drawing.prototype.text = function (x, y, str, cls, parent) {
        var t = el("text", { x: x, y: y, class: cls || "pz-dim-t", "text-anchor": "middle" }, parent || this.svg);
        t.textContent = str;
        return t;
    };
    // Cota horizontal o vertical con flechas y su etiqueta "d = 25 mm"
    Drawing.prototype.dim = function (k, x1, y1, x2, y2, tx, ty) {
        var g = el("g", { class: "pz-dim", "data-dim": k }, this.svg);
        el("line", { x1: x1, y1: y1, x2: x2, y2: y2, "marker-start": "url(#bbt-pz-arrow)", "marker-end": "url(#bbt-pz-arrow)" }, g);
        this.text(tx, ty, this.labels[k], "pz-dim-t", g);
        return g;
    };

    function ringParts(v) {
        var D = v.D || 52;
        var d = v.d || 25;
        return { r: clamp(d / D, 0.25, 0.82), w: clamp((v.B || 15) / D, 0.14, 0.9) };
    }

    var DRAW = {
        balero: function (dr, v) {
            var p = ringParts(v);
            var cx = 150, cy = 140, R = 104, rIn = R * p.r;
            var Ro = R - (R - rIn) * 0.24, Ri = rIn + (R - rIn) * 0.24;
            var rm = (Ro + Ri) / 2, br = (Ro - Ri) / 2 * 0.82;
            var n = clamp(Math.floor(2 * Math.PI * rm / (br * 2.5)), 6, 16);
            dr.add("circle", { cx: cx, cy: cy, r: R, class: "pz-metal" });
            dr.add("circle", { cx: cx, cy: cy, r: Ro, class: "pz-dark" });
            for (var i = 0; i < n; i++) {
                var a = i / n * 2 * Math.PI;
                dr.add("circle", { cx: cx + rm * Math.cos(a), cy: cy + rm * Math.sin(a), r: br, class: "pz-ball" });
            }
            dr.add("circle", { cx: cx, cy: cy, r: Ri, class: "pz-metal" });
            dr.add("circle", { cx: cx, cy: cy, r: rIn, class: "pz-bore" });
            // Vista lateral
            var w = p.w * 2 * R, x0 = 400 - w / 2;
            dr.add("rect", { x: x0, y: cy - R, width: w, height: 2 * R, rx: 4, class: "pz-metal" });
            dr.add("rect", { x: x0, y: cy - Ro, width: w, height: Ro - Ri, class: "pz-dark" });
            dr.add("rect", { x: x0, y: cy + Ri, width: w, height: Ro - Ri, class: "pz-dark" });
            dr.add("rect", { x: x0 + w * 0.2, y: cy - rm - br * 0.7, width: w * 0.6, height: br * 1.4, rx: br * 0.7, class: "pz-ball" });
            dr.add("rect", { x: x0 + w * 0.2, y: cy + rm - br * 0.7, width: w * 0.6, height: br * 1.4, rx: br * 0.7, class: "pz-ball" });
            dr.add("rect", { x: x0, y: cy - rIn, width: w, height: 2 * rIn, class: "pz-bore pz-bore--side" });
            dr.dim("d", cx - rIn + 2, cy, cx + rIn - 2, cy, cx, cy - 8);
            dr.dim("D", cx - R, cy + R + 22, cx + R, cy + R + 22, cx, cy + R + 44);
            dr.dim("B", x0, cy + R + 22, x0 + w, cy + R + 22, 400, cy + R + 44);
        },
        reten: function (dr, v) {
            var p = ringParts(v);
            var cx = 150, cy = 140, R = 104, rIn = R * p.r;
            dr.add("circle", { cx: cx, cy: cy, r: R, class: "pz-metal" });
            dr.add("circle", { cx: cx, cy: cy, r: R - 9, class: "pz-rubber" });
            dr.add("circle", { cx: cx, cy: cy, r: rIn + (R - rIn) * 0.3, class: "pz-spring", fill: "none" });
            dr.add("circle", { cx: cx, cy: cy, r: rIn + 6, class: "pz-lip" });
            dr.add("circle", { cx: cx, cy: cy, r: rIn, class: "pz-bore" });
            var w = p.w * 2 * R, x0 = 400 - w / 2;
            dr.add("rect", { x: x0, y: cy - R, width: w, height: 2 * R, rx: 3, class: "pz-rubber" });
            dr.add("rect", { x: x0, y: cy - R, width: w, height: 9, class: "pz-metal" });
            dr.add("rect", { x: x0, y: cy + R - 9, width: w, height: 9, class: "pz-metal" });
            dr.add("rect", { x: x0, y: cy - rIn, width: w, height: 2 * rIn, class: "pz-bore pz-bore--side" });
            [-1, 1].forEach(function (s) {
                var y = cy + s * rIn;
                dr.add("path", { d: "M" + (x0 + w * 0.15) + " " + (y + s * 14) + "L" + (x0 + w * 0.5) + " " + y + "L" + (x0 + w * 0.85) + " " + (y + s * 14) + "Z", class: "pz-lip" });
                dr.add("circle", { cx: x0 + w * 0.5, cy: y + s * 20, r: 4, class: "pz-spring" });
            });
            dr.dim("d", cx - rIn + 2, cy, cx + rIn - 2, cy, cx, cy - 8);
            dr.dim("D", cx - R, cy + R + 22, cx + R, cy + R + 22, cx, cy + R + 44);
            dr.dim("B", x0, cy + R + 22, x0 + w, cy + R + 22, 400, cy + R + 44);
        },
        banda: function (dr, v) {
            var h = clamp((v.H || 8) / (v.W || 13), 0.35, 1);
            var cx = 120, top = 96, topW = 150, height = topW * h;
            var bottomW = Math.max(26, topW - 0.73 * height);
            dr.add("path", { d: "M" + (cx - topW / 2) + " " + top + "H" + (cx + topW / 2) + "L" + (cx + bottomW / 2) + " " + (top + height) +
                "H" + (cx - bottomW / 2) + "Z", class: "pz-rubber" });
            dr.add("line", { x1: cx - topW / 2 + 10, y1: top + height * 0.28, x2: cx + topW / 2 - 10, y2: top + height * 0.28, class: "pz-cord" });
            dr.dim("W", cx - topW / 2, top - 20, cx + topW / 2, top - 20, cx, top - 30);
            dr.dim("H", cx + topW / 2 + 22, top, cx + topW / 2 + 22, top + height, cx + topW / 2 + 52, top + height / 2 + 5);
            // La banda montada en sus poleas
            dr.add("circle", { cx: 330, cy: 150, r: 46, class: "pz-metal" });
            dr.add("circle", { cx: 462, cy: 150, r: 30, class: "pz-metal" });
            dr.add("circle", { cx: 330, cy: 150, r: 10, class: "pz-dark" });
            dr.add("circle", { cx: 462, cy: 150, r: 7, class: "pz-dark" });
            dr.add("path", { d: "M330 98L462 114A36 36 0 0 1 462 186L330 202A52 52 0 0 1 330 98Z", class: "pz-belt" });
            dr.dim("L", 278, 238, 498, 238, 388, 262);
        },
        tornillo: function (dr, v) {
            var M = v.M || 10;
            var ratio = clamp((v.L || 40) / M, 1.5, 9);
            var cy = 140, sh = 44, x0 = 46, headW = 40;
            var len = clamp(sh * ratio, 90, 340);
            var end = x0 + headW + len;
            dr.add("rect", { x: x0, y: cy - sh * 0.85, width: headW, height: sh * 1.7, rx: 4, class: "pz-metal" });
            dr.add("line", { x1: x0, y1: cy - sh * 0.3, x2: x0 + headW, y2: cy - sh * 0.3, class: "pz-edge" });
            dr.add("line", { x1: x0, y1: cy + sh * 0.3, x2: x0 + headW, y2: cy + sh * 0.3, class: "pz-edge" });
            dr.add("path", { d: "M" + (x0 + headW) + " " + (cy - sh / 2) + "H" + (end - 6) + "L" + end + " " + (cy - sh / 2 + 6) +
                "V" + (cy + sh / 2 - 6) + "L" + (end - 6) + " " + (cy + sh / 2) + "H" + (x0 + headW) + "Z", class: "pz-metal" });
            // Rosca: el espaciado sigue al paso capturado (en pulgadas, hilos por pulgada)
            var pitchMm = v.P ? (v.unit === "in" ? MM_PER_IN / v.P : v.P) : M * 0.15;
            var mMm = v.unit === "in" ? M * MM_PER_IN : M;
            var step = clamp(sh * pitchMm / mMm, 5, 18);
            var threadStart = x0 + headW + len * 0.35;
            for (var x = threadStart; x < end - 8; x += step) {
                dr.add("line", { x1: x, y1: cy - sh / 2, x2: x + step * 0.6, y2: cy + sh / 2, class: "pz-thread" });
            }
            dr.dim("M", end + 22, cy - sh / 2, end + 22, cy + sh / 2, Math.min(end + 22, 470), cy - sh / 2 - 12);
            dr.dim("L", x0 + headW, cy + sh * 0.85 + 26, end, cy + sh * 0.85 + 26, x0 + headW + len / 2, cy + sh * 0.85 + 50);
            dr.dim("P", threadStart, cy - sh / 2 - 18, threadStart + step, cy - sh / 2 - 18, threadStart + step / 2, cy - sh / 2 - 28);
        },
        manguera: function (dr) {
            var cx = 100, cy = 150, R = 66, r = R * 0.58;
            dr.add("circle", { cx: cx, cy: cy, r: R, class: "pz-rubber" });
            dr.add("circle", { cx: cx, cy: cy, r: R - 12, fill: "none", class: "pz-cord" });
            dr.add("circle", { cx: cx, cy: cy, r: r, class: "pz-bore" });
            dr.dim("ID", cx - r + 2, cy, cx + r - 2, cy, cx, cy - 8);
            dr.add("rect", { x: 214, y: cy - 26, width: 258, height: 52, rx: 10, class: "pz-rubber" });
            dr.add("line", { x1: 236, y1: cy, x2: 450, y2: cy, class: "pz-print" });
            dr.add("rect", { x: 196, y: cy - 34, width: 30, height: 68, rx: 4, class: "pz-metal" });
            dr.add("rect", { x: 460, y: cy - 34, width: 30, height: 68, rx: 4, class: "pz-metal" });
            dr.dim("L", 196, cy + 62, 490, cy + 62, 343, cy + 86);
            // Manómetro con la presión
            var g = dr.add("g", { class: "pz-dim", "data-dim": "P" });
            el("circle", { cx: 343, cy: 50, r: 26, class: "pz-gauge" }, g);
            el("path", { d: "M343 50L360 37", class: "pz-needle" }, g);
            dr.text(343, 100, dr.labels.P, "pz-dim-t", g);
        },
        otra: function (dr) {
            dr.add("rect", { x: 140, y: 50, width: 240, height: 180, rx: 18, class: "pz-dashed" });
            dr.add("rect", { x: 222, y: 104, width: 76, height: 56, rx: 10, class: "pz-metal" });
            dr.add("circle", { cx: 260, cy: 132, r: 16, class: "pz-bore" });
            dr.add("rect", { x: 236, y: 94, width: 22, height: 12, rx: 3, class: "pz-metal" });
            dr.text(260, 200, "Tómale una foto y cuéntanos qué es", "pz-dim-t pz-dim-t--note");
        },
    };

    // ---------------------------------------------------------------- herramienta
    function init() {
        var form = document.querySelector("form.bbt-pz");
        if (!form || window.frameElement || document.body.classList.contains("editor_enable")) {
            return;
        }
        form.classList.add("is-ready");
        var draw = form.querySelector(".bbt-pz-draw");
        var dimsBox = form.querySelector(".bbt-pz-dims");
        var codigo = form.querySelector("#bbt-pz-codigo");
        var equipo = form.querySelector("#bbt-pz-equipo");
        var listEl = form.querySelector(".bbt-pz-list");
        var emptyEl = form.querySelector(".bbt-pz-empty");
        var photos = form.querySelector('input[name="fotos"]');
        var thumbs = form.querySelector(".bbt-pz-thumbs");
        var sucursal = form.querySelector('select[name="sucursal"]');
        var waBtn = form.querySelector("button.bbt-pz-wa");
        var errorEl = form.querySelector(".bbt-pz-error");
        var guide = form.querySelector(".bbt-guide");

        function say(text) {
            if (!guide) {
                return;
            }
            guide.querySelector(".bbt-guide-text").textContent = text;
            guide.classList.remove("is-talking");
            void guide.offsetWidth; // reinicia la animación
            guide.classList.add("is-talking");
        }

        var state = { type: "balero", unit: "mm", values: {}, list: [], focus: null };
        Object.keys(TYPES).forEach(function (t) {
            state.values[t] = {};
        });

        function numbers() {
            var v = { unit: state.unit };
            TYPES[state.type].dims.forEach(function (dim) {
                var n = parseNum(state.values[state.type][dim.k]);
                v[dim.k] = n > 0 ? n : 0;
            });
            return v;
        }

        function labelFor(dim) {
            var raw = state.values[state.type][dim.k];
            return dim.k + " = " + (raw ? raw + " " + unitLabel(dim, state.unit) : "?");
        }

        function render() {
            var labels = {};
            TYPES[state.type].dims.forEach(function (dim) {
                labels[dim.k] = labelFor(dim);
            });
            var dr = new Drawing(labels);
            DRAW[state.type](dr, numbers());
            draw.replaceChildren(dr.svg);
            highlight();
        }

        function highlight() {
            draw.querySelectorAll(".pz-dim").forEach(function (g) {
                g.classList.toggle("is-on", g.getAttribute("data-dim") === state.focus);
            });
        }

        function conversionText(dim, raw) {
            var n = parseNum(raw);
            var c = convert(dim, n, state.unit);
            if (isNaN(c)) {
                return raw && isNaN(n) ? "Escribe solo el número (ej. 25, 1.5 o 3/4)" : (dim.help || "");
            }
            var other = state.unit === "mm" ? "in" : "mm";
            return "= " + round(c, other === "mm" ? 1 : 3) + " " + unitLabel(dim, other);
        }

        function renderFields() {
            dimsBox.replaceChildren();
            TYPES[state.type].dims.forEach(function (dim) {
                var id = "bbt-pz-dim-" + dim.k;
                var wrap = document.createElement("div");
                wrap.className = "bbt-field bbt-pz-dim";
                wrap.innerHTML = '<label></label><div class="bbt-pz-input"><input type="text" inputmode="decimal" autocomplete="off"/><span></span></div><small></small>';
                var label = wrap.querySelector("label");
                label.setAttribute("for", id);
                label.innerHTML = "<b></b> ";
                label.querySelector("b").textContent = dim.k;
                label.appendChild(document.createTextNode(dim.label));
                var input = wrap.querySelector("input");
                input.id = id;
                input.value = state.values[state.type][dim.k] || "";
                wrap.querySelector("span").textContent = unitLabel(dim, state.unit);
                var note = wrap.querySelector("small");
                note.textContent = conversionText(dim, input.value);
                input.addEventListener("input", function () {
                    state.values[state.type][dim.k] = input.value.trim();
                    note.textContent = conversionText(dim, input.value);
                    wrap.classList.toggle("is-bad", !!input.value.trim() && isNaN(parseNum(input.value)));
                    render();
                });
                input.addEventListener("focus", function () {
                    state.focus = dim.k;
                    highlight();
                });
                input.addEventListener("blur", function () {
                    state.focus = null;
                    highlight();
                });
                dimsBox.appendChild(wrap);
            });
        }

        function setType(type, quiet) {
            state.type = type;
            form.setAttribute("data-type", type);
            renderFields();
            render();
            if (!quiet) {
                say(TIPS[type]);
            }
        }

        // Cambiar de unidad convierte lo ya capturado
        function setUnit(unit) {
            if (unit === state.unit) {
                return;
            }
            Object.keys(TYPES).forEach(function (t) {
                TYPES[t].dims.forEach(function (dim) {
                    var c = convert(dim, parseNum(state.values[t][dim.k]), state.unit);
                    if (!isNaN(c)) {
                        state.values[t][dim.k] = round(c, unit === "mm" || dim.pitch ? 1 : 3);
                    }
                });
            });
            state.unit = unit;
            say(unit === "in" ? "En pulgadas puedes escribir fracciones: 3/4 o 1 1/2. Yo lo convierto a milímetros." : "Listo, en milímetros. Te muestro la conversión a pulgadas debajo de cada medida.");
            form.querySelectorAll(".bbt-pz-units button").forEach(function (b) {
                b.classList.toggle("is-on", b.getAttribute("data-unit") === unit);
            });
            renderFields();
            render();
        }

        function currentItem() {
            var medidas = [];
            TYPES[state.type].dims.forEach(function (dim) {
                var raw = state.values[state.type][dim.k];
                if (raw && !isNaN(parseNum(raw))) {
                    medidas.push({ nombre: dim.label.toLowerCase(), valor: raw, unidad: unitLabel(dim, state.unit) });
                }
            });
            var item = { tipo: TYPES[state.type].name, codigo: codigo.value.trim(), equipo: equipo.value.trim(), medidas: medidas };
            return item.codigo || item.equipo || medidas.length ? item : null;
        }

        function renderList() {
            listEl.replaceChildren();
            state.list.forEach(function (item, i) {
                var li = document.createElement("li");
                var title = document.createElement("b");
                title.textContent = item.tipo + (item.codigo ? " " + item.codigo : "");
                var detail = document.createElement("span");
                detail.textContent = item.medidas.map(function (m) {
                    return m.nombre + " " + m.valor + " " + m.unidad;
                }).concat(item.equipo ? ["para " + item.equipo] : []).join(" · ");
                var del = document.createElement("button");
                del.type = "button";
                del.className = "bbt-pz-del";
                del.setAttribute("aria-label", "Quitar " + title.textContent);
                del.textContent = "×";
                del.addEventListener("click", function () {
                    state.list.splice(i, 1);
                    renderList();
                });
                li.append(title, detail, del);
                listEl.appendChild(li);
            });
            emptyEl.hidden = state.list.length > 0;
            form.querySelector('input[name="piezas"]').value = JSON.stringify(state.list);
        }

        function addCurrent() {
            var item = currentItem();
            if (!item) {
                return false;
            }
            state.list.push(item);
            state.values[state.type] = {};
            codigo.value = "";
            equipo.value = "";
            renderFields();
            render();
            renderList();
            listEl.lastElementChild.classList.add("is-new");
            say(state.list.length > 1 ? "Van " + state.list.length + " piezas en tu lista. Cuando acabes, elige tu sucursal y mándala." : "¡Va! Ya está en tu lista. Agrega otra o mándala a tu sucursal.");
            return true;
        }

        function renderThumbs() {
            var files = Array.prototype.slice.call(photos.files || []);
            if (files.length > 3 && window.DataTransfer) {
                var dt = new DataTransfer();
                files.slice(0, 3).forEach(function (f) {
                    dt.items.add(f);
                });
                photos.files = dt.files;
                files = files.slice(0, 3);
            }
            thumbs.replaceChildren();
            files.forEach(function (f) {
                var img = document.createElement("img");
                img.alt = f.name;
                img.src = URL.createObjectURL(f);
                thumbs.appendChild(img);
            });
        }

        function updateWhatsapp() {
            var opt = sucursal.options[sucursal.selectedIndex];
            var noWa = opt && opt.value && opt.getAttribute("data-whatsapp") !== "1";
            waBtn.disabled = !!noWa;
            waBtn.title = noWa ? "Esta sucursal no tiene WhatsApp; usa \"Mejor que me llamen\"" : "";
        }

        function fail(msg) {
            say(msg);
            errorEl.textContent = msg;
            errorEl.hidden = false;
            errorEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }

        function done(data, accion) {
            var text = "Tu folio es " + data.folio + ". ";
            var link = form.querySelector(".bbt-pz-done-wa");
            if (accion === "whatsapp" && data.whatsapp_url) {
                text += "Te abrimos WhatsApp con el mensaje listo para " + data.sucursal + ": solo dale enviar.";
                link.href = data.whatsapp_url;
                link.hidden = false;
            } else {
                text += data.sucursal + " te llamará al teléfono que dejaste.";
            }
            form.querySelector(".bbt-pz-done-text").textContent = text;
            form.classList.add("is-done");
            var panel = form.querySelector(".bbt-pz-done");
            panel.hidden = false;
            panel.focus();
            panel.scrollIntoView({ block: "center", behavior: "smooth" });
            if (accion === "whatsapp" && data.whatsapp_url) {
                window.setTimeout(function () {
                    window.location.href = data.whatsapp_url;
                }, 900);
            }
        }

        form.addEventListener("submit", function (ev) {
            ev.preventDefault();
            var accion = (ev.submitter && ev.submitter.getAttribute("data-accion")) || "whatsapp";
            form.querySelector('input[name="accion"]').value = accion;
            errorEl.hidden = true;
            addCurrent();
            var nota = form.querySelector('textarea[name="nota"]').value.trim();
            if (!state.list.length && !nota && !(photos.files && photos.files.length)) {
                return fail("Agrega al menos una pieza, una foto o un comentario.");
            }
            if (!sucursal.value) {
                sucursal.focus();
                return fail("Elige la sucursal a la que se lo mandamos.");
            }
            if (!form.querySelector('input[name="nombre"]').value.trim()) {
                form.querySelector('input[name="nombre"]').focus();
                return fail("Escribe tu nombre.");
            }
            if (form.querySelector('input[name="telefono"]').value.replace(/\D/g, "").length < 10) {
                form.querySelector('input[name="telefono"]').focus();
                return fail("Escribe tu teléfono a 10 dígitos para que la sucursal te pueda contactar.");
            }
            var buttons = form.querySelectorAll(".bbt-pz-send button");
            buttons.forEach(function (b) {
                b.disabled = true;
            });
            form.classList.add("is-sending");
            fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    if (!data.ok) {
                        throw new Error((data.errors || []).join(","));
                    }
                    done(data, accion);
                })
                .catch(function () {
                    fail("No pudimos enviar tu solicitud. Revisa tus datos e intenta otra vez, o llama a tu sucursal.");
                })
                .finally(function () {
                    form.classList.remove("is-sending");
                    buttons.forEach(function (b) {
                        b.disabled = false;
                    });
                    updateWhatsapp();
                });
        });

        form.querySelectorAll('input[name="tipo"]').forEach(function (radio) {
            radio.addEventListener("change", function () {
                if (radio.checked) {
                    setType(radio.value);
                }
            });
        });
        form.querySelectorAll(".bbt-pz-units button").forEach(function (b) {
            b.addEventListener("click", function () {
                setUnit(b.getAttribute("data-unit"));
            });
        });
        form.querySelector(".bbt-pz-add").addEventListener("click", function () {
            if (!addCurrent()) {
                var first = dimsBox.querySelector("input") || codigo;
                first.focus();
            }
        });
        photos.addEventListener("change", renderThumbs);
        sucursal.addEventListener("change", updateWhatsapp);

        var checked = form.querySelector('input[name="tipo"]:checked');
        setType(checked ? checked.value : "balero", !new URLSearchParams(window.location.search).get("tipo"));
        renderList();
        updateWhatsapp();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
