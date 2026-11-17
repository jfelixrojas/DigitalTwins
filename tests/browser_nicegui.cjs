/* Chrome real; solo loopback permitido, sin instalaciones de paquetes de prueba. */
const {chromium} = require("playwright");
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const out = path.resolve(process.env.DT_QA_OUTPUT || path.join(root, "outputs/intervention008/regression007/browser"));
assert(out.startsWith(path.join(root, "outputs/intervention008/")), "Keep historical007 evidence immutable");
const url = process.env.DT_NICEGUI_URL || "http://127.0.0.1:8087/";
const origin = new URL(url).origin;
const hash = file => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
for (const p of ["profile", "tmp", "downloads"]) fs.mkdirSync(path.join(out, p), {recursive: true});
(async () => {
  const context = await chromium.launchPersistentContext(path.join(out, "profile"), {
    executablePath: process.env.DT_CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    headless: true, viewport: {width: 1600, height: 1120},
    downloadsPath: path.join(out, "downloads"), env: {...process.env, TMPDIR: path.join(out, "tmp")},
    args: ["--no-first-run", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--no-default-browser-check"]
  });
  const page = context.pages()[0], errors = [], external = [], requests = [], sockets = [], checks = [];
  let appMessagesSent = 0; const socketMessages = [], receivedMessages = [];
  const check = (name, value) => { assert(value, name); checks.push(name); };
  await context.route("**/*", route => {
    const request = route.request(), target = new URL(request.url());
    if (target.protocol.startsWith("http") && target.origin !== origin) {
      external.push(target.href); return route.abort("internetdisabled");
    }
    return route.continue();
  });
  page.on("request", request => requests.push(request.url()));
  page.on("pageerror", error => errors.push(String(error)));
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  page.on("websocket", socket => {
    sockets.push(socket.url());
    socket.on("framesent", event => { if (String(event.payload).startsWith("42")) { appMessagesSent++; socketMessages.push(String(event.payload)); } });
    socket.on("framereceived", event => { if (String(event.payload).startsWith("42")) receivedMessages.push(String(event.payload)); });
  });
  const dataPath = path.join(root, "outputs/nicegui_prototype/data.json");
  const dataHash = hash(dataPath), data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
  const state = () => page.evaluate(() => DT007.getState());
  const inspect = () => page.evaluate(() => DT007.inspect());
  async function seek(time) {
    await page.locator("#time-slider").evaluate((node, t) => { node.value = t; node.dispatchEvent(new Event("input", {bubbles: true})); }, time);
  }
  function fcdMatches(snapshot) {
    const expected = data.frames[snapshot.state.scenario][snapshot.state.time];
    const actual = new Map(snapshot.vehicles.map(v => [v.id, v]));
    return expected.length === actual.size && expected.every(([idx, lat, lon]) => {
      const vehicle = actual.get(data.vehicles[idx]);
      return vehicle && vehicle.lat === lat && vehicle.lon === lon && vehicle.tooltip.includes(data.vehicles[idx]);
    });
  }
  try {
    await page.goto(url, {waitUntil: "domcontentloaded"});
    await page.waitForFunction(() => window.DT007?.getState().ready, {timeout: 30000});
    await page.waitForTimeout(300);
    let snapshot = await inspect();
    check("Server starts on loopback", new URL(page.url()).hostname === "127.0.0.1");
    check("350 source roads loaded", snapshot.roadCount === 350);
    check("No default or external tile layers", snapshot.tileLayers === 0);
    check("Initial state base t0 paused", snapshot.state.scenario === "base" && snapshot.state.time === 0 && !snapshot.state.playing);
    check("Initial native FCD positions and IDs", fcdMatches(snapshot));
    check("Synthetic data notice visible", await page.locator(".synthetic-badge").isVisible());
    check("Base metrics 132.90 and19935", (await page.locator("#duration-mean").innerText()).includes("132.90") && (await page.locator("#duration-total").innerText()).includes("19,935"));
    check("Completed final horizon explicit", (await page.locator(".result-scope").innerText()).includes("1800"));
    check("Evaluated edge open in base", snapshot.closedEdge === "1257993561#5" && snapshot.closedLabel.includes("abierto"));
    check("ECharts has two OD series", snapshot.odSeries.length === 2 && snapshot.odSeries[0].data.length === 6);
    await page.screenshot({path: path.join(out, "01_initial_desktop.png"), fullPage: true});
    await seek(480); snapshot = await inspect();
    check("Base t480 native FCD", fcdMatches(snapshot) && snapshot.vehicles.length > 0);
    check("Time clock active count and completed synchronized", snapshot.active === data.active.base[480] && snapshot.arrived === data.arrived.base[480] && (await page.locator("#clock").innerText()).includes("480"));
    await page.screenshot({path: path.join(out, "02_base_vehicles.png"), fullPage: true});
    await page.locator("#scenario-closure").click(); snapshot = await inspect();
    check("Scenario switch preserves time and pauses", snapshot.state.time === 480 && snapshot.state.scenario === "closure" && !snapshot.state.playing);
    check("Closure positions and IDs match native FCD", fcdMatches(snapshot));
    check("Closure edge and label correct", snapshot.closedLabel.includes("Cierre virtual") && (await page.locator("#closure-legend").innerText()).includes("Cerrado"));
    check("Closure metrics 135.60 and20340", (await page.locator("#duration-mean").innerText()).includes("135.60") && (await page.locator("#duration-total").innerText()).includes("20,340"));
    check("waitingTime separate from timeLoss", (await page.locator("#waiting-mean").innerText()).includes("30.32") && (await page.locator("#loss-mean").innerText()).includes("50.53"));
    check("Difference remains +405s", (await page.locator("#impact-total").innerText()).includes("+405"));
    await page.screenshot({path: path.join(out, "03_closure_desktop.png"), fullPage: true});
    await page.locator(".simulation-panel").screenshot({path: path.join(out, "04_indicators.png")});
    await page.locator("#chart-delta").click(); snapshot = await inspect();
    check("OD differences are native paired means", snapshot.odSeries.length === 1 && snapshot.odSeries[0].data.every((v, i) => v.value === data.comparison.by_stream[["W_E","E_W","N_W","E_N","N_E","W_S"][i]].duration_s.delta_mean));
    await page.locator("#chart-paired").click();
    check("Return to paired comparison", (await inspect()).odSeries.length === 2);
    await page.locator("#seek-time").fill("836"); await page.locator("#seek-form button").click();
    check("Explicit numeric seek", (await state()).time === 836 && fcdMatches(await inspect()));
    await page.locator("#advance").click(); check("Advance ten seconds", (await state()).time === 846);
    await page.locator("#reset").click(); check("Restart retains scenario and pauses", (await state()).time === 0 && (await state()).scenario === "closure" && !(await state()).playing);
    await seek(400); await page.locator("#speed").selectOption("30"); await page.waitForTimeout(150);
    const beforeMessages = appMessagesSent;
    const beforeReceived = receivedMessages.length;
    await page.locator("#play").click(); await page.waitForTimeout(2500); await page.locator("#play").click();
    snapshot = await inspect(); const paused = snapshot.state.time;
    check("Playback speed30 advances local time", paused >= 460 && paused <= 490);
    check("Playback frames remain native", fcdMatches(snapshot));
    const playbackTransport = {sent: socketMessages.slice(beforeMessages), received: receivedMessages.slice(beforeReceived)};
    fs.writeFileSync(path.join(out, "playback_socket_messages.json"), JSON.stringify(playbackTransport, null, 2));
    check("No Python updates per frame or vehicle (transport acks only)",
      playbackTransport.sent.every(m => JSON.parse(m.slice(2))[0] === "ack") &&
      playbackTransport.received.every(m => JSON.parse(m.slice(2))[0] === "ack"));
    await page.waitForTimeout(200); check("Pause holds time", (await state()).time === paused);
    check("Finite rendering performance diagnostics", Number.isFinite(snapshot.diagnostics.renderP95_ms));
    // Otro cliente conserva su propia selección, tiempo y controles.
    const other = await context.newPage();
    await other.goto(url); await other.waitForFunction(() => window.DT007?.getState().ready);
    const otherState = await other.evaluate(() => DT007.getState());
    check("Clients do not share playback state", otherState.scenario === "base" && otherState.time === 0 && !otherState.playing && (await state()).time === paused);
    await other.close();
    await page.locator("#scenario-base").click(); await seek(480);
    check("Base restored without closure metrics leak", (await page.locator("#duration-total").innerText()).includes("19,935") && fcdMatches(await inspect()));
    const pixel = await page.evaluate(() => {
      const node = document.querySelector(".corridor-map"), leaflet = getElement(node).map;
      const r = node.getBoundingClientRect();
      return {zoom: leaflet.getZoom(), x: r.x, y: r.y, width: r.width, height: r.height};
    });
    await page.locator(".primary-map .leaflet-control-zoom-in").click();
    await page.waitForFunction(value => getElement(document.querySelector(".corridor-map")).map.getZoom() > value, pixel.zoom, {timeout: 3000});
    check("Leaflet zoom works", await page.evaluate(() => getElement(document.querySelector(".corridor-map")).map.getZoom()) > pixel.zoom);
    await page.waitForTimeout(350);
    await page.locator(".primary-map .leaflet-control-zoom-out").click();
    await page.waitForFunction(value => getElement(document.querySelector(".corridor-map")).map.getZoom() === value, pixel.zoom, {timeout: 3000});
    await page.waitForTimeout(300);
    const click = await page.evaluate(road => {
      const node = document.querySelector(".corridor-map"), leaflet = getElement(node).map, rect = node.getBoundingClientRect();
      const line = road.latlngs[0]; let best = [line[0], line[1]], size = -1;
      for (let i = 1; i < line.length; i++) {
        const d = Math.hypot(line[i][0] - line[i-1][0], line[i][1] - line[i-1][1]);
        if (d > size) { best = [line[i-1], line[i]]; size = d; }
      }
      const mid = [(best[0][0] + best[1][0]) / 2, (best[0][1] + best[1][1]) / 2];
      // A escala de enlace, los dos sentidos paralelos dejan de compartir píxel.
      leaflet.setView(mid, 19, {animate: false});
      const p = leaflet.latLngToContainerPoint(mid);
      return {x: rect.left + p.x, y: rect.top + p.y};
    }, data.roads.find(r => r.id === "-175606174"));
    await page.mouse.click(click.x, click.y);
    fs.writeFileSync(path.join(out, "selection_probe.json"), JSON.stringify({target: "-175606174",selected: (await state()).selectedEdge,click}, null, 2));
    check("Click selects source road", (await state()).selectedEdge === "-175606174");
    const centerBefore = await page.evaluate(() => getElement(document.querySelector(".corridor-map")).map.getCenter().toString());
    await page.mouse.move(pixel.x + pixel.width / 2, pixel.y + pixel.height / 3);
    await page.mouse.down(); await page.mouse.move(pixel.x + pixel.width / 2 + 55, pixel.y + pixel.height / 3 + 35, {steps: 8}); await page.mouse.up();
    check("Leaflet pan works", await page.evaluate(() => getElement(document.querySelector(".corridor-map")).map.getCenter().toString()) !== centerBefore);
    await page.locator("#fit-map").click();
    check("Map reframe preserves selected run and time", (await state()).scenario === "base" && (await state()).time === 480);
    await page.locator("#experiment summary").click();
    check("Traceability includes objective and limits", (await page.locator(".experiment-grid").innerText()).includes("semilla 42") && (await page.locator(".experiment-grid").innerText()).includes("sin calibración"));
    const sheet = await page.request.get(origin + "/experiment/SIM-005.md");
    check("Original Markdown ficha served locally", sheet.ok() && (await sheet.text()).includes("# SIM-005"));
    await page.locator("#experiment summary").click();
    for (const width of [1024, 768, 390, 320]) {
      await page.setViewportSize({width, height: 900}); await page.waitForTimeout(150);
      const layout = await page.evaluate(() => ({width: innerWidth, scroll: document.documentElement.scrollWidth,
        bad: [...document.querySelectorAll("main *")].filter(n => n.getBoundingClientRect().width && n.getBoundingClientRect().right > innerWidth + 1).map(n => ({tag:n.tagName,cls:typeof n.className==="string"?n.className:"",id:n.id,right:n.getBoundingClientRect().right})).slice(0,15)}));
      if (layout.scroll > width) fs.writeFileSync(path.join(out,"overflow.json"),JSON.stringify(layout,null,2));
      check("Responsive page no overflow at" + width, layout.scroll <= width);
    }
    await page.setViewportSize({width: 390, height: 900});
    await page.locator("#indicators-panel").evaluate(node => { node.open = true; });
    await page.locator("#scenario-closure").click(); await seek(485);
    await page.locator("#fit-map").click();
    await page.screenshot({path: path.join(out, "05_mobile_closure.png"), fullPage: true});
    await page.locator(".primary-map").screenshot({path: path.join(out, "06_mobile_map.png")});
    await seek(1799); check("Final frame empty and all completed", (await inspect()).vehicles.length === 0 && (await inspect()).arrived === 150);
    await page.locator("#advance").click(); check("Horizon cannot be exceeded", (await state()).time === 1799);
    await page.locator("#reset").click(); check("Reset from horizon returns t0", (await state()).time === 0 && fcdMatches(await inspect()));
    check("Source bundle unchanged during UI test", hash(dataPath) === dataHash);
    check("All requests stay on loopback", external.length === 0 && requests.every(r => !r.startsWith("http") || new URL(r).origin === origin));
    check("Websocket remains on loopback", sockets.length >= 1 && sockets.every(r => new URL(r).hostname === "127.0.0.1"));
    check("No JavaScript or console errors", errors.length === 0);
    check("No error panel", await page.locator("#runtime-error").isHidden());
    const final = {pass: true, checked_at_utc: new Date().toISOString(), browser: context.browser().version(),
      mode: "HTTP loopback only; every nonlocal request blocked; fresh test profile; no Internet required",
      checks, errors, external_requests: external, local_requests: requests.length, socket_urls: sockets,
      data_sha256: dataHash, qa_script_sha256: hash(__filename), diagnostics: (await inspect()).diagnostics};
    fs.writeFileSync(path.join(out, "validation.json"), JSON.stringify(final, null, 2) + "\n");
    console.log(JSON.stringify({pass: true, checks: checks.length, local_requests: requests.length, external_requests: external.length, diagnostics: final.diagnostics}));
  } catch (error) {
    await page.screenshot({path: path.join(out, "failure.png"), fullPage: true}).catch(() => {});
    fs.writeFileSync(path.join(out, "validation.json"), JSON.stringify({pass: false, error: String(error), checks, errors, external_requests: external}, null, 2) + "\n");
    throw error;
  } finally { await context.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
