const {test} = require("node:test");
const assert = require("node:assert/strict");
const {ReplayClock, framePair, vehicleState, routeFor} = require("../src/digitaltwins/nicegui_app/assets/replay-model.js");
const data = {last_time_s: 3, vehicles: ["same"],
  frames: {base: [[], [[0,13.7,-89.2,2]], [[0,13.8,-89.1,3]], []],
           closure: [[], [[0,13.6,-89.3,0]], [], []]}, routes: {base:["a","b"],closure:["a","c","b"]}};
const catalog = {vehicles: {same: {base:{depart_s:1,arrival_s:3,route:["a","b"]}, closure:{depart_s:1,arrival_s:2,route:["a","c","b"]}}}};

test("un reloj avanza por segundos nativos y conserva fracciones", () => {
  const clock = new ReplayClock(); clock.play(); assert.equal(clock.tick(100), false);
  assert.equal(clock.tick(100), true); assert.equal(clock.time, 1);
});
test("pausa y búsqueda no acumulan tiempo oculto", () => {
  const clock = new ReplayClock(); clock.play(); clock.tick(50); clock.seek(8);
  assert.equal(clock.playing, false); clock.tick(200); assert.equal(clock.time, 8);
  clock.play(); clock.tick(200); assert.equal(clock.time, 9);
});
test("el horizonte detiene y reiniciar desde el final vuelve a cero", () => {
  const clock = new ReplayClock(2); clock.speed=30; clock.play(); clock.tick(250);
  assert.equal(clock.time,2); assert.equal(clock.playing,false); clock.play(); assert.equal(clock.time,0);
});
test("una pausa larga de navegador no extrapola posiciones", () => {
  const clock = new ReplayClock(); clock.speed=30; clock.play(); clock.tick(10000);
  assert.equal(clock.time,7); assert(Number.isInteger(clock.time));
});
test("la búsqueda limita el intervalo y rechaza números no finitos", () => {
  const clock = new ReplayClock(); clock.seek(-10); assert.equal(clock.time,0);
  clock.seek(9999); assert.equal(clock.time,1799); assert.equal(clock.seek(NaN),false);
});
test("un snapshot inmutable contiene los dos escenarios en el mismo segundo", () => {
  const pair=framePair(data,1);
  assert.equal(pair.time,1); assert(Object.isFrozen(pair));
  assert.strictEqual(pair.base,data.frames.base[1]); assert.strictEqual(pair.closure,data.frames.closure[1]);
  assert.notDeepEqual(pair.base,pair.closure);
});
test("se rechazan instantes fraccionarios o ausentes sin interpolarlos", () => {
  for(const t of [-1,.5,4]) assert.throws(()=>framePair(data,t));
});
test("el mismo ID retiene sus posiciones diferentes y velocidades nativas", () => {
  const pair=framePair(data,1), a=vehicleState(data,catalog,"same","base",pair), b=vehicleState(data,catalog,"same","closure",pair);
  assert.deepEqual(a.sample,[0,13.7,-89.2,2]); assert.deepEqual(b.sample,[0,13.6,-89.3,0]);
});
test("salida, llegada y ausencia se determinan con registros individuales", () => {
  assert.equal(vehicleState(data,catalog,"same","base",framePair(data,0)).state,"not-departed");
  assert.equal(vehicleState(data,catalog,"same","closure",framePair(data,2)).state,"finished");
  const modified={vehicles:{same:{base:{depart_s:0,arrival_s:9}}}};
  const gap=vehicleState(data,modified,"same","base",framePair(data,0));
  assert.equal(gap.state,"no-sample"); assert.equal(gap.sample,null);
});
test("las rutas conservan el orden ejecutado y se rechazan IDs inventados", () => {
  assert.strictEqual(routeFor(data,catalog,"same","closure"),catalog.vehicles.same.closure.route);
  assert.strictEqual(routeFor(data,catalog,"","base"),data.routes.base);
  assert.throws(()=>routeFor(data,catalog,"wrong","base"));
});
