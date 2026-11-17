/* Modelo de presentación sin DOM: reloj único, muestras nativas y estados por ID. */
((root) => {
  "use strict";
  class ReplayClock {
    constructor(last = 1799) { this.last = last; this.time = 0; this.speed = 5; this.playing = false; this.fraction = 0; }
    pause() { this.playing = false; }
    seek(value) {
      if (!Number.isFinite(Number(value))) return false;
      this.pause(); this.fraction = 0; this.time = Math.max(0, Math.min(this.last, Math.round(Number(value)))); return true;
    }
    play() { if (this.time === this.last) this.time = 0; this.fraction = 0; this.playing = true; }
    tick(milliseconds) {
      if (!this.playing) return false;
      this.fraction += Math.max(0, Math.min(250, milliseconds)) / 1000 * this.speed;
      const steps = Math.floor(this.fraction);
      if (!steps) return false;
      this.fraction -= steps; this.time = Math.min(this.last, this.time + steps);
      if (this.time === this.last) this.pause();
      return true;
    }
  }
  function framePair(data, time) {
    if (!Number.isInteger(time) || time < 0 || time > data.last_time_s) throw new Error("Instante FCD inválido");
    const base = data.frames.base[time], closure = data.frames.closure[time];
    if (!base || !closure) throw new Error("Falta una muestra del par FCD");
    return Object.freeze({time, base, closure});
  }
  function vehicleState(data, catalog, id, scenario, pair) {
    const info = catalog.vehicles[id]?.[scenario];
    if (!info) throw new Error("ID ajeno al experimento");
    const index = data.vehicles.indexOf(id), sample = pair[scenario].find(row => row[0] === index);
    if (sample) return {state: "active", sample, info};
    if (pair.time < info.depart_s) return {state: "not-departed", sample: null, info};
    if (pair.time >= info.arrival_s) return {state: "finished", sample: null, info};
    return {state: "no-sample", sample: null, info};
  }
  function routeFor(data, catalog, id, scenario) {
    if (!id) return data.routes[scenario];
    if (!catalog.vehicles[id]?.[scenario]) throw new Error("Ruta de ID no disponible");
    return catalog.vehicles[id][scenario].route;
  }
  const api = Object.freeze({ReplayClock, framePair, vehicleState, routeFor});
  root.DTReplay = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
