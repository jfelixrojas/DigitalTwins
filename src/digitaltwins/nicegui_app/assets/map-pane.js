/* Una instancia Leaflet por panel; ningún panel posee un temporizador. */
(() => {
  "use strict";
  const COLORS = {base: "#23685b", closure: "#b86332", closed: "#a33549", selected: "#e5b237"};
  const escape = value => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
  const fmt = value => new Intl.NumberFormat("es-SV", {maximumFractionDigits: 2, minimumFractionDigits: 2}).format(value);
  class MapPane {
    constructor(map, data, catalog, scenario, callbacks) {
      this.map = map; this.data = data; this.catalog = catalog; this.scenario = scenario; this.callbacks = callbacks;
      this.roads = new Map(); this.markers = new Map(); this.time = null; this.selectedVehicle = "";
      map.eachLayer(layer => { if (layer instanceof L.TileLayer) throw new Error("No se permiten teselas"); });
      map.attributionControl.setPrefix(false);
      map.attributionControl.addAttribution("© OpenStreetMap / Geofabrik · ODbL");
      this.renderer = L.canvas({padding: .3, tolerance: 3});
      map.options.renderer = this.renderer;
      L.control.scale({imperial: false, metric: true, position: "bottomleft", maxWidth: 80}).addTo(map);
      const north = L.control({position: "topright"});
      north.onAdd = () => { const div = L.DomUtil.create("div", "north-control"); div.textContent = "↑ N"; return div; };
      north.addTo(map);
      const corridor = new Set(data.routes.base);
      for (const road of data.roads) {
        const main = corridor.has(road.id);
        const line = L.polyline(road.latlngs, {renderer: this.renderer, color: main ? "#75857d" : "#9ca99f",
                                            weight: main ? 3.4 : 1.8, opacity: main ? .95 : .8});
        line.bindTooltip(escape(road.name) + "<br>" + escape(road.id), {sticky: true});
        line.on("click", () => callbacks.onEdge(road.id)); line.addTo(map);
        this.roads.set(road.id, {data: road, line});
      }
      this.selection = L.layerGroup().addTo(map);
      this.route = L.layerGroup().addTo(map);
      this.alternatives = L.layerGroup().addTo(map);
      for (const id of data.routes.closure.filter(id => !data.routes.base.includes(id))) {
        L.polyline(this.roads.get(id).data.latlngs, {color: "#a07e45", weight: 4.2, opacity: .8, dashArray: "5 4", interactive: false}).addTo(this.alternatives);
      }
      const closedRoad = this.roads.get(data.closedEdge).data;
      this.closed = L.polyline(closedRoad.latlngs, {weight: 7, color: COLORS.closed, dashArray: "7 4"}).addTo(map);
      this.closed.on("click", () => callbacks.onEdge(data.closedEdge));
      this.closedLabel = L.tooltip({permanent: true, direction: "top", className: "map-label", offset: [0, -9]})
        .setLatLng(L.latLngBounds(closedRoad.latlngs.flat()).getCenter()).addTo(map);
      this.vehicleLayer = L.layerGroup().addTo(map);
      this.drawRoute(); this.fit();
    }
    fit() { this.map.invalidateSize({pan: false}); this.map.fitBounds(this.data.bounds, {padding: [22, 20], animate: false}); }
    drawRoute() {
      this.route.clearLayers();
      this.routeIds = DTReplay.routeFor(this.data, this.catalog, this.selectedVehicle, this.scenario);
      for (const id of this.routeIds) L.polyline(this.roads.get(id).data.latlngs, {
        color: COLORS[this.scenario], weight: this.selectedVehicle ? 4.4 : 3.5, opacity: this.selectedVehicle ? .85 : .48, interactive: false,
      }).addTo(this.route);
      const closed = this.scenario === "closure";
      this.closed.setStyle({color: closed ? COLORS.closed : "#68745c", weight: closed ? 7.5 : 5, dashArray: closed ? "7 4" : "4 5"});
      this.closedLabel.setContent(closed ? "× Cierre virtual" : "Enlace evaluado · abierto");
      this.closedLabel.getElement()?.style.setProperty("color", closed ? COLORS.closed : "#53634d");
      this.closed.bringToFront();
    }
    setScenario(scenario) {
      if (scenario === this.scenario) return;
      this.scenario = scenario; this.drawRoute();
    }
    selectVehicle(id) {
      if (id === this.selectedVehicle) return;
      this.selectedVehicle = id;
      // El rótulo fijo del tramo cede espacio al ID; línea, leyenda y encabezado siguen identificando el cierre.
      if (id) this.map.removeLayer(this.closedLabel);
      else this.closedLabel.addTo(this.map);
      this.drawRoute();
    }
    selectEdge(id) {
      const road = this.roads.get(id); if (!road) return;
      this.selectedEdge = id; this.selection.clearLayers();
      L.polyline(road.data.latlngs, {color: "#344d64", weight: 10, opacity: .28, interactive: false}).addTo(this.selection).bringToBack();
    }
    render(pair) {
      const visible = new Set();
      for (const [idx, lat, lon, speed] of pair[this.scenario]) {
        visible.add(idx); const id = this.data.vehicles[idx], selected = id === this.selectedVehicle;
        let marker = this.markers.get(idx);
        if (!marker) {
          marker = L.circleMarker([lat, lon], {renderer: this.renderer, radius: 3.7, weight: 1.1, color: "#fff", fillOpacity: 1});
          marker.on("click", () => this.callbacks.onVehicle(id)); this.markers.set(idx, marker);
        }
        marker.setLatLng([lat, lon]).setStyle({
          fillColor: selected ? COLORS.selected : COLORS[this.scenario], color: selected ? "#283c37" : "#fbfcf7",
          radius: selected ? 6.3 : 3.7, weight: selected ? 2.1 : 1.1,
        });
        if (marker._dtSelected !== selected || !marker.getTooltip()) {
          marker.unbindTooltip(); marker.bindTooltip("", {permanent: selected, direction: "top", className: selected ? "vehicle-label" : ""});
          marker._dtSelected = selected;
        }
        marker.setTooltipContent(escape(id) + (selected ? "" : " · " + fmt(speed) + " m/s<br>t = " + pair.time + " s · FCD nativo"));
        if (!this.vehicleLayer.hasLayer(marker)) marker.addTo(this.vehicleLayer);
        if (selected) marker.openTooltip();
        marker.bringToFront();
      }
      for (const [idx, marker] of this.markers) if (!visible.has(idx) && this.vehicleLayer.hasLayer(marker)) this.vehicleLayer.removeLayer(marker);
      this.time = pair.time;
      this.map.getContainer().dataset.frameTime = pair.time;
      this.map.getContainer().dataset.run = this.scenario;
    }
    inspect() {
      return {scenario: this.scenario, frameTime: this.time, roadCount: this.roads.size, selectedEdge: this.selectedEdge,
        route: [...this.routeIds], closedEdge: this.data.closedEdge, closedLabel: this.closedLabel.getContent(),
        tileLayers: Object.values(this.map._layers).filter(layer => layer instanceof L.TileLayer).length,
        camera: {center: [this.map.getCenter().lat, this.map.getCenter().lng], zoom: this.map.getZoom()},
        vehicles: [...this.markers].filter(([, m]) => this.vehicleLayer.hasLayer(m)).map(([idx, m]) => ({
          id: this.data.vehicles[idx], lat: m.getLatLng().lat, lon: m.getLatLng().lng,
          selected: this.data.vehicles[idx] === this.selectedVehicle, tooltip: m.getTooltip().getContent(),
        }))};
    }
  }
  window.DTMapPane = Object.freeze({MapPane, COLORS});
})();
