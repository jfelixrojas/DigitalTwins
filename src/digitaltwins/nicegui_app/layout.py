"""Textos y controles de la pantalla; datos científicos cargados aparte."""
from html import escape

HEADER = """
<div class="brand"><span class="brand-mark">DT</span><div><strong>DigitalTwins</strong><span>Laboratorio de movilidad urbana</span></div></div>
<div class="header-meta"><span class="local-label">COMPARADOR LOCAL / 008</span><span class="synthetic-badge">Datos sintéticos</span><span class="calibration-label">Sin calibración real</span></div>
"""
INTRO = """
<div><p class="eyebrow">San Salvador · El Salvador</p><h1>Alameda Roosevelt</h1><p class="intro-caption">El mismo instante, dos escenarios. Explora el efecto de un cierre virtual.</p></div>
<a class="experiment-shortcut" href="#experiment">SIM-005 <span>Original / desfase 0 s</span><span aria-hidden="true">↘</span></a>
"""
MODE_TOOLS = """
<div class="mode-switch" role="group" aria-label="Modo de visualización"><button id="mode-single" type="button" aria-pressed="true">Un mapa</button><button id="mode-compare" type="button" aria-pressed="false">Comparar base y cierre</button></div>
<div id="single-scenario-controls" class="scenario-switch" role="group" aria-label="Escenario del mapa único"><button id="scenario-base" data-scenario="base" class="selected" aria-pressed="true" type="button">Base</button><button id="scenario-closure" data-scenario="closure" aria-pressed="false" type="button">Cierre virtual</button></div>
<span id="camera-note">Mapa único</span>
<form id="vehicle-form" class="vehicle-search"><label for="vehicle-search">Mismo vehículo</label><input id="vehicle-search" list="vehicle-ids" autocomplete="off" placeholder="Buscar ID original" aria-label="ID del vehículo"><datalist id="vehicle-ids"></datalist><button type="submit">Ver</button><button id="clear-vehicle" type="button" aria-label="Quitar selección de vehículo">×</button></form>
<p id="vehicle-error" role="status"></p>
"""
MAP_HEADING = """
<div><h2>Red y trayectorias</h2><p>Consulta un tramo en el mapa o en la lista.</p></div>
<div class="map-heading-actions"><button id="fit-map" type="button">Encuadrar</button><span id="map-scenario" class="scenario-tag">Base</span></div>
"""
MAP_FOOT = """
<div class="map-legend"><span><i class="key network-key"></i>Red vial</span><span class="single-vehicle-key"><i id="vehicle-key" class="key dot-key"></i>Vehículos</span><span class="compare-vehicle-key"><i class="key dot-key base-key"></i>Base <i class="key dot-key closure-key"></i>Cierre</span><span><i class="key route-key"></i>Ruta mostrada</span><span><i class="key detour-key"></i>Desvío del cierre</span><span><i id="closed-key" class="key"></i><span id="closure-legend">Enlace evaluado, abierto</span></span><span id="selected-vehicle-key" hidden><i class="key selected-key"></i>Mismo ID seleccionado</span></div>
<div class="edge-selection"><label for="edge-select">Consultar tramo</label><select id="edge-select" aria-label="Seleccionar enlace dirigido"></select><strong id="edge-name" class="sr-only"></strong><span id="edge-detail"></span></div>
"""
PLAYBACK = """
<div class="playback-top"><div class="transport"><button id="play" class="primary" type="button" aria-pressed="false"><span aria-hidden="true">▶</span> Reproducir</button><button id="reset" type="button" aria-label="Reiniciar reproducción">↺ <span>Reiniciar</span></button><button id="advance" type="button" aria-label="Adelantar diez segundos">+10 s</button><label class="speed-label">Velocidad<select id="speed" aria-label="Velocidad de reproducción"><option value="1">1×</option><option value="5" selected>5×</option><option value="10">10×</option><option value="30">30×</option></select></label></div><div class="clock-group"><span id="clock-context" class="shared-clock-label">Base</span><output id="clock" for="time-slider">t = 0 s</output></div></div>
<input id="time-slider" type="range" min="0" max="1799" step="1" value="0" aria-label="Tiempo simulado en segundos">
<div class="timeline-meta"><span>0 s</span><p id="frame-status">Cargando trayectorias verificadas…</p><span>1799 s</span></div>
<div class="seek-row"><span>Muestras de 1 s · sin interpolación.</span><form id="seek-form"><label for="seek-time">Ir al segundo</label><input id="seek-time" type="number" min="0" max="1799" step="1" value="0" aria-label="Instante de simulación"><span>s</span><button type="submit">Ir</button></form></div>
"""
VEHICLE_INSPECTOR = """
<section id="vehicle-inspector" class="vehicle-inspector" hidden><div class="vehicle-inspector-heading"><div><p class="eyebrow">Un ID · el mismo instante</p><h3 id="selected-vehicle-title"></h3></div><button id="locate-vehicle" type="button">Localizar en ambos</button></div><div class="vehicle-pair"><article><span class="scenario-word base-word">Base</span><strong id="vehicle-base-state"></strong><p id="vehicle-base-detail"></p><small id="vehicle-base-trip"></small></article><article><span class="scenario-word closure-word">Cierre</span><strong id="vehicle-closure-state"></strong><p id="vehicle-closure-detail"></p><small id="vehicle-closure-trip"></small></article></div><p id="vehicle-route-note" class="vehicle-route-note"></p></section>
"""
SIMULATION = """
<p class="eyebrow">Original / 0 s</p><h2>Escenario consultado</h2>
<p id="scenario-description" class="scenario-description" aria-live="polite">Red abierta. Mismo calendario y demanda que en el cierre.</p>
<p class="result-scope">Resultados finales · horizonte 1800 s</p>
<div class="completion"><span id="completed-value">150 <small>/ 150</small></span><p>vehículos completados</p><span id="completion-detail">0 pendientes · 0 rechazos</span></div>
<dl class="main-metrics"><div><dt>Tiempo medio de recorrido</dt><dd id="duration-mean">—</dd></div><div><dt>Tiempo total de recorrido</dt><dd id="duration-total">—</dd></div></dl>
<div class="secondary-metrics"><div><span>Tiempo detenido</span><strong id="waiting-mean">—</strong><small>waitingTime medio</small></div><div><span>Tiempo perdido</span><strong id="loss-mean">—</strong><small>timeLoss medio · frente al ideal</small></div></div>
<div class="impact"><div><span>Impacto del cierre</span><small>cierre − base · tiempo total</small></div><strong id="impact-total">+405 s</strong><span id="impact-percent">+2,03 %</span></div>
<p class="metric-note">Mismos viajes en cada comparación. Tiempo detenido y tiempo perdido se solapan; no se suman.</p>
"""
ANALYSIS_HEADING = """
<div><p class="eyebrow">Comparación por movimiento</p><h2>Tiempo de recorrido</h2></div><div class="analysis-switch" role="group" aria-label="Vista del gráfico"><button id="chart-paired" type="button" aria-pressed="true">Base / cierre</button><button id="chart-delta" type="button" aria-pressed="false">Diferencia</button></div>
"""
ACTIVE_HEADING = """
<div><p class="eyebrow">Evolución temporal</p><h2>Vehículos activos</h2></div><span id="active-now" class="active-now">0 vehículos · base</span>
"""


def comparative_metrics(data):
    a, b = data["metrics"]["base"], data["metrics"]["closure"]
    rows = [("Completados / solicitados", f"{a['completed']} / {a['requested']}", f"{b['completed']} / {b['requested']}"),
            ("Recorrido medio (s)", f"{a['duration_s']['mean']:,.2f}", f"{b['duration_s']['mean']:,.2f}"),
            ("Recorrido total (s)", f"{a['duration_s']['total']:,.0f}", f"{b['duration_s']['total']:,.0f}"),
            ("Detenido medio · waitingTime (s)", f"{a['waiting_time_s']['mean']:,.2f}", f"{b['waiting_time_s']['mean']:,.2f}"),
            ("Perdido medio · timeLoss (s)", f"{a['time_loss_s']['mean']:,.2f}", f"{b['time_loss_s']['mean']:,.2f}")]
    return '<p class="horizon-note">Resultados finales del par · [0,1800) s</p><div class="table-scroll"><table id="compare-metrics"><thead><tr><th>Indicador</th><th>Base</th><th>Cierre</th></tr></thead><tbody>' + "".join(
        "<tr>" + "".join("<td>" + escape(value) + "</td>" for value in row) + "</tr>" for row in rows) + \
        '</tbody></table></div><p class="compare-impact">Impacto del cierre: <strong id="compare-impact">+405 s</strong></p><p class="metric-note">Tiempo detenido y tiempo perdido se solapan; no se suman. No hay pendientes en este par.</p>'


def experiment(catalog):
    return f"""
<details id="experiment" class="experiment"><summary><span>SIM-005</span> Experimento, datos y límites <span class="details-arrow">+</span></summary>
<div class="experiment-grid"><div><h3>Pregunta</h3><p>{escape(catalog['question'])}</p><h3>Par mostrado</h3><p>Original / desfase 0 s. Base y cierre virtual del tramo 1257993561#5 de Roosevelt, clase passenger, durante [0,1800) s. Los 45 viajes oeste → este toman un desvío.</p></div>
<div><h3>Datos utilizados</h3><p>FCD y rutas ejecutadas de SUMO 1.28.0. 150 viajes sintéticos, semilla 42, salidas antes de 900 s, horizonte 1800 s y registros cada 1 s. Red OSM/Geofabrik de octubre de 2026 y 18 programas semafóricos virtuales.</p><h3>Resultado del par</h3><p>+405 s de tiempo total (+2,03 %). El efecto depende del calendario; no es una predicción operacional.</p></div>
<div><h3>Limitaciones</h3><p>Demanda sintética, atributos inferidos y señales virtuales, sin calibración real. No hay conteos, Waze ni modelos CTM/LTM. La falta de una muestra nunca se rellena con una posición inventada.</p><p class="sheet-links">Fichas: <a href="/experiment/SIM-002.md" target="_blank" rel="noopener">SIM-002</a> · <a href="/experiment/SIM-003.md" target="_blank" rel="noopener">SIM-003</a> · <a href="/experiment/SIM-004.md" target="_blank" rel="noopener">SIM-004</a> · <a href="/experiment/SIM-005.md" target="_blank" rel="noopener">SIM-005</a></p><p class="trace-hash">Manifiesto SIM-005: {escape(catalog['manifest_sha256'])}</p></div></div></details>
"""
