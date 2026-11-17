/* Un solo reloj entrega el mismo fotograma lógico a uno o dos mapas. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const text = (id, value) => { $(id).textContent = value; };
  const fmt = (value, digits = 2) => new Intl.NumberFormat("es-SV", {minimumFractionDigits: digits, maximumFractionDigits: digits}).format(value);
  const signed = (value, digits = 2) => (value > 0 ? "+" : "") + fmt(value, digits);
  const escape = value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  const STREAMS = ["W_E", "E_W", "N_W", "E_N", "N_E", "W_S"];
  const S = {mode: "single", scenario: "base", time: 0, playing: false, speed: 5, selectedEdge: "1257993561#5", selectedVehicle: "", chartMode: "paired"};
  let D, V, clock, primary, secondary, odChart, activeChart, cursor, ready = false, previous = 0, syncingCamera = false;
  const timings = {single: [], compare: []}, rafGaps = [], versions = {};
  let framesRendered = 0;
  const currentPanes = () => S.mode === "compare" ? [primary, secondary] : [primary];
  function pause() {
    clock?.pause(); S.playing = false;
    if ($("play")) { $("play").innerHTML = '<span aria-hidden="true">▶</span> Reproducir'; $("play").setAttribute("aria-pressed", "false"); }
  }
  function fail(message) {
    if ($("runtime-error")) { $("runtime-error").hidden = false; text("runtime-error", "No se pudo representar la evidencia: " + message); }
    pause();
  }
  window.addEventListener("error", event => fail(event.message));
  window.addEventListener("unhandledrejection", event => fail(String(event.reason)));
  async function waitFor(read, message) {
    const began = performance.now();
    while (performance.now() - began < 15000) {
      const result = read(); if (result) return result;
      await new Promise(resolve => setTimeout(resolve, 25));
    }
    throw new Error(message);
  }
  function seek(value) { if (clock.seek(value)) { pause(); renderFrame(); } }
  function play() {
    if (clock.playing) { pause(); return; }
    clock.play(); S.playing = true;
    $("play").innerHTML = '<span aria-hidden="true">Ⅱ</span> Pausar'; $("play").setAttribute("aria-pressed", "true");
    renderFrame();
  }
  function animate(now) {
    if (clock.playing) {
      rafGaps.push(now - previous); if (rafGaps.length > 5000) rafGaps.shift();
      if (clock.tick(now - previous)) renderFrame();
      if (!clock.playing) pause();
    }
    previous = now; requestAnimationFrame(animate);
  }
  function syncCamera(source, target) {
    if (S.mode !== "compare" || syncingCamera) return;
    const a = source.map.getCenter(), b = target.map.getCenter(), zoom = source.map.getZoom();
    if (Math.abs(a.lat - b.lat) < 1e-10 && Math.abs(a.lng - b.lng) < 1e-10 && zoom === target.map.getZoom()) return;
    syncingCamera = true; target.map.setView(a, zoom, {animate: false}); syncingCamera = false;
  }
  function selectEdge(id) {
    const road = D.roads.find(road => road.id === id); if (!road) return;
    S.selectedEdge = id; primary.selectEdge(id); secondary.selectEdge(id); $("edge-select").value = id;
    text("edge-name", road.name);
    const defaults = road.defaults.map(key => ({numLanes: "carriles", speed: "velocidad"})[key] || key);
    text("edge-detail", id + " · " + road.lanes + " carriles · " + fmt(road.speed * 3.6, 0) + " km/h" +
      (defaults.length ? " · valores supuestos: " + defaults.join(", ") : " · atributos OSM/SUMO, sin validación de campo"));
  }
  function selectVehicle(id) {
    if (id && !V.vehicles[id]) { text("vehicle-error", "Elige un ID original de la lista."); return; }
    pause(); S.selectedVehicle = id; $("vehicle-search").value = id; text("vehicle-error", "");
    primary.selectVehicle(id); secondary.selectVehicle(id);
    $("vehicle-inspector").hidden = !id; $("selected-vehicle-key").hidden = !id;
    renderFrame();
  }
  function vehicleInspector(pair) {
    if (!S.selectedVehicle) return;
    text("selected-vehicle-title", S.selectedVehicle);
    for (const scenario of ["base", "closure"]) {
      const result = DTReplay.vehicleState(D, V, S.selectedVehicle, scenario, pair);
      const stateText = {active: "En la red", "not-departed": "Aún no salió", finished: "Viaje finalizado", "no-sample": "Sin muestra FCD en este instante"}[result.state];
      text("vehicle-" + scenario + "-state", stateText);
      text("vehicle-" + scenario + "-detail", result.sample ? "Velocidad " + fmt(result.sample[3]) + " m/s" :
        result.state === "not-departed" ? "Salida registrada: " + fmt(result.info.depart_s, 0) + " s" :
        result.state === "finished" ? "Llegada registrada: " + fmt(result.info.arrival_s, 0) + " s" : "No se inventa una posición.");
      text("vehicle-" + scenario + "-trip", "Viaje completo: " + fmt(result.info.duration_s, 0) + " s · " + fmt(result.info.route_length_m) + " m");
    }
    const a = V.vehicles[S.selectedVehicle].base, b = V.vehicles[S.selectedVehicle].closure;
    text("vehicle-route-note", (JSON.stringify(a.route) === JSON.stringify(b.route) ? "Misma ruta ejecutada." : "Las rutas ejecutadas difieren; se resaltan en cada mapa.") +
      " Cambio de duración: " + signed(b.duration_s - a.duration_s, 0) + " s.");
  }
  function locateVehicle() {
    if (!S.selectedVehicle) return;
    const pair = DTReplay.framePair(D, clock.time), points = ["base", "closure"].map(scenario =>
      DTReplay.vehicleState(D, V, S.selectedVehicle, scenario, pair).sample).filter(Boolean).map(row => [row[1], row[2]]);
    if (!points.length) { text("vehicle-error", "Este vehículo no tiene posición FCD en el instante elegido."); return; }
    currentPanes().forEach(pane => pane.map.invalidateSize({pan: false}));
    primary.map.fitBounds(L.latLngBounds(points).pad(.5), {padding: [70, 50], maxZoom: 19, animate: false});
    syncCamera(primary, secondary);
  }
  function renderFrame() {
    const began = performance.now(), pair = DTReplay.framePair(D, clock.time);
    S.time = pair.time; S.playing = clock.playing; S.speed = clock.speed;
    // No hay await, temporizador secundario ni posiciones interpoladas entre estos dos renders.
    for (const pane of currentPanes()) pane.render(pair);
    for (const [key, pane] of [["primary", primary], ["secondary", secondary]]) {
      text("pane-" + key + "-count", D.active[pane.scenario][pair.time] + " activos · " + D.arrived[pane.scenario][pair.time] + " finalizaron");
    }
    text("clock", "t = " + fmt(pair.time, 0) + " s"); $("time-slider").value = pair.time; $("seek-time").value = pair.time;
    text("frame-status", S.mode === "compare" ? "Dos mapas · un reloj · muestras de 1 s" :
      D.active[S.scenario][pair.time] + " activos · " + D.arrived[S.scenario][pair.time] + " finalizaron");
    text("active-now", S.mode === "compare" ? "Base " + D.active.base[pair.time] + " / Cierre " + D.active.closure[pair.time] + " veh" :
      D.active[S.scenario][pair.time] + " vehículos · " + (S.scenario === "base" ? "base" : "cierre"));
    const x = activeChart.convertToPixel({xAxisIndex: 0}, pair.time);
    if (Number.isFinite(x)) cursor.style.left = x + "px";
    vehicleInspector(pair);
    timings[S.mode].push(performance.now() - began); if (timings[S.mode].length > 5000) timings[S.mode].shift();
    framesRendered++;
  }
  function updateMetrics() {
    const metric = D.metrics[S.scenario], COLORS = DTMapPane.COLORS;
    document.querySelectorAll("button[data-scenario]").forEach(button => {
      const selected = button.dataset.scenario === S.scenario;
      button.classList.toggle("selected", selected); button.setAttribute("aria-pressed", String(selected));
    });
    text("map-scenario", S.scenario === "base" ? "Base" : "Cierre virtual");
    $("map-scenario").classList.toggle("is-closure", S.scenario === "closure");
    text("clock-context", S.mode === "compare" ? "Reloj compartido" : S.scenario === "base" ? "Base" : "Cierre virtual");
    text("scenario-description", S.scenario === "base" ? "Red abierta. Se conserva el mismo calendario y demanda." :
      "Cierre del tramo resaltado de Roosevelt. Desvío por 35 Avenida Sur y Calle el Progreso.");
    $("completed-value").replaceChildren(document.createTextNode(metric.completed + " "));
    const total = document.createElement("small"); total.textContent = "/ " + metric.requested; $("completed-value").append(total);
    text("completion-detail", metric.pending + " pendientes · " + metric.rejected + " rechazos");
    for (const [id, value, digits] of [["duration-mean", metric.duration_s.mean, 2], ["duration-total", metric.duration_s.total, 0],
      ["waiting-mean", metric.waiting_time_s.mean, 2], ["loss-mean", metric.time_loss_s.mean, 2]]) text(id, fmt(value, digits) + " s");
    const delta = D.metrics.closure.duration_s.total - D.metrics.base.duration_s.total;
    text("impact-total", signed(delta, 0) + " s"); text("impact-percent", signed(delta / D.metrics.base.duration_s.total * 100) + " %");
    text("compare-impact", signed(delta, 0) + " s · " + signed(delta / D.metrics.base.duration_s.total * 100) + " %");
    text("closure-legend", S.mode === "compare" || S.scenario === "closure" ? "Cerrado solo en cierre" : "Enlace evaluado, abierto");
    $("closed-key").style.background = S.mode === "compare" || S.scenario === "closure" ? COLORS.closed : "#68745c";
    $("vehicle-key").style.background = COLORS[S.scenario];
  }
  function setScenario(scenario) {
    if (!["base", "closure"].includes(scenario)) return;
    pause(); S.scenario = scenario;
    if (S.mode === "single") {
      primary.setScenario(scenario); text("pane-primary-title", scenario === "base" ? "Base · red abierta" : "Cierre virtual");
    }
    updateMetrics(); renderFrame();
  }
  function setMode(mode) {
    if (!["single", "compare"].includes(mode)) return;
    pause();
    const camera = primary.map.getCenter(), zoom = primary.map.getZoom();
    S.mode = mode; document.querySelector(".prototype-shell").dataset.mode = mode;
    $("secondary-map-panel").hidden = mode !== "compare";
    $("single-indicators").hidden = mode === "compare"; $("compare-indicators").hidden = mode !== "compare";
    $("map-scenario").hidden = mode === "compare";
    $("mode-single").setAttribute("aria-pressed", String(mode === "single"));
    $("mode-compare").setAttribute("aria-pressed", String(mode === "compare"));
    primary.setScenario(mode === "compare" ? "base" : S.scenario); secondary.setScenario("closure");
    text("pane-primary-title", mode === "compare" ? "Base" : S.scenario === "base" ? "Base · red abierta" : "Cierre virtual");
    text("camera-note", mode === "compare" ? "Zoom y desplazamiento vinculados" : "Mapa único");
    for (const pane of currentPanes()) { pane.map.invalidateSize({pan: false}); pane.map.setView(camera, zoom, {animate: false}); }
    updateMetrics(); renderFrame();
  }
  function fitMaps() {
    currentPanes().forEach(pane => pane.map.invalidateSize({pan: false}));
    primary.fit(); if (S.mode === "compare") syncCamera(primary, secondary);
  }
  function chartMode(mode) {
    S.chartMode = mode; const COLORS = DTMapPane.COLORS;
    $("chart-paired").setAttribute("aria-pressed", String(mode === "paired")); $("chart-delta").setAttribute("aria-pressed", String(mode === "delta"));
    const series = mode === "paired" ? ["base", "closure"].map((scenario, i) => ({
      name: i ? "Cierre" : "Base", type: "bar", barMaxWidth: 20, itemStyle: {color: COLORS[scenario], borderRadius: [3, 3, 0, 0]},
      data: STREAMS.map(stream => D.comparison.by_stream[stream].duration_s[scenario + "_mean"]),
    })) : [{name: "Cierre − base", type: "bar", barMaxWidth: 26, data: STREAMS.map(stream => {
      const value = D.comparison.by_stream[stream].duration_s.delta_mean;
      return {value, itemStyle: {color: value < 0 ? COLORS.base : COLORS.closure, borderRadius: [3, 3, 0, 0]}};
    })}];
    odChart.setOption({series, legend: {show: mode === "paired"}, yAxis: {name: mode === "paired" ? "s / viaje" : "Δ s / viaje"},
      tooltip: {trigger: "axis", formatter: params => {
        const stream = STREAMS[params[0].dataIndex], values = D.comparison.by_stream[stream].duration_s;
        return "<strong>" + escape(stream) + "</strong> · " + escape(D.movementDescriptions[stream]) +
          "<br>Base " + fmt(values.base_mean) + " s · Cierre " + fmt(values.closure_mean) + " s<br>Δ " + signed(values.delta_mean) + " s / viaje";
      }}}, {replaceMerge: ["series"]});
    text("od-note", mode === "paired" ? "Duración media por viaje. Los códigos identifican los seis movimientos; consulta sus nombres al pasar el cursor." :
      "Diferencia de medias: cierre − base, en segundos por viaje. Más tiempo en terracota; menos tiempo en verde.");
  }
  function diagnostics() {
    const stats = values => {
      const sorted = [...values].sort((a, b) => a - b);
      return {samples: values.length, renderMean_ms: values.reduce((a, b) => a + b, 0) / (values.length || 1),
        renderP95_ms: sorted[Math.floor((sorted.length - 1) * .95)] || 0, renderMax_ms: sorted.at(-1) || 0};
    };
    return {framesRendered, ...stats([...timings.single, ...timings.compare]), byMode: {single: stats(timings.single), compare: stats(timings.compare)},
      rafMeanGap_ms: rafGaps.reduce((a, b) => a + b, 0) / (rafGaps.length || 1), versions: {...versions}};
  }
  async function start(primaryId, secondaryId, odId, activeId) {
    if (ready) return true;
    const mapA = await waitFor(() => getElement(primaryId)?.map, "No se inicializó el mapa principal");
    const mapB = await waitFor(() => getElement(secondaryId)?.map, "No se inicializó el mapa de cierre");
    odChart = await waitFor(() => getElement(odId)?.chart, "No se inicializó el gráfico por movimiento");
    activeChart = await waitFor(() => getElement(activeId)?.chart, "No se inicializó el gráfico temporal");
    const responses = await Promise.all([fetch("/prototype-data.json", {cache: "no-store"}), fetch("/vehicle-catalog.json", {cache: "no-store"})]);
    if (responses.some(response => !response.ok)) throw new Error("No están disponibles los datos locales");
    [D, V] = await Promise.all(responses.map(response => response.json()));
    if (D.schema !== "digitaltwins-nicegui-1" || D.combination !== "original_offset000" || V.schema !== "digitaltwins-vehicle-catalog-1") throw new Error("Fuentes incompatibles");
    clock = new DTReplay.ReplayClock(D.last_time_s);
    primary = new DTMapPane.MapPane(mapA, D, V, "base", {onEdge: selectEdge, onVehicle: selectVehicle});
    secondary = new DTMapPane.MapPane(mapB, D, V, "closure", {onEdge: selectEdge, onVehicle: selectVehicle});
    primary.map.on("move zoom moveend zoomend", () => syncCamera(primary, secondary));
    secondary.map.on("move zoom moveend zoomend", () => syncCamera(secondary, primary));
    for (const road of [...D.roads].sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id))) {
      const option = document.createElement("option"); option.value = road.id; option.textContent = road.name + " · " + road.id; $("edge-select").append(option);
    }
    for (const id of D.vehicles) { const option = document.createElement("option"); option.value = id; $("vehicle-ids").append(option); }
    cursor = document.createElement("div"); cursor.className = "chart-playhead"; cursor.setAttribute("aria-hidden", "true"); activeChart.getDom().append(cursor);
    activeChart.on("finished", () => { if (D) { const x = activeChart.convertToPixel({xAxisIndex: 0}, clock.time); if (Number.isFinite(x)) cursor.style.left = x + "px"; } });
    $("play").onclick = play; $("reset").onclick = () => seek(0); $("advance").onclick = () => seek(clock.time + 10);
    $("time-slider").oninput = event => seek(event.target.value); $("speed").onchange = event => { clock.speed = Number(event.target.value); S.speed = clock.speed; };
    $("seek-form").onsubmit = event => { event.preventDefault(); seek($("seek-time").value); };
    $("fit-map").onclick = fitMaps; $("mode-single").onclick = () => setMode("single"); $("mode-compare").onclick = () => setMode("compare");
    $("edge-select").onchange = event => selectEdge(event.target.value);
    $("vehicle-search").oninput = event => { if (!event.target.value || V.vehicles[event.target.value]) selectVehicle(event.target.value); };
    $("vehicle-form").onsubmit = event => { event.preventDefault(); selectVehicle($("vehicle-search").value); };
    $("clear-vehicle").onclick = () => selectVehicle(""); $("locate-vehicle").onclick = locateVehicle;
    document.querySelectorAll("button[data-scenario]").forEach(button => { button.onclick = () => setScenario(button.dataset.scenario); });
    $("chart-paired").onclick = () => chartMode("paired"); $("chart-delta").onclick = () => chartMode("delta");
    $("analysis-details").addEventListener("toggle", () => {
      if ($("analysis-details").open) requestAnimationFrame(() => { odChart.resize(); activeChart.resize(); renderFrame(); });
    });
    versions.leaflet = L.version; versions.echarts = (await import("nicegui-echart")).echarts.version;
    const narrow = matchMedia("(max-width: 760px)");
    const collapse = () => { $("indicators-panel").open = !narrow.matches; $("analysis-details").open = !narrow.matches; };
    collapse(); narrow.addEventListener("change", collapse);
    window.addEventListener("resize", () => requestAnimationFrame(() => {
      if (S.mode === "compare") syncCamera(primary, secondary);
    }));
    selectEdge(D.closedEdge); chartMode("paired"); setMode("single"); ready = true; requestAnimationFrame(animate);
    return true;
  }
  function inspect() {
    const a = primary?.inspect(), b = secondary?.inspect(), selected = S.mode === "compare" && S.scenario === "closure" ? b : a;
    return {...selected, state: {...S}, active: D?.active[S.scenario][S.time], arrived: D?.arrived[S.scenario][S.time],
      panes: {primary: a, secondary: b}, selectedVehicle: S.selectedVehicle, diagnostics: diagnostics(),
      odSeries: odChart?.getOption().series.map(series => ({name: series.name, data: series.data}))};
  }
  const api = Object.freeze({start, getState: () => ({...S, ready}), inspect});
  window.DT008 = api;
  window.DT007 = api; // Compatibilidad de la prueba funcional del modo único.
})();
