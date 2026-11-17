/* Visor sin red: únicamente geometría, posiciones y registros verificados. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const error = message => { $("runtime-error").hidden = false; $("runtime-error").textContent = "No se pudo representar la evidencia: " + message; };
  window.addEventListener("error", event => error(event.message));
  window.addEventListener("unhandledrejection", event => error(String(event.reason)));
  const D = JSON.parse($("viewer-data").textContent);
  const S = {caseId: "original_offset000", scenario: "base", time: 0, playing: false, speed: 5, edge: D.closedEdge, tab: "explore"};
  const colors = {base: "#216cac", closure: "#d36c1c", W_E: "#216cac", E_W: "#d36c1c", N_W: "#8157a2", E_N: "#427841", N_E: "#b13d67", W_S: "#8a6c20"};
  const lanes = new Map(D.geometry.lanes.map(x => [x.id, x]));
  const roads = new Map(D.geometry.roads.map(x => [x.id, x]));
  const n = (value, places = 2) => new Intl.NumberFormat("es-SV", {maximumFractionDigits: places, minimumFractionDigits: places}).format(Number(value));
  const signed = (value, places = 2) => (Number(value) > 0 ? "+" : "") + n(value, places);
  const c = () => D.cases[S.caseId];
  const name = schedule => schedule === "original" ? "Original" : "J" + schedule.slice(-3);
  const label = row => name(row.schedule) + " / desfase " + row.offset + " s";
  const el = (tag, text, cls) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; };
  const svg = (tag, attrs = {}, text) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const link = (text, path) => { const node = el("a", text, "text-link"); node.href = path; return node; };
  const path = shape => shape.map((p, i) => (i ? "L" : "M") + p[0] + "," + (-p[1])).join(" ");
  function tableRow(parent, values, deltaColumns = []) {
    const tr = el("tr");
    values.forEach((value, i) => {
      const td = el("td", value);
      if (deltaColumns.includes(i)) td.className = Number(String(value).replaceAll(",", "")) > 0 ? "positive" : "negative";
      tr.append(td);
    });
    parent.append(tr); return tr;
  }
  function setTab(tab) {
    S.tab = tab;
    document.querySelectorAll("[data-tab]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.tab === tab)));
    document.querySelectorAll(".tab-panel").forEach(panel => { panel.hidden = panel.id !== "tab-" + tab; });
    if (tab === "explore") { metrics(); selectEdge(S.edge); renderFrame(); }
  }
  document.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click", () => setTab(button.dataset.tab)));

  // Los puntos están en el mismo sistema métrico local de SUMO. Solo se invierte Y para SVG.
  const bounds = D.geometry.bounds;
  const home = [bounds[0] - 35, -bounds[3] - 35, bounds[2] - bounds[0] + 70, bounds[3] - bounds[1] + 70];
  let viewport = [...home], drag = null;
  function symbolScale() {
    const scale = $("road-map").getScreenCTM()?.a || 1;
    for (const text of $("road-map").querySelectorAll(".map-label")) {
      text.setAttribute("font-size", (text.dataset.kind === "closure" ? 12 : 10) / scale);
      text.setAttribute("stroke-width", 3 / scale);
    }
    for (const dot of $("vehicle-layer").children) {
      dot.setAttribute("r", (dot.dataset.focal === "true" ? 4 : 2.6) / scale);
      dot.setAttribute("stroke-width", .8 / scale);
    }
  }
  const setView = () => { $("road-map").setAttribute("viewBox", viewport.join(" ")); symbolScale(); };
  function zoom(factor) {
    const width = Math.max(100, Math.min(home[2] * 3, viewport[2] * factor));
    const height = width * viewport[3] / viewport[2];
    viewport = [viewport[0] + (viewport[2] - width) / 2, viewport[1] + (viewport[3] - height) / 2, width, height]; setView();
  }
  $("zoom-in").onclick = () => zoom(.75); $("zoom-out").onclick = () => zoom(1.33);
  $("zoom-reset").onclick = () => { viewport = [...home]; setView(); };
  const map = $("road-map");
  map.addEventListener("pointerdown", event => {
    if (event.button !== 0) return;
    drag = {x: event.clientX, y: event.clientY, view: [...viewport], moved: false};
    map.setPointerCapture(event.pointerId); map.classList.add("dragging");
  });
  map.addEventListener("pointermove", event => {
    if (!drag) return;
    const scale = map.getScreenCTM().a, dx = (event.clientX - drag.x) / scale, dy = (event.clientY - drag.y) / scale;
    if (Math.abs(dx) + Math.abs(dy) > 3) drag.moved = true;
    viewport = [drag.view[0] - dx, drag.view[1] - dy, drag.view[2], drag.view[3]]; setView();
  });
  map.addEventListener("pointerup", event => {
    const moved = drag && drag.moved; drag = null; map.classList.remove("dragging");
    if (map.hasPointerCapture(event.pointerId)) map.releasePointerCapture(event.pointerId);
    if (!moved) {
      const point = document.elementFromPoint(event.clientX, event.clientY);
      const eid = point && point.getAttribute("data-edge");
      if (eid) selectEdge(eid);
    }
  });
  map.addEventListener("pointercancel", () => { drag = null; map.classList.remove("dragging"); });
  for (const road of roads.values()) for (const lid of road.lanes) {
    const line = svg("path", {d: path(lanes.get(lid).shape), stroke: "#c3cfc5", "stroke-width": 2.7, fill: "none", "stroke-linecap": "round", class: "road-path", "data-edge": road.id});
    line.append(svg("title", {}, road.name + " · " + road.id)); $("road-layer").append(line);
  }
  const signalPaths = D.geometry.signals.map(connection => {
    const line = svg("path", {d: path(lanes.get(connection.via).shape), fill: "none", "stroke-width": 4, "stroke-linecap": "round", "data-tls": connection.tls, "data-index": connection.index});
    line.append(svg("title")); $("signal-layer").append(line); return {connection, line};
  });
  setView();

  function drawEdge(group, edge, color, width, attrs = {}) {
    const road = roads.get(edge); if (!road) return;
    for (const lid of road.lanes) {
      const p = svg("path", {d: path(lanes.get(lid).shape), fill: "none", stroke: color, "stroke-width": width, "stroke-linecap": "round", "data-edge": edge, ...attrs});
      p.append(svg("title", {}, road.name + " · " + edge)); group.append(p);
    }
  }
  function drawRoutes() {
    const group = $("route-layer"); group.replaceChildren();
    for (const eid of c().routes.base) drawEdge(group, eid, colors.base, 5.5, {opacity: .72});
    for (const eid of c().routes.closure) {
      if (!c().routes.base.includes(eid)) drawEdge(group, eid, colors.closure, 6, {opacity: .9});
    }
    drawEdge(group, D.closedEdge, S.scenario === "closure" ? "#bd3549" : "#92588e", 9, {"stroke-dasharray": "9 4", "data-closure": S.scenario === "closure" ? "closed" : "open"});
    const closedRoad = roads.get(D.closedEdge), shape = lanes.get(closedRoad.lanes[0]).shape, mid = shape[Math.floor(shape.length / 2)];
    const annotation = svg("text", {x: mid[0], y: -mid[1] - 34, class: "map-label", "data-kind": "closure", "font-size": 15, "font-weight": 650, fill: S.scenario === "closure" ? "#9a233b" : "#784674", "paint-order": "stroke", stroke: "#fff", "stroke-width": 4, "text-anchor": "middle"},
      S.scenario === "closure" ? "× Cierre virtual" : "Enlace evaluado · abierto");
    group.append(annotation);
    // Identificación geográfica sin teselas ni etiquetas procedentes de otros mapas.
    for (const [eid, title] of [["-175606174", "35 Av. Sur"], ["-198404021", "Calle el Progreso"]]) {
      const l = lanes.get(roads.get(eid).lanes[0]), p = l.shape[0];
      group.append(svg("text", {x: p[0] + 7, y: -p[1] + 30, class: "map-label", "font-size": 12, fill: "#45605b", "paint-order": "stroke", stroke: "#f1f4ef", "stroke-width": 3}, title));
    }
    $("closure-legend").replaceChildren();
    const swatch = el("i", undefined, "swatch"); swatch.style.color = S.scenario === "closure" ? "#bd3549" : "#92588e";
    $("closure-legend").append(swatch, document.createTextNode(S.scenario === "closure" ? "Cerrado a passenger" : "Enlace evaluado, abierto"));
    drawSelection(); symbolScale();
  }
  function drawSelection() {
    $("selection-layer").replaceChildren();
    drawEdge($("selection-layer"), S.edge, "#133e36", 11, {opacity: .38, "pointer-events": "none"});
  }
  function signalPhase(timeline, time) {
    let lo = 0, hi = timeline.length - 1;
    while (lo < hi) { const mid = Math.ceil((lo + hi) / 2); if (timeline[mid][0] <= time) lo = mid; else hi = mid - 1; }
    return timeline[lo][1];
  }
  function renderFrame() {
    const row = c(), time = S.time;
    $("clock").textContent = n(time, 0) + " s"; $("time-slider").value = time;
    $("vehicle-layer").replaceChildren();
    const frame = row.frames ? row.frames[S.scenario][time] : null;
    if (frame) for (const [idx, x, y, speed] of frame) {
      const vid = D.vehicles[idx], focal = vid === "N_E.0007" || vid === "N_E.0013";
      const vehicle = svg("circle", {cx: x, cy: -y, r: focal ? 4.8 : 3.2, fill: colors[vid.split(".")[0]], stroke: "#fff", "stroke-width": .8, class: "vehicle", "data-vehicle": vid, "data-focal": String(focal)});
      vehicle.append(svg("title", {}, vid + " · " + n(speed) + " m/s · " + time + " s · FCD nativo"));
      $("vehicle-layer").append(vehicle);
    }
    for (const {connection, line} of signalPaths) {
      const program = D.geometry.programs[connection.tls];
      const phase = signalPhase(D.signals[String(row.offset)][connection.tls], time);
      const state = program.states[phase][connection.index];
      line.setAttribute("stroke", ({G: "#238451", g: "#67a77f", y: "#d59425", r: "#bd3549", o: "#87918c", O: "#87918c"})[state] || "#87918c");
      line.setAttribute("data-state", state); line.setAttribute("data-phase", phase);
      line.firstChild.textContent = "Señal virtual " + connection.tls + " · conexión " + connection.index + " · estado " + state + " · " + time + " s";
    }
    $("map-status").textContent = "350 enlaces · 18 programas virtuales · " + row.active[S.scenario][time] + " vehículos activos";
    $("animation-notice").textContent = frame
      ? "Posiciones FCD a " + time + " s · " + frame.length + " vehículos. Colores por movimiento; dos casos N_E con borde reforzado."
      : "Este par incluye agregados y señales. Su reproducción FCD no está incluida en el paquete; no se dibujan posiciones.";
    $("time-resolution").textContent = frame
      ? "Muestras nativas de 1 s, sin interpolación. Se muestran instantes de 0 a 1799 s."
      : "Señales y vehículos activos cada 1 s; estadísticas de enlace cada 60 s. Sin animación vehicular en este par.";
    symbolScale(); renderEdgeCurrent();
    for (const plot of [$("active-chart"), $("edge-chart")]) {
      const cursor = plot.querySelector("[data-cursor]");
      if (cursor) { const x = 42 + time / 1800 * Number(plot.dataset.plotWidth); cursor.setAttribute("x1", x); cursor.setAttribute("x2", x); }
    }
  }
  function pause() {
    S.playing = false; $("play").textContent = "Reproducir"; $("play").setAttribute("aria-pressed", "false");
  }
  let previous = 0, accrued = 0;
  function animate(now) {
    if (S.playing) {
      accrued += Math.min(now - previous, 300) * S.speed / 1000;
      if (accrued >= 1) {
        const steps = Math.floor(accrued); accrued -= steps;
        S.time = Math.min(1799, S.time + steps); renderFrame();
        if (S.time === 1799) pause();
      }
    }
    previous = now; requestAnimationFrame(animate);
  }
  $("play").onclick = () => {
    if (S.playing) pause();
    else { if (S.time === 1799) S.time = 0; accrued = 0; S.playing = true; $("play").textContent = "Pausar"; $("play").setAttribute("aria-pressed", "true"); }
  };
  function seek(time) { pause(); S.time = Math.max(0, Math.min(1799, Math.round(Number(time)))); renderFrame(); }
  $("time-slider").oninput = event => seek(event.target.value);
  $("back").onclick = () => seek(S.time - 1); $("forward").onclick = () => seek(S.time + 1);
  $("speed").onchange = event => { S.speed = Number(event.target.value); };

  function chart(id, base, closure, unit, period = 1) {
    const root = $(id), width = Math.max(240, root.clientWidth || 600), right = width - 20, plotWidth = right - 42;
    root.replaceChildren(); root.setAttribute("viewBox", "0 0 " + width + " 160"); root.dataset.plotWidth = plotWidth;
    const max = Math.max(1, ...base, ...closure), y = value => 124 - value / max * 103, x = i => 42 + i * period / 1800 * plotWidth;
    for (const fraction of [0, .5, 1]) {
      const yy = y(max * fraction);
      root.append(svg("line", {x1: 42, x2: right, y1: yy, y2: yy, stroke: "#e5eae6"}));
      root.append(svg("text", {x: 35, y: yy + 4, "text-anchor": "end", "font-size": 12, fill: "#5b6d71"}, n(max * fraction, max < 5 ? 1 : 0)));
    }
    root.append(svg("text", {x: 42, y: 12, "font-size": 12, fill: "#5b6d71"}, unit));
    for (const t of [0, 600, 1200, 1800]) root.append(svg("text", {x: 42 + t / 1800 * plotWidth, y: 146, "text-anchor": t === 1800 ? "end" : "middle", "font-size": 12, fill: "#5b6d71"}, t + " s"));
    for (const [values, color] of [[base, colors.base], [closure, colors.closure]]) {
      const points = [];
      values.forEach((value, i) => {
        points.push([x(i), y(value)]);
        if (period > 1) points.push([x(i + 1), y(value)]);
      });
      root.append(svg("polyline", {points: points.map(p => p.join(",")).join(" "), stroke: color, "stroke-width": 1.8, fill: "none", "stroke-linejoin": "round"}));
    }
    root.append(svg("line", {x1: 42, x2: 42, y1: 18, y2: 124, stroke: "#677d74", "stroke-dasharray": "3 3", "data-cursor": "true"}));
  }
  function metrics() {
    const row = c(), m = row.metrics[S.scenario], delta = row.metrics.closure.duration_s.total - row.metrics.base.duration_s.total;
    $("stat-completed").textContent = m.completed + " / " + m.requested;
    $("stat-pending").textContent = m.pending + " pendientes · " + m.rejected + " rechazos";
    $("stat-total").textContent = n(m.duration_s.total, 0) + " s";
    $("stat-delta").textContent = "Δ cierre − base: " + signed(delta, 0) + " s (" + signed(100 * delta / row.metrics.base.duration_s.total) + " %)";
    $("stat-mean").textContent = n(m.duration_s.mean) + " s";
    $("stat-length").textContent = "Longitud media: " + n(m.route_length_m.mean) + " m";
    $("metric-body").replaceChildren();
    const quantities = [
      ["Tiempo total (s)", "duration_s", "total"], ["Recorrido medio (s)", "duration_s", "mean"],
      ["waitingTime medio (s)", "waiting_time_s", "mean"], ["timeLoss medio (s)", "time_loss_s", "mean"],
      ["Longitud media (m)", "route_length_m", "mean"], ["Espera de salida media (s)", "depart_delay_s", "mean"]
    ];
    for (const [title, key, part] of quantities) {
      const a = row.metrics.base[key][part], b = row.metrics.closure[key][part];
      tableRow($("metric-body"), [title, n(a), n(b), signed(b - a)], [3]);
    }
    tableRow($("metric-body"), ["Rutas modificadas", "—", row.comparison.system.routes_changed, "—"]);
    chart("active-chart", row.active.base, row.active.closure, "vehículos activos");
    $("movement-body").replaceChildren();
    for (const [stream, r] of Object.entries(row.comparison.by_stream)) tableRow($("movement-body"), [
      stream + " · " + D.movementDescriptions[stream], r.paired_completed, n(r.duration_s.base_mean), n(r.duration_s.closure_mean), signed(r.duration_s.delta_mean),
      signed(r.waiting_time_s.delta_mean), signed(r.time_loss_s.delta_mean), signed(r.route_length_m.delta_mean)
    ], [4, 5, 6, 7]);
    $("NE-cases").replaceChildren();
    for (const r of row.NE) {
      const article = el("article"); article.append(el("h4", r.id), el("strong", signed(r.delta_duration_s, 0) + " s de recorrido"));
      article.append(el("p", "Δ waitingTime " + signed(r.delta_waiting_time_s, 0) + " s · Δ timeLoss " + signed(r.delta_time_loss_s) + " s."));
      article.append(el("p", "Primera muestra en aproximación: base " + n(r.base_first_approach_sample_s, 0) + " s (" + r.base_state_at_approach_sample + "), cierre " + n(r.closure_first_approach_sample_s, 0) + " s (" + r.closure_state_at_approach_sample + ")."));
      article.append(el("p", "Salida del enlace de aproximación: " + n(r.base_focal_incoming_exit_s, 0) + " → " + n(r.closure_focal_incoming_exit_s, 0) + " s. Muestras detenido en cierre: " + r.closure_halt_samples_approach + "."));
      $("NE-cases").append(article);
    }
    $("jump-NE").onclick = () => { seek(Number(row.NE[0][S.scenario + "_first_approach_sample_s"])); $("road-map").scrollIntoView({block: "center", behavior: "smooth"}); };
  }
  function selectEdge(eid) {
    if (!roads.has(eid)) return;
    S.edge = eid; $("edge-select").value = eid;
    document.querySelectorAll("[data-edge-shortcut]").forEach(button => button.classList.toggle("is-selected", button.dataset.edgeShortcut === eid));
    const road = roads.get(eid), total = c().edgeTotals[eid];
    $("edge-attributes").textContent = road.name + " · " + eid + " · " + road.lanes.length + " carriles · límite SUMO " + n(road.speed * 3.6, 0) + " km/h. " +
      (road.defaults.length ? "Campos con valor predeterminado: " + road.defaults.join(", ") + "." : "Sin valores predeterminados anotados para carriles/velocidad; no implica calibración real.");
    const table = el("table"), body = el("tbody");
    tableRow(body, ["Totales en [0,1800) s", "Base", "Cierre"]);
    tableRow(body, ["Entradas (veh)", total[0], total[1]]);
    tableRow(body, ["Ocupación máxima de intervalo (%)", n(total[2]), n(total[3])]);
    tableRow(body, ["Presencia media en 1800 s (veh)", n(total[4]), n(total[5])]);
    table.append(body); $("edge-totals").replaceChildren(table);
    const intervals = c().edgeIntervals[eid];
    $("edge-chart").toggleAttribute("hidden", !intervals);
    if (!intervals) $("edge-chart").replaceChildren();
    if (intervals) chart("edge-chart", intervals.base.map(x => x[0]), intervals.closure.map(x => x[0]), "flujo de entrada (veh/h)", 60);
    drawSelection(); renderEdgeCurrent();
  }
  function renderEdgeCurrent() {
    const rows = c().edgeIntervals[S.edge], interval = Math.floor(S.time / 60);
    $("edge-interval-label").textContent = rows ? "Intervalo [" + interval * 60 + ", " + (interval + 1) * 60 + ") s · base / cierre" : "Este enlace tiene totales; su serie temporal no se incluye en el paquete.";
    $("edge-current").replaceChildren();
    if (!rows) return;
    const a = rows.base[interval], b = rows.closure[interval];
    $("edge-current").append(el("p", "Flujo: " + n(a[0], 0) + " / " + n(b[0], 0) + " veh/h. Ocupación: " + n(a[1]) + " / " + n(b[1]) + " %."),
      el("p", "Vehículos presentes, media de intervalo: " + n(a[2]) + " / " + n(b[2]) + " veh. El porcentaje mide espacio ocupado, no un conteo."));
  }
  for (const row of Object.values(D.cases)) {
    const option = el("option", label(row) + (row.animated ? " · FCD" : " · agregados")); option.value = row.id; $("case-select").append(option);
  }
  for (const road of [...roads.values()].sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id))) {
    const option = el("option", road.name + " · " + road.id); option.value = road.id; $("edge-select").append(option);
  }
  const shortNames = ["Cierre Roosevelt", "35 Av. Sur", "El Progreso", "Aproximación N_E", "Retorno a Roosevelt"];
  D.interestEdges.forEach((eid, i) => {
    const button = el("button", shortNames[i]); button.type = "button"; button.dataset.edgeShortcut = eid;
    button.onclick = () => selectEdge(eid); $("edge-shortcuts").append(button);
  });
  for (const stream of ["W_E", "E_W", "N_W", "E_N", "N_E", "W_S"]) {
    const span = el("span"), dot = el("i", undefined, "dot"); span.title = D.movementDescriptions[stream]; dot.style.background = colors[stream]; span.append(dot, document.createTextNode(stream)); $("movement-legend").append(span);
  }
  function selectCase(id) {
    if (!D.cases[id]) return;
    pause(); S.caseId = id; $("case-select").value = id;
    $("selection-detail").textContent = "SIM-005 · " + label(c()) + " · semilla SUMO 42 · mismos 150 viajes por par · cierre [0,1800) s. " +
      (c().schedule === "original" ? "Calendario original." : "Salidas con perturbación entera acotada ±15 s; semilla de calendario " + c().schedule.slice(-3) + ".");
    $("scenario-badge").textContent = S.scenario === "base" ? "Base" : "Cierre virtual";
    $("scenario-badge").classList.toggle("intervened", S.scenario === "closure");
    document.querySelectorAll("[data-scenario]").forEach(button => button.setAttribute("aria-pressed", String(button.dataset.scenario === S.scenario)));
    document.querySelectorAll("[data-case]").forEach(button => button.classList.toggle("selected", button.dataset.case === id));
    metrics(); drawRoutes(); selectEdge(S.edge); renderFrame();
  }
  $("case-select").onchange = event => selectCase(event.target.value);
  $("edge-select").onchange = event => selectEdge(event.target.value);
  document.querySelectorAll("[data-scenario]").forEach(button => button.onclick = () => { S.scenario = button.dataset.scenario; selectCase(S.caseId); });

  const summary = D.summary, changes = summary.total_duration_change_s;
  for (const [title, value, detail] of [
    ["Pares comparados", "15", summary.higher_total_travel_time + " aumentan · " + summary.lower_total_travel_time + " disminuye"],
    ["Cambio de tiempo total", signed(changes.min, 0) + " a " + signed(changes.max, 0) + " s", "Media " + signed(changes.mean) + " s · mediana " + signed(changes.median, 0) + " s"],
    ["Movimiento W_E", "15 / 15", "Medianas positivas; +14 a +16 s por vehículo"]
  ]) {
    const article = el("article", undefined, "stat"); article.append(el("span", title), el("strong", value), el("small", detail)); $("sensitivity-stats").append(article);
  }
  for (const schedule of ["original", "jitter101", "jitter102", "jitter103", "jitter104"]) {
    const tr = el("tr"); tr.append(el("td", name(schedule)));
    for (const offset of [0, 30, 60]) {
      const row = D.matrix.find(r => r.schedule === schedule && r.offset === offset), td = el("td"), button = el("button", signed(row.delta, 0) + " s");
      button.type = "button"; button.dataset.case = row.id; button.setAttribute("aria-label", label(row) + ": " + signed(row.delta, 0) + " segundos, abrir comparación");
      button.append(el("small", signed(row.pct) + " %"));
      button.style.background = row.delta < 0 ? "#dbeaf5" : "rgba(177,52,67," + (.05 + row.delta / changes.max * .20) + ")";
      button.style.color = row.delta < 0 ? colors.base : "#8e3341";
      button.onclick = () => { selectCase(row.id); setTab("explore"); $("case-select").focus(); };
      td.append(button); tr.append(td);
    }
    $("matrix-body").append(tr);
  }
  $("sensitivity-conclusion").textContent = "Los 150 viajes terminan en todos los pares, sin colisiones ni teletransportes. El mayor aumento absoluto es Original/0 (+405 s, +2,03 %); J103/0 reduce 19 s el total. Los 45 W_E se desvían en todos los cierres y su longitud aumenta 105,55 m por viaje. Los casos N_E.0007 y N_E.0013 superan +60 s solamente en Original/0 (1 de 15 pares cada uno).";

  function sheet(code) {
    const row = D.catalog.find(x => x.id === code), target = $("sheet-content"); target.replaceChildren();
    target.append(el("p", row.id + " · versión " + row.sheet_version, "eyebrow"), el("h2", row.name), el("p", row.date + " · America/Bogota · SUMO " + row.SUMO_version + " · " + row.type, "muted"));
    for (const [title, text] of [["Objetivo", row.question], ["Intervención", row.intervention], ["Condiciones conservadas", row.constants]]) {
      const section = el("section", undefined, "sheet-section"); section.append(el("h3", title), el("p", text)); target.append(section);
    }
    const config = el("section", undefined, "sheet-section"); config.append(el("h3", "Configuración"));
    for (const [key, value] of Object.entries(row.configuration)) config.append(el("p", key + ": " + value)); target.append(config);
    const result = el("section", undefined, "sheet-section"), table = el("table"), body = el("tbody");
    result.append(el("h3", "Resultados")); D.metricLabels[code].forEach(([title, value]) => tableRow(body, [title, n(value)]));
    table.append(body); result.append(table); target.append(result);
    const interpretation = el("section", undefined, "sheet-section");
    interpretation.append(el("h3", "Interpretación y límites"), el("p", row.interpretation), el("p", row.limitations),
      el("p", "Evidencias disponibles: " + row.inventory.FCD.length + " FCD y " + row.inventory.TLS.length + " registros de señales.")); target.append(interpretation);
    const reproduction = el("section", undefined, "sheet-section");
    reproduction.append(el("h3", "Reproducción"), el("code", row.command), el("p", "Manifiesto SHA-256: " + row.manifest_sha256), link("Abrir ficha Markdown ↗", "../../" + row.sheet),
      document.createTextNode(" · "), link("Manifiesto de origen ↗", "../../" + row.manifest));
    target.append(reproduction); $("sheet-dialog").showModal();
  }
  for (const row of D.catalog) {
    const card = el("article", undefined, "panel catalog-card"); card.append(el("p", row.id + " / " + row.date, "eyebrow"), el("h3", row.name), el("p", row.question));
    const r = row.results;
    const result = row.id === "SIM-005" ? "15 pares · Δ " + signed(r.delta_min_s, 0) + " a " + signed(r.delta_max_s, 0) + " s"
      : row.id === "SIM-004" ? signed(r.delta_total_s, 0) + " s · " + signed(r.delta_pct) + " %"
      : r.completed + " / " + r.requested + " viajes completados";
    card.append(el("p", result, "card-result"), el("p", row.interpretation));
    const button = el("button", "Ver ficha completa ↗"); button.type = "button"; button.dataset.sheet = row.id; button.onclick = () => sheet(row.id); card.append(button); $("catalog-grid").append(card);
  }
  $("current-sheet").onclick = () => sheet("SIM-005");
  $("close-sheet").onclick = () => $("sheet-dialog").close();
  $("sheet-dialog").addEventListener("click", event => {
    const rect = $("sheet-dialog").getBoundingClientRect();
    if (event.target === $("sheet-dialog") && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) $("sheet-dialog").close();
  });
  for (const source of D.sources) {
    const row = el("tr"), file = el("td"); file.append(link(source.path, "../../" + source.path));
    row.append(file, el("td", source.roles.join(", ")), el("td", source.sha256.slice(0, 16) + "…")); $("source-body").append(row);
  }
  selectCase(S.caseId);
  new ResizeObserver(symbolScale).observe($("road-map"));
  let resizeFrame;
  window.addEventListener("resize", () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      if (S.tab === "explore") { metrics(); selectEdge(S.edge); renderFrame(); }
    });
  });
  requestAnimationFrame(animate);
  // Solo lectura: facilita auditoría de la selección sin acceder a perfiles del usuario.
  window.DigitalTwinsViewer = Object.freeze({getState: () => ({...S}), version: D.schema});
})();
