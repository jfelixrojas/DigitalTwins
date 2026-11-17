"""Original/0 verificado; exportar la 008 sin reescribir evidencias 001–007."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re

from pyproj import CRS, Transformer, network, __version__ as pyproj_version

from ..doctor import sha256
from ..pilot import require
from ..visualization.builder import ROOT, Sources, check_metrics, geometry, pack_fcd, safe_json

PAIR = "outputs/closure_sensitivity/combinations/original_offset000"
OUT = ROOT / "outputs/nicegui_comparison"
CLOSED = "1257993561#5"


class SumoProjection:
    """SUMO local -> UTM original -> WGS84 -> orden lat/lon de Leaflet."""
    def __init__(self, location):
        network.set_network_enabled(False)
        self.spec = location["projParameter"]
        self.offset = tuple(float(v) for v in location["netOffset"].split(","))
        require(len(self.offset) == 2 and all(math.isfinite(v) for v in self.offset), "Invalid network offset")
        require(self.spec not in ("!", "-", ".", ""), "Georeferencing unavailable: SUMO projection is not declared")
        self.crs = CRS.from_user_input(self.spec)
        require(self.crs.is_projected, "Expected the original projected SUMO network")
        self.inverse = Transformer.from_crs(self.crs, "EPSG:4326", always_xy=True)
        self.forward = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True)
        self.max_roundtrip_error_m = 0.

    def to_leaflet(self, x, y):
        require(math.isfinite(x) and math.isfinite(y), "Nonfinite SUMO coordinate")
        lon, lat = self.inverse.transform(x - self.offset[0], y - self.offset[1], errcheck=True)
        require(-90 <= lat <= 90 and -180 <= lon <= 180, "Invalid geographic coordinate")
        xx, yy = self.from_leaflet(lat, lon)
        error = math.hypot(xx - x, yy - y)
        require(error < .0001, "Georeferencing roundtrip failed; no approximate coordinates are used")
        self.max_roundtrip_error_m = max(self.max_roundtrip_error_m, error)
        return [lat, lon]

    def from_leaflet(self, lat, lon):
        x, y = self.forward.transform(lon, lat, errcheck=True)
        return [x + self.offset[0], y + self.offset[1]]

    def validate_anchors(self, net, osm):
        nodes = {n.get("id"): n for n in osm.findall("node")}
        anchors = []
        for junction in net.findall("junction"):
            if junction.get("id") not in nodes:
                continue
            node = nodes[junction.get("id")]
            lat, lon = float(node.get("lat")), float(node.get("lon"))
            x, y = float(junction.get("x")), float(junction.get("y"))
            expected_x, expected_y = self.from_leaflet(lat, lon)
            error = math.hypot(expected_x - x, expected_y - y)
            require(error < .03, "Georeferencing differs from original OSM anchor " + node.get("id"))
            anchors.append({"node": node.get("id"), "lat": lat, "lon": lon, "sumo_x": x, "sumo_y": y, "error_m": error})
        require(len(anchors) >= 3, "Insufficient independent OSM anchors; georeferencing stopped")
        return anchors


def load_original(sources):
    """Fijar el paquete anterior y comparar sus datos con los nativos."""
    viewer_manifest = sources.load("outputs/visualization/manifest.json", "viewer006_manifest")
    for relative, item in viewer_manifest["outputs"].items():
        require(sha256(sources.root / "outputs/visualization" / relative) == item["sha256"], "Viewer006 artifact changed: " + relative)
    path = sources.add("outputs/visualization/index.html", "viewer006_consistency")
    matched = re.search(r'<script id="viewer-data" type="application/json">(.*?)</script>', path.read_text(), re.S)
    require(matched is not None, "Viewer006 structured data unavailable")
    old = json.loads(matched.group(1))
    require(old["schema"] == "digitaltwins-viewer-1", "Unsupported viewer006 schema")
    return old


def vehicle_catalog(trips, routes, ids, road_ids):
    """Ciclo de vida y ruta de cada ID, siempre desde registros individuales."""
    catalog = {vid: {} for vid in ids}
    for scenario in ("base", "closure"):
        native_rows = trips[scenario].findall("tripinfo")
        rows = {row.get("id"): row for row in native_rows}
        require(len(native_rows) == len(rows) == len(ids) and set(rows) == set(ids) == set(routes[scenario]), "Vehicle metadata population differs")
        for vid in ids:
            row = rows[vid]; route = routes[scenario][vid]["edges"]
            depart, arrival = float(row.get("depart")), float(row.get("arrival"))
            require(math.isfinite(depart) and math.isfinite(arrival) and 0 <= depart < arrival, "Invalid native vehicle lifetime")
            require(len(route) >= 2 and all(edge in road_ids for edge in route), "Executed route contains unknown edges")
            catalog[vid][scenario] = {
                "depart_s": depart, "arrival_s": arrival, "duration_s": float(row.get("duration")),
                "waiting_time_s": float(row.get("waitingTime")), "time_loss_s": float(row.get("timeLoss")),
                "route_length_m": float(row.get("routeLength")), "route": route,
            }
    return {"schema": "digitaltwins-vehicle-catalog-1", "vehicles": catalog}


def prepare(output=OUT):
    output = Path(output).resolve()
    require(output == OUT, "Comparison output must remain outputs/nicegui_comparison")
    if output.exists() and any(output.iterdir()):
        require((output / "manifest.json").is_file() and json.loads((output / "manifest.json").read_text()).get("kind") == "digitaltwins_nicegui_comparison",
                "Output is not an owned NiceGUI prototype bundle")
    sources = Sources()
    checked = sources.pin()
    old = load_original(sources); reference = old["cases"]["original_offset000"]
    net = sources.xml("outputs/closure_sensitivity/common/controlled.net.xml", "network_geometry")
    audit = sources.load("outputs/pilot_controlled_verified/edge_attribute_audit.json", "inferred_attributes")
    geo = geometry(net, audit)
    require(geo == old["geometry"], "Geometry differs from viewer006")
    projection = SumoProjection(geo["location"])
    anchors = projection.validate_anchors(net, sources.xml("outputs/pilot_verified/pilot.osm.xml", "independent_OSM_projection_anchors"))
    require(len(anchors) == 243, "Original OSM anchor inventory differs")
    ids = old["vehicles"]; lanes = {lane["id"]: lane for lane in geo["lanes"]}
    roads = []
    for road in geo["roads"]:
        roads.append({**{k: v for k, v in road.items() if k != "lanes"},
                      "lanes": len(road["lanes"]),
                      "latlngs": [[projection.to_leaflet(*p) for p in lanes[lid]["shape"]] for lid in road["lanes"]]})
    metrics, active, arrived, frames, samples, trips = {}, {}, {}, {}, {}, {}
    for scenario in ("base", "closure"):
        relative = PAIR + "/" + scenario
        metrics[scenario] = sources.load(relative + "/system_metrics.json", "scenario_metrics")
        trips[scenario] = sources.xml(relative + "/tripinfo.xml", "metric_validation_and_vehicle_lifetimes")
        check_metrics(metrics[scenario], trips[scenario])
        native_frames, count = pack_fcd(sources.xml(relative + "/fcd.xml.gz", "native_FCD_positions"), ids, lanes)
        steps = sources.xml(relative + "/summary.xml", "active_vehicles").findall("step")
        active[scenario] = [int(row.get("running")) for row in steps]
        arrived[scenario] = [int(row.get("arrived")) for row in steps]
        require(len(steps) == 1800 and [float(row.get("time")) for row in steps] == list(range(1800)), "Incomplete summary timeline")
        require([len(frame) for frame in native_frames] == active[scenario], "FCD and active counts differ")
        require(native_frames == reference["frames"][scenario] and metrics[scenario] == reference["metrics"][scenario]
                and active[scenario] == reference["active"][scenario], "Scenario differs from intervention006")
        frames[scenario] = [[[idx, *projection.to_leaflet(x, y), speed] for idx, x, y, speed in frame] for frame in native_frames]
        samples[scenario] = count
    comparison = sources.load(PAIR + "/comparison.json", "paired_comparison")
    require(comparison == reference["comparison"], "Paired comparison differs from viewer006")
    routes, all_routes = {}, {}
    for scenario in ("base", "closure"):
        executed = sources.load(PAIR + "/" + scenario + "/executed_routes.json", "executed_routes")
        all_routes[scenario] = executed
        routes[scenario] = executed["W_E.0000"]["edges"]
        require(routes[scenario] == reference["routes"][scenario], "Executed routes differ from viewer006")
    require(CLOSED in routes["base"] and CLOSED not in routes["closure"], "Closed edge or detour differs")
    require(all(metrics[s]["completed"] == 150 and metrics[s]["pending"] == 0 for s in metrics), "Population differs")
    require(samples == {"base": 19935, "closure": 20340}, "Original/0 sample count differs")
    cloud = [p for road in roads for lane in road["latlngs"] for p in lane]
    bounds = [[min(p[0] for p in cloud), min(p[1] for p in cloud)], [max(p[0] for p in cloud), max(p[1] for p in cloud)]]
    catalog = next(item for item in old["catalog"] if item["id"] == "SIM-005")
    data = {"schema": "digitaltwins-nicegui-1", "experiment": "SIM-005", "combination": "original_offset000",
            "roads": roads, "bounds": bounds, "closedEdge": CLOSED, "vehicles": ids, "frames": frames, "active": active, "arrived": arrived,
            "metrics": metrics, "comparison": comparison, "routes": routes, "catalog": catalog,
            "movementDescriptions": old["movementDescriptions"], "resolution_s": 1, "last_time_s": 1799,
            "projection": {"source": projection.spec, "netOffset": projection.offset, "target": "EPSG:4326",
                           "order": "Leaflet [latitude,longitude]; always_xy=True inside PROJ",
                           "roundtrip_max_error_m": projection.max_roundtrip_error_m,
                           "OSM_anchors": len(anchors), "OSM_anchor_max_error_m": max(a["error_m"] for a in anchors)},
            "classification": "Synthetic simulation, no real traffic observations or calibration."}
    reference007 = sources.load("outputs/nicegui_prototype/manifest.json", "frozen_007_manifest")
    original007 = sources.add("outputs/nicegui_prototype/data.json", "frozen_007_dataset")
    require(sha256(original007) == reference007["data_sha256"] and original007.read_text() == safe_json(data) + "\n",
            "Scientific dataset differs from verified intervention007")
    vehicles = vehicle_catalog(trips, all_routes, ids, {road["id"] for road in roads})
    output.mkdir(exist_ok=True)
    (output / "data.json").write_text(safe_json(data) + "\n")
    (output / "projection_validation.json").write_text(json.dumps({**data["projection"], "anchors": anchors}, ensure_ascii=False, indent=2) + "\n")
    (output / "vehicle_catalog.json").write_text(safe_json(vehicles) + "\n")
    manifest = {"kind": "digitaltwins_nicegui_comparison", "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "simulation_runs": 0, "canonical_artifacts_checked": checked, "native_FCD_samples": samples,
                "resolution_s": 1, "interpolation": False, "pyproj_version": pyproj_version,
                "projection": data["projection"], "sources": list(sources.entries.values()),
                "viewer006_manifest_sha256": sha256(ROOT / "outputs/visualization/manifest.json"),
                "reference007_manifest_sha256": sha256(ROOT / "outputs/nicegui_prototype/manifest.json"),
                "reference007_data_sha256": reference007["data_sha256"],
                "vehicle_catalog_sha256": sha256(output / "vehicle_catalog.json"),
                "data_sha256": sha256(output / "data.json"), "data_bytes": (output / "data.json").stat().st_size,
                "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in sorted(Path(__file__).parent.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return data
