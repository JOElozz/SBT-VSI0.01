// ─────────────────────────────────────────────
// UTILIDADES SVG
// ─────────────────────────────────────────────
function svgEl(tag, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    Object.keys(attrs).forEach(function(k) { el.setAttribute(k, attrs[k]); });
    return el;
}

function svgTexto(svg, x, y, texto, attrs) {
    var el = svgEl('text', Object.assign({ x: x, y: y, 'text-anchor': 'middle', 'font-family': 'Inter, sans-serif' }, attrs));
    el.textContent = texto;
    svg.appendChild(el);
    return el;
}

function limpiarPanel(canvasId) {
    var viejo = document.getElementById(canvasId + '_svg');
    if (viejo) viejo.remove();
    var canvas = document.getElementById(canvasId);
    if (canvas) canvas.style.display = 'none';
    return document.getElementById(canvasId).parentNode;
}

// ─────────────────────────────────────────────
// 1. DONA — Tasa de Cumplimiento
// ─────────────────────────────────────────────
function dibujarDona(canvasId, autorizados, denegados) {
    var contenedor = limpiarPanel(canvasId);
    var total = autorizados + denegados;
    var pct   = total === 0 ? 0 : Math.round((autorizados / total) * 100);
    var r = 72, cx = 130, cy = 100;
    var circ = 2 * Math.PI * r;
    var arcoVerde = total === 0 ? 0 : (autorizados / total) * circ;

    var svg = svgEl('svg', { id: canvasId + '_svg', viewBox: '0 0 260 230', width: '100%', height: '230px' });

    // Círculo fondo (rojo)
    svg.appendChild(svgEl('circle', { cx: cx, cy: cy, r: r, fill: 'none', stroke: '#dc3545', 'stroke-width': 26 }));

    // Arco verde
    if (autorizados > 0) {
        var arco = svgEl('circle', {
            cx: cx, cy: cy, r: r, fill: 'none',
            stroke: '#28a745', 'stroke-width': 26,
            'stroke-dasharray': arcoVerde + ' ' + (circ - arcoVerde),
            transform: 'rotate(-90 ' + cx + ' ' + cy + ')'
        });
        svg.appendChild(arco);
    }

    // Texto central
    svgTexto(svg, cx, cy - 6, pct + '%', { 'font-size': 28, 'font-weight': 'bold', fill: '#212529' });
    svgTexto(svg, cx, cy + 14, 'cumplimiento', { 'font-size': 11, fill: '#888' });

    // Leyenda
    var ly = cy + r + 24;
    svg.appendChild(svgEl('rect', { x: 30, y: ly, width: 13, height: 13, rx: 3, fill: '#28a745' }));
    var t1 = svgEl('text', { x: 48, y: ly + 11, 'font-size': 12, fill: '#333', 'font-family': 'Inter,sans-serif' });
    t1.textContent = 'Autorizados (' + autorizados + ')';
    svg.appendChild(t1);

    svg.appendChild(svgEl('rect', { x: 30, y: ly + 20, width: 13, height: 13, rx: 3, fill: '#dc3545' }));
    var t2 = svgEl('text', { x: 48, y: ly + 31, 'font-size': 12, fill: '#333', 'font-family': 'Inter,sans-serif' });
    t2.textContent = 'Denegados (' + denegados + ')';
    svg.appendChild(t2);

    contenedor.appendChild(svg);
}

// ─────────────────────────────────────────────
// 2. BARRAS — Top EPP Faltante
// ─────────────────────────────────────────────
function dibujarBarras(canvasId, etiquetas, valores) {
    var contenedor = limpiarPanel(canvasId);
    var maxV = Math.max.apply(null, valores.concat([1]));
    var hBarra = 26, gap = 10, mIzq = 90, mDer = 30, mTop = 8, ancho = 260;
    var aBarra = ancho - mIzq - mDer;
    var alto   = mTop + etiquetas.length * (hBarra + gap) + 10;

    var svg = svgEl('svg', { id: canvasId + '_svg', viewBox: '0 0 ' + ancho + ' ' + alto, width: '100%', height: Math.max(alto, 100) + 'px' });

    etiquetas.forEach(function(etq, i) {
        var y    = mTop + i * (hBarra + gap);
        var wBar = (valores[i] / maxV) * aBarra;
        var txt  = etq.length > 11 ? etq.substring(0, 10) + '…' : etq;

        var lbl = svgEl('text', { x: mIzq - 6, y: y + hBarra / 2 + 4, 'text-anchor': 'end', 'font-size': 11, fill: '#555', 'font-family': 'Inter,sans-serif' });
        lbl.textContent = txt;
        svg.appendChild(lbl);

        svg.appendChild(svgEl('rect', { x: mIzq, y: y, width: aBarra, height: hBarra, rx: 4, fill: '#f0f0f0' }));
        if (wBar > 0) {
            svg.appendChild(svgEl('rect', { x: mIzq, y: y, width: wBar, height: hBarra, rx: 4, fill: '#ffc107' }));
        }

        var num = svgEl('text', { x: mIzq + wBar + 5, y: y + hBarra / 2 + 4, 'font-size': 11, 'font-weight': 'bold', fill: '#333', 'font-family': 'Inter,sans-serif' });
        num.textContent = valores[i];
        svg.appendChild(num);
    });

    contenedor.appendChild(svg);
}

// ─────────────────────────────────────────────
// 4. SEMÁFORO — Indicador de seguridad
// ─────────────────────────────────────────────
function dibujarSemaforo(canvasId, pct) {
    var contenedor = limpiarPanel(canvasId);
    var color, texto, emoji;
    if (pct >= 80)      { color = '#28a745'; texto = 'SEGURO';     emoji = '✔'; }
    else if (pct >= 50) { color = '#ffc107'; texto = 'ATENCIÓN';   emoji = '⚠'; }
    else                { color = '#dc3545'; texto = 'RIESGO';      emoji = '✖'; }

    var svg = svgEl('svg', { id: canvasId + '_svg', viewBox: '0 0 260 180', width: '100%', height: '180px' });

    // Fondo redondeado
    svg.appendChild(svgEl('rect', { x: 20, y: 20, width: 220, height: 140, rx: 20, fill: color, opacity: '0.12' }));
    svg.appendChild(svgEl('rect', { x: 20, y: 20, width: 220, height: 140, rx: 20, fill: 'none', stroke: color, 'stroke-width': 3 }));

    // Emoji / icono grande
    svgTexto(svg, 130, 85, emoji, { 'font-size': 48, fill: color });

    // Porcentaje
    svgTexto(svg, 130, 118, pct + '%', { 'font-size': 22, 'font-weight': 'bold', fill: color });

    // Estado
    svgTexto(svg, 130, 142, texto, { 'font-size': 13, fill: color, 'font-weight': 'bold', 'letter-spacing': 2 });

    contenedor.appendChild(svg);
}

// ─────────────────────────────────────────────
// 5. LÍNEA DE TIEMPO — Incidentes por hora
// ─────────────────────────────────────────────
function dibujarLinea(canvasId, horasLabels, autorizadosPorHora, denegadosPorHora) {
    var contenedor = limpiarPanel(canvasId);
    var mIzq = 30, mDer = 15, mTop = 15, mBot = 35;
    var ancho = 560, alto = 160;
    var aGraf = ancho - mIzq - mDer;
    var hGraf = alto - mTop - mBot;
    var n = horasLabels.length;
    var maxV = Math.max.apply(null, autorizadosPorHora.concat(denegadosPorHora).concat([1]));

    var svg = svgEl('svg', { id: canvasId + '_svg', viewBox: '0 0 ' + ancho + ' ' + alto, width: '100%', height: alto + 'px' });

    // Líneas guía horizontales
    [0, 0.25, 0.5, 0.75, 1].forEach(function(f) {
        var y = mTop + hGraf * (1 - f);
        svg.appendChild(svgEl('line', { x1: mIzq, y1: y, x2: ancho - mDer, y2: y, stroke: '#e0e0e0', 'stroke-width': 1 }));
        if (f > 0) {
            var lbl = svgEl('text', { x: mIzq - 4, y: y + 4, 'text-anchor': 'end', 'font-size': 9, fill: '#aaa', 'font-family': 'Inter,sans-serif' });
            lbl.textContent = Math.round(maxV * f);
            svg.appendChild(lbl);
        }
    });

    function xPos(i) { return mIzq + (i / Math.max(n - 1, 1)) * aGraf; }
    function yPos(v) { return mTop + hGraf * (1 - v / maxV); }

    function dibujarLineas(valores, color) {
        if (n < 2) return;
        var d = 'M ' + xPos(0) + ' ' + yPos(valores[0]);
        for (var i = 1; i < n; i++) { d += ' L ' + xPos(i) + ' ' + yPos(valores[i]); }
        svg.appendChild(svgEl('path', { d: d, fill: 'none', stroke: color, 'stroke-width': 2.5, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));
        valores.forEach(function(v, i) {
            svg.appendChild(svgEl('circle', { cx: xPos(i), cy: yPos(v), r: 4, fill: color }));
        });
    }

    dibujarLineas(autorizadosPorHora, '#28a745');
    dibujarLineas(denegadosPorHora,   '#dc3545');

    // Etiquetas eje X (cada 2 horas)
    horasLabels.forEach(function(h, i) {
        if (i % 2 === 0) {
            var lbl = svgEl('text', { x: xPos(i), y: alto - mBot + 14, 'text-anchor': 'middle', 'font-size': 9, fill: '#888', 'font-family': 'Inter,sans-serif' });
            lbl.textContent = h + 'h';
            svg.appendChild(lbl);
        }
    });

    // Leyenda
    var lyX = ancho - mDer - 120;
    svg.appendChild(svgEl('line', { x1: lyX, y1: mTop + 8, x2: lyX + 16, y2: mTop + 8, stroke: '#28a745', 'stroke-width': 2.5 }));
    var lt1 = svgEl('text', { x: lyX + 20, y: mTop + 12, 'font-size': 10, fill: '#333', 'font-family': 'Inter,sans-serif' });
    lt1.textContent = 'Autorizados';
    svg.appendChild(lt1);

    svg.appendChild(svgEl('line', { x1: lyX, y1: mTop + 24, x2: lyX + 16, y2: mTop + 24, stroke: '#dc3545', 'stroke-width': 2.5 }));
    var lt2 = svgEl('text', { x: lyX + 20, y: mTop + 28, 'font-size': 10, fill: '#333', 'font-family': 'Inter,sans-serif' });
    lt2.textContent = 'Denegados';
    svg.appendChild(lt2);

    contenedor.appendChild(svg);
}

// ─────────────────────────────────────────────
// GRÁFICA EXTRA — Cumplimiento por Trabajador
// ─────────────────────────────────────────────
function dibujarPorTrabajador(canvasId, trabajadores, autorizados, denegados) {
    var contenedor = limpiarPanel(canvasId);
    var n = trabajadores.length;
    var hBarra = 22, gap = 8, mIzq = 85, mDer = 10, mTop = 8, ancho = 260;
    var aBarra = ancho - mIzq - mDer;
    var alto   = mTop + n * (hBarra + gap) + 10;

    var svg = svgEl('svg', { id: canvasId + '_svg', viewBox: '0 0 ' + ancho + ' ' + Math.max(alto, 80), width: '100%', height: Math.max(alto, 80) + 'px' });

    trabajadores.forEach(function(trab, i) {
        var y    = mTop + i * (hBarra + gap);
        var tot  = autorizados[i] + denegados[i];
        var wOk  = tot === 0 ? 0 : (autorizados[i] / tot) * aBarra;
        var wMal = aBarra - wOk;
        var txt  = trab.length > 10 ? trab.substring(0, 9) + '…' : trab;

        var lbl = svgEl('text', { x: mIzq - 5, y: y + hBarra / 2 + 4, 'text-anchor': 'end', 'font-size': 10, fill: '#555', 'font-family': 'Inter,sans-serif' });
        lbl.textContent = txt;
        svg.appendChild(lbl);

        if (wOk > 0)  svg.appendChild(svgEl('rect', { x: mIzq,       y: y, width: wOk,  height: hBarra, rx: 4, fill: '#28a745' }));
        if (wMal > 0) svg.appendChild(svgEl('rect', { x: mIzq + wOk, y: y, width: wMal, height: hBarra, rx: 0, fill: '#dc3545' }));

        var pct = tot === 0 ? 0 : Math.round((autorizados[i] / tot) * 100);
        var num = svgEl('text', { x: mIzq + aBarra + 5, y: y + hBarra / 2 + 4, 'font-size': 10, 'font-weight': 'bold', fill: '#333', 'font-family': 'Inter,sans-serif' });
        num.textContent = pct + '%';
        svg.appendChild(num);
    });

    contenedor.appendChild(svg);
}

// ─────────────────────────────────────────────
// FECHA HOY — formatea para mostrar en UI
// ─────────────────────────────────────────────
function fechaHoyStr() {
    var d = new Date();
    var dd = String(d.getDate()).padStart(2, '0');
    var mm = String(d.getMonth() + 1).padStart(2, '0');
    var yyyy = d.getFullYear();
    return dd + '/' + mm + '/' + yyyy;
}

// ─────────────────────────────────────────────
// CARGA PRINCIPAL — usa /historial/hoy
// ─────────────────────────────────────────────
function cargarHistorial() {
    fetch('/historial/hoy')
        .then(function(r) { return r.json(); })
        .then(function(rawData) {
            var data = Array.isArray(rawData) ? rawData : [];

            // Actualizar fecha en el título
            var elFecha = document.getElementById('fecha-hoy');
            if (elFecha) elFecha.textContent = fechaHoyStr();

            var autorizados = data.filter(function(a) { return a.resultado === 'AUTORIZADO'; }).length;
            var denegados   = data.filter(function(a) { return a.resultado === 'DENEGADO'; }).length;
            var total       = data.length;
            var pct         = total === 0 ? 0 : Math.round((autorizados / total) * 100);

            document.getElementById('total').textContent       = total;
            document.getElementById('autorizados').textContent = autorizados;
            document.getElementById('denegados').textContent   = denegados;

            // ── Dona ──
            dibujarDona('graficaCumplimiento', autorizados, denegados);

            // ── Semáforo ──
            dibujarSemaforo('graficaSemaforo', pct);

            // ── EPP Faltante ──
            var conteoEpp = {};
            data.forEach(function(a) {
                if (a.resultado === 'DENEGADO' && a.faltante && a.faltante !== '-') {
                    a.faltante.split(',').forEach(function(epp) {
                        var e = epp.trim();
                        if (e) { conteoEpp[e] = (conteoEpp[e] || 0) + 1; }
                    });
                }
            });
            var etiquetasEpp = Object.keys(conteoEpp).sort(function(a, b) { return conteoEpp[b] - conteoEpp[a]; });
            var valoresEpp   = etiquetasEpp.map(function(e) { return conteoEpp[e]; });
            if (etiquetasEpp.length === 0) { etiquetasEpp = ['Sin datos']; valoresEpp = [0]; }
            dibujarBarras('graficaFaltantes', etiquetasEpp, valoresEpp);

            // ── Línea de tiempo por hora ──
            var porHora = {};
            for (var h = 0; h < 24; h++) { porHora[h] = { ok: 0, mal: 0 }; }
            data.forEach(function(a) {
                // timestamp: YYYYMMDD_HHMMSS → hora = caracteres 9-10
                var hora = parseInt(a.timestamp.substring(9, 11), 10);
                if (!isNaN(hora)) {
                    if (a.resultado === 'AUTORIZADO') porHora[hora].ok++;
                    else                              porHora[hora].mal++;
                }
            });
            // Solo mostrar horas con actividad + contexto
            var horasActivas = Object.keys(porHora).filter(function(h) {
                return porHora[h].ok > 0 || porHora[h].mal > 0;
            }).map(Number);

            var horaMin = horasActivas.length > 0 ? Math.max(0,  Math.min.apply(null, horasActivas) - 1) : 6;
            var horaMax = horasActivas.length > 0 ? Math.min(23, Math.max.apply(null, horasActivas) + 1) : 18;
            var horasLabels = [], okPorHora = [], malPorHora = [];
            for (var hh = horaMin; hh <= horaMax; hh++) {
                horasLabels.push(String(hh).padStart(2, '0'));
                okPorHora.push(porHora[hh].ok);
                malPorHora.push(porHora[hh].mal);
            }
            dibujarLinea('graficaLinea', horasLabels, okPorHora, malPorHora);

            // ── Por Trabajador ──
            var porTrab = {};
            data.forEach(function(a) {
                var t = a.trabajador || 'DESCONOCIDO';
                if (!porTrab[t]) porTrab[t] = { ok: 0, mal: 0 };
                if (a.resultado === 'AUTORIZADO') porTrab[t].ok++;
                else                              porTrab[t].mal++;
            });
            var trabKeys = Object.keys(porTrab).sort(function(a, b) {
                return (porTrab[b].ok + porTrab[b].mal) - (porTrab[a].ok + porTrab[a].mal);
            });
            dibujarPorTrabajador(
                'graficaTrabajador',
                trabKeys,
                trabKeys.map(function(t) { return porTrab[t].ok; }),
                trabKeys.map(function(t) { return porTrab[t].mal; })
            );

            // ── Tabla ──
            var tbody = document.getElementById('tabla-body');
            tbody.innerHTML = '';
            data.slice().reverse().forEach(function(a) {
                var badge = a.resultado === 'AUTORIZADO'
                    ? '<span class="badge-ok">AUTORIZADO</span>'
                    : '<span class="badge-mal">DENEGADO</span>';
                tbody.innerHTML += '<tr>'
                    + '<td>' + (a.trabajador || '-') + '</td>'
                    + '<td>' + (a.timestamp  || '-') + '</td>'
                    + '<td>' + badge + '</td>'
                    + '<td>' + (a.fase       || '-') + '</td>'
                    + '<td>' + (a.faltante   || '-') + '</td>'
                    + '</tr>';
            });
        })
        .catch(function(err) { console.error('Error al cargar historial:', err); });
}

cargarHistorial();
setInterval(cargarHistorial, 3000);