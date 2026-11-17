"""Empaquetar evidencia local autorizada; JSON compacto, geometría y FCD nativos."""

import csv
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

from ..doctor import sha256
from ..pilot import require

ROOT = Path(__file__).resolve().parents[3]
SENSITIVITY = "outputs/closure_sensitivity"
ANIMATED = ("original_offset000", "jitter103_offset000")
EDGES = ("1257993561#5", "-175606174", "-198404021", "1182057747", "1225540290#0")
ROOTS = {"SIM-002": "outputs/pilot_verified", "SIM-003": "outputs/pilot_controlled_verified",
         "SIM-004": "outputs/closure_experiment_verified", "SIM-005": SENSITIVITY}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def safe_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


class Sources:
    def __init__(self, root=ROOT):
        self.root = root; self.entries = {}; self.expected = {}; self.manifests = {}

    def add(self, relative, role):
        relative = str(relative); path = (self.root / relative).resolve()
        require(path.is_relative_to(self.root) and path.is_file(), "Missing or unauthorized source: " + relative)
        if relative not in self.entries:
            digest = sha256(path)
            if relative in self.expected:
                require(digest == self.expected[relative], "Canonical source hash differs: " + relative)
            self.entries[relative] = {"path": relative, "bytes": path.stat().st_size, "sha256": digest, "roles": []}
        if role not in self.entries[relative]["roles"]:
            self.entries[relative]["roles"].append(role)
        return path

    def load(self, relative, role):
        return json.loads(self.add(relative, role).read_text())

    def table(self, relative, role):
        with self.add(relative, role).open() as handle:
            return list(csv.DictReader(handle))

    def xml(self, relative, role):
        path = self.add(relative, role)
        with (gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")) as handle:
            return ET.parse(handle).getroot()

    def pin(self):
        checked = 0
        for code, relative in ROOTS.items():
            path = self.add(relative + "/manifest.json", "experiment_manifest")
            manifest = json.loads(path.read_text()); self.manifests[code] = manifest
            for name, item in manifest["artifacts"].items():
                if Path(name).name == ".DS_Store":
                    continue
                p = self.root / relative / name
                require(p.is_file() and sha256(p) == item["sha256"], "Verified artifact changed: " + str(p))
                self.expected[relative + "/" + name] = item["sha256"]; checked += 1
        return checked


def points(shape):
    return [[float(v.split(",")[0]), float(v.split(",")[1])] for v in shape.split()]


def geometry(net, attributes):
    audit = {r["edge"]: r for r in attributes["edges"]}
    lanes = {l.get("id"): {"id": l.get("id"), "edge": e.get("id"), "shape": points(l.get("shape")),
                           "length": float(l.get("length"))}
             for e in net.findall("edge") for l in e.findall("lane")}
    roads = [{"id": e.get("id"), "lanes": [l.get("id") for l in e.findall("lane")],
              "name": audit.get(e.get("id"), {}).get("name") or "Vía sin nombre",
              "speed": float(e.find("lane").get("speed")), "defaults": audit.get(e.get("id"), {}).get("default_fields", [])}
             for e in net.findall("edge") if e.get("function") != "internal"]
    programs = {p.get("id"): {"id": p.get("id"), "program": p.get("programID"),
                "states": [phase.get("state") for phase in p.findall("phase")],
                "durations": [float(phase.get("duration")) for phase in p.findall("phase")], "offset": float(p.get("offset", 0))}
                for p in net.findall("tlLogic")}
    signals = []
    for c in net.findall("connection"):
        if not c.get("tl"):
            continue
        tid, index, via = c.get("tl"), int(c.get("linkIndex")), c.get("via")
        require(tid in programs and via in lanes, "Signal connection lacks program or via geometry")
        require(all(0 <= index < len(state) for state in programs[tid]["states"]), "Signal linkIndex outside state vector")
        signals.append({"tls": tid, "index": index, "via": via, "from": c.get("from"), "to": c.get("to")})
    cloud = [p for l in lanes.values() for p in l["shape"]]
    bounds = [min(p[0] for p in cloud), min(p[1] for p in cloud), max(p[0] for p in cloud), max(p[1] for p in cloud)]
    return {"lanes": list(lanes.values()), "roads": roads, "programs": programs, "signals": signals,
            "bounds": bounds, "location": dict(net.find("location").attrib)}


def pack_fcd(root, ids, lanes, horizon=1800):
    index = {vid: i for i, vid in enumerate(ids)}; frames = [[] for _ in range(horizon)]; seen = set(); count = 0
    for step in root.findall("timestep"):
        t = float(step.get("time")); require(t.is_integer() and 0 <= t < horizon and t not in seen, "Invalid FCD timestamp")
        t = int(t); seen.add(t); vehicles = set()
        for vehicle in step.findall("vehicle"):
            vid = vehicle.get("id"); require(vid in index and vid not in vehicles, "Unexpected/duplicate FCD vehicle")
            require(vehicle.get("lane") in lanes, "FCD lane missing from geometry")
            x, y, speed = (float(vehicle.get(k)) for k in ("x", "y", "speed"))
            require(all(math.isfinite(v) for v in (x, y, speed)), "Invalid FCD coordinate")
            frames[t].append([index[vid], x, y, speed]); vehicles.add(vid); count += 1
    require(len(seen) == horizon, "Incomplete FCD timeline")
    return frames, count


def compact_signals(root, programs, horizon=1800):
    ids = sorted(programs); changes = {tid: [] for tid in ids}; previous = {}; seen = set(); last_time = {}
    for state in root.findall("tlsState"):
        tid = state.get("id"); t = float(state.get("time")); phase = int(state.get("phase"))
        require(tid in programs and t.is_integer() and 0 <= t < horizon and (t, tid) not in seen, "Invalid TLS record")
        require(t > last_time.get(tid, -1), "Unordered TLS timeline")
        require(0 <= phase < len(programs[tid]["states"]), "Invalid TLS phase index")
        require(state.get("programID") == programs[tid]["program"] and state.get("state") == programs[tid]["states"][phase], "TLS record and geometry mapping differ")
        seen.add((t, tid)); last_time[tid] = t
        if previous.get(tid) != phase:
            changes[tid].append([int(t), phase]); previous[tid] = phase
    require(len(seen) == horizon * len(ids), "Incomplete native TLS coverage")
    return changes


def check_metrics(metrics, tripinfo):
    trips = [t for t in tripinfo.findall("tripinfo") if float(t.get("arrival", -1)) >= 0 and not t.get("vaporized")]
    require(len(trips) == metrics["completed"], "Displayed completion count differs from tripinfo")
    for field, attr in (("duration_s", "duration"), ("waiting_time_s", "waitingTime"), ("time_loss_s", "timeLoss"), ("route_length_m", "routeLength")):
        total = sum(float(t.get(attr)) for t in trips)
        require(abs(total - metrics[field]["total"]) < .001, "Displayed metric differs from tripinfo: " + field)
        require(metrics[field]["count"] == len(trips) and abs(metrics[field]["mean"] * len(trips) - total) < .001,
                "Displayed metric mean or denominator differs from tripinfo: " + field)


def pack_edges(rows, totals):
    compact = {}
    for eid in EDGES:
        selected = sorted((r for r in rows if r["edge"] == eid), key=lambda r: float(r["begin_s"]))
        require([float(r["begin_s"]) for r in selected] == list(range(0, 1800, 60)), "Edge time series incomplete")
        compact[eid] = {}
        for name in ("base", "closure"):
            values = []
            for r in selected:
                require(float(r["end_s"]) - float(r["begin_s"]) == 60, "Unexpected edge aggregation period")
                flow, entered = float(r[name + "_flow_in_veh_h"]), int(r[name + "_entered_veh"])
                require(abs(flow - 60 * entered) < 1e-9, "Flow units inconsistent with counts")
                values.append([flow, float(r[name + "_occupancy_pct"]), float(r[name + "_mean_vehicles"])])
            compact[eid][name] = values
    all_totals = {r["edge"]: [int(r["base_entered_veh"]), int(r["closure_entered_veh"]),
                   float(r["base_max_occupancy_pct"]), float(r["closure_max_occupancy_pct"]),
                   float(r["base_sampled_vehicle_s"]) / 1800, float(r["closure_sampled_vehicle_s"]) / 1800] for r in totals}
    return compact, all_totals


def legacy_snapshot(summary):
    stats = summary["base"]["trip_statistics"]; base = summary["base"]
    return {"requested": base["requested_trips"], "completed": base["completed_vehicles"], "rejected": base["rejected_trips"],
            "duration_mean_s": float(stats["duration"]), "duration_total_s": float(stats["totalTravelTime"]),
            "waiting_mean_s": float(stats["waitingTime"]), "time_loss_mean_s": float(stats["timeLoss"]), "length_mean_m": float(stats["routeLength"])}


def make_catalog(sources):
    definitions = {
        "SIM-002": ("Primer piloto con demanda aleatoria", "Prueba técnica de red y ruteo", "¿Puede ejecutarse y repetirse el corredor OSM local?", "Demanda aleatoria con semilla 42: 150 solicitudes, sin sustitución de rechazos.", "Demuestra factibilidad técnica y rechazos de ruteo; no representa una demanda observada.", "pilot"),
        "SIM-003": ("Piloto con demanda controlada", "Base controlada", "¿Son válidos y reproducibles seis movimientos explícitos?", "Seis OD, 600 veh/h nominales durante 900 s, 150 solicitudes periódicas.", "Permite fijar una base equivalente para cierres posteriores, dentro de los supuestos sintéticos.", "controlled"),
        "SIM-004": ("Primer cierre virtual", "Contrafactual base/cierre", "¿Qué cambia al impedir el paso por Roosevelt hacia el este?", "Prohibición passenger en 1257993561#5 durante [0,1800), con información de desvío en el origen.", "El +2,03 % corresponde a esta configuración. No prueba saturación ni efectos reales.", "closure"),
        "SIM-005": ("Sensibilidad temporal del cierre", "Matriz factorial descriptiva", "¿Cómo cambia el impacto al perturbar salidas y desfases virtuales?", "Cinco calendarios por tres offsets; 30 corridas y un par nuevo repetido. Semilla SUMO fija 42.", "El efecto global depende del diseño temporal; la mediana W_E es positiva en los 15 pares.", "sensitivity")}
    catalog = []
    for code, (title, kind, question, intervention, interpretation, module) in definitions.items():
        relative = ROOTS[code]; manifest = sources.manifests[code]
        created = datetime.fromisoformat(manifest["created_at_utc"]).astimezone(ZoneInfo("America/Bogota"))
        summary = sources.load(relative + "/summary.json", "catalog_metrics")
        if code in ("SIM-002", "SIM-003"):
            results = legacy_snapshot(summary)
        elif code == "SIM-004":
            results = {"requested": summary["base"]["requested"], "completed_base": summary["base"]["completed"],
                       "completed_closure": summary["closure"]["completed"], "duration_base_s": summary["base"]["duration_s"]["mean"],
                       "duration_closure_s": summary["closure"]["duration_s"]["mean"],
                       "delta_total_s": summary["system_comparison"]["duration_s"]["closure_total"] - summary["system_comparison"]["duration_s"]["base_total"],
                       "delta_pct": summary["system_comparison"]["duration_s"]["delta_of_mean_pct"]}
        else:
            results = {"pairs": summary["evaluated_pairs"], "increases": summary["higher_total_travel_time"], "reductions": summary["lower_total_travel_time"],
                       "delta_min_s": summary["total_duration_change_s"]["min"], "delta_max_s": summary["total_duration_change_s"]["max"],
                       "delta_median_s": summary["total_duration_change_s"]["median"], "delta_mean_s": summary["total_duration_change_s"]["mean"],
                       "WE_positive_medians": summary["W_E_positive_median_pairs"]}
        inventory = {"FCD": [], "TLS": []}
        for name in manifest["artifacts"]:
            if name.endswith("fcd.xml.gz"):
                inventory["FCD"].append(relative + "/" + name); sources.add(relative + "/" + name, "inventory_FCD")
            if name.endswith("tls_states.xml.gz"):
                inventory["TLS"].append(relative + "/" + name); sources.add(relative + "/" + name, "inventory_native_signals")
        sources.add(relative + "/reproducibility.json" if code != "SIM-002" else relative + "/summary.json", "reproducibility")
        configuration = {
            "Red": "350 enlaces y 604 carriles externos; tres componentes débiles (321/21/8 enlaces). Misma red desde SIM-002.",
            "SHA-256 de red": "5ffebc98d865aa238703cc39463d4a34128e83390e6a4b24611a9e280b6fe4d5",
            "Tiempo": "Horizonte [0,1800) s; paso 1 s; salidas previstas antes de 900 s.",
            "Semáforos": "18 programas estáticos virtuales, ciclos de 90 s; sin calibración ni registros reales.",
            "Semillas": "SUMO 42; un hilo de ruteo.",
        }
        if code == "SIM-002":
            configuration["Demanda"] = "randomTrips.py, passenger, período 6 s, semilla 42; 150 solicitudes, 109 rutas aceptadas y 41 rechazadas. Sin sustituir rechazos."
            configuration["Entradas"] = "scenarios/pilot/pilot.sumocfg; configuración y argv efectivos en outputs/pilot_verified/commands.json."
            sources.add("scenarios/pilot/pilot.sumocfg", "experiment_recipe")
        else:
            demand = sources.manifests["SIM-003"]["demand"]
            configuration["Demanda"] = "150 viajes: W_E 45, E_W 45, N_W 15, E_N 15, N_E 15, W_S 15; 600 veh/h nominales durante 900 s."
            configuration["Vehículo"] = "; ".join(f"{k}={v}" for k, v in demand["vehicle_type"].items()) + "; resto: supuestos predeterminados SUMO."
            configuration["Llegadas originales"] = "; ".join(f"{s['id']}: {s['rate_veh_h']} veh/h, inicio {s['begin_s']} s" for s in demand["streams"])
            configuration["Entradas"] = "scenarios/pilot_controlled/demand.json; red, rutas y calendario nativos fijados en el manifiesto."
            sources.add("scenarios/pilot_controlled/demand.json", "experiment_recipe")
        if code in ("SIM-004", "SIM-005"):
            configuration["Cierre"] = "1257993561#5, clase passenger, [0,1800) s; closingReroute desde 198404000; routingMode=8 solo en cierre. 45 rutas W_E desviadas."
            sources.add("scenarios/closure_experiment/experiment.json", "experiment_recipe")
        if code == "SIM-005":
            configuration["Sensibilidad"] = "Original y J101/J102/J103/J104: jitter entero acotado ±15 s, semillas de calendario 101–104, orden por OD e IDs conservados. Offsets adicionales 0/30/60 s en todos los programas."
            configuration["Repetición"] = "15 pares + repetición de J101/30; dos corridas adicionales de auditoría inicial sin FCD. Umbral N_E: +60 s."
            sources.add("scenarios/closure_sensitivity/experiment.json", "experiment_recipe")
        catalog.append({"id": code, "name": title, "date": created.strftime("%Y-%m-%d"), "created_at": created.isoformat(),
            "date_zone": "America/Bogota", "sheet_version": "1.0.0", "SUMO_version": "1.28.0", "type": kind,
            "question": question, "intervention": intervention, "interpretation": interpretation,
            "configuration": configuration,
            "constants": "Red del mismo corredor; conducción y señales virtuales declaradas. En cada par se conservan demanda, semilla y configuración general.",
            "horizon_s": 1800, "simulation_seed": 42, "results": results, "inventory": inventory,
            "manifest": relative + "/manifest.json", "manifest_sha256": sha256(ROOT / relative / "manifest.json"),
            "command": f"PYTHONPATH=src python3 -B -m digitaltwins.{module} --output outputs/{module}_reproduction",
            "sheet": f"docs/simulations/{code}.md",
            "limitations": "Cartografía OSM, atributos inferidos, demanda sintética y semáforos virtuales. Sin conteos, Waze, registros reales ni calibración física."})
    return catalog


def metric_rows(results):
    labels = {"requested": "Viajes solicitados", "completed": "Completados", "rejected": "Rechazados",
        "duration_mean_s": "Recorrido medio (s)", "duration_total_s": "Tiempo total (s)", "waiting_mean_s": "waitingTime medio (s)",
        "time_loss_mean_s": "timeLoss medio (s)", "length_mean_m": "Longitud media (m)", "completed_base": "Completados base",
        "completed_closure": "Completados cierre", "duration_base_s": "Recorrido medio base (s)", "duration_closure_s": "Recorrido medio cierre (s)",
        "delta_total_s": "Cambio total (s)", "delta_pct": "Cambio (%)", "pairs": "Pares", "increases": "Pares que empeoran",
        "reductions": "Pares que mejoran", "delta_min_s": "Cambio mínimo (s)", "delta_max_s": "Cambio máximo (s)",
        "delta_median_s": "Cambio mediano (s)", "delta_mean_s": "Cambio medio (s)", "WE_positive_medians": "Pares con mediana W_E positiva"}
    return [(labels[k], v) for k, v in results.items()]


def write_sheets(catalog):
    folder = ROOT / "docs/simulations"; folder.mkdir(exist_ok=True)
    for item in catalog:
        table = "\n".join(f"| {label} | {value:g} |" for label, value in metric_rows(item["results"]))
        configuration = "\n\n".join(f"**{k}:** {v}" for k, v in item["configuration"].items())
        body = f"""# {item['id']} — {item['name']}

Ficha generada desde resultados estructurados; regenerar con `python3 -B -m digitaltwins.visualization` y `PYTHONPATH=src`.

## Identificación y objetivo

Fecha del experimento: **{item['date']}**, zona America/Bogota. Registro original: `{item['created_at']}`.
Versión de ficha: {item['sheet_version']}; SUMO {item['SUMO_version']}. Tipo: {item['type']}.

{item['question']}

## Configuración e intervención

Corredor de Alameda Franklin Delano Roosevelt, San Salvador, El Salvador. Horizonte {item['horizon_s']} s; semilla SUMO {item['simulation_seed']}.

{configuration}

{item['intervention']}

{item['constants']}

La configuración completa y los parámetros están en el manifiesto; las fases no son registros de controladores reales.

## Resultados

| Indicador | Valor |
|---|---:|
{table}

## Interpretación y límites

{item['interpretation']}

{item['limitations']}

Trayectorias FCD disponibles: **{len(item['inventory']['FCD'])}**. Registros temporales nativos de señales: **{len(item['inventory']['TLS'])}**.
La ausencia de FCD impide animar posiciones originales; rutas y promedios no se convierten en trayectorias.

## Reproducción y evidencia

Desde la raíz de DigitalTwins, con fuentes y herramientas locales fijadas y una salida nueva:

```sh
{item['command']}
```

Manifiesto: [{item['manifest']}](../../{item['manifest']}).
SHA-256: `{item['manifest_sha256']}`.
Resultados estructurados: [summary.json](../../{ROOTS[item['id']]}/summary.json).
El [catálogo de fuentes visualizadas](../../outputs/visualization/source_catalog.json) registra tamaños, hashes y funciones de cada insumo utilizado.

Las evidencias en `outputs/` son locales y están excluidas de Git. La ficha no autoriza descargas ni intervenciones reales.
"""
        (folder / (item["id"] + ".md")).write_text(body)
    lines = [f"| [{x['id']}]({x['id']}.md) | {x['name']} | {x['date']} | {len(x['inventory']['FCD'])} | {len(x['inventory']['TLS'])} |" for x in catalog]
    (folder / "README.md").write_text("# Catálogo de simulaciones\n\nFichas generadas a partir de manifiestos y resultados verificados. Las fechas usan America/Bogota.\n\n| Código | Experimento | Fecha | FCD | Señales por segundo |\n|---|---|---|---:|---:|\n" + "\n".join(lines) + "\n\n[Abrir visor local](../../outputs/visualization/index.html) · [Flujo OSM–SUMO](../sumo_osm_workflow.md).\n\nSIM-005 aporta 30 corridas de matriz y dos de repetición con FCD y señales. La animación compacta del visor incluye Original/0 y J103/0, base y cierre; sus otros pares se consultan como agregados. Los estados son simulados, no observaciones reales.\n")


def collect():
    sources = Sources(); checked = sources.pin(); catalog = make_catalog(sources)
    net = sources.xml(SENSITIVITY + "/common/controlled.net.xml", "map_geometry")
    attributes = sources.load("outputs/pilot_controlled_verified/edge_attribute_audit.json", "source_and_inferred_attributes")
    geo = geometry(net, attributes); lanes = {l["id"]: l for l in geo["lanes"]}
    ids = sorted(r["id"] for r in sources.load(SENSITIVITY + "/schedules/original/arrival_schedule.json", "vehicle_identifiers"))
    matrix = sources.table(SENSITIVITY + "/matrix_comparison.csv", "sensitivity_matrix")
    summary = sources.load(SENSITIVITY + "/summary.json", "descriptive_sensitivity")
    cases = {}; signals = {}; trajectory_stats = {}
    for record in matrix:
        cid = record["combination"]; offset = int(record["offset_s"]); relative = SENSITIVITY + "/combinations/" + cid
        comparison = sources.load(relative + "/comparison.json", "paired_metrics_by_movement")
        metrics = {}; active = {}
        for name in ("base", "closure"):
            metrics[name] = sources.load(relative + f"/{name}/system_metrics.json", "scenario_metrics")
            trip = sources.xml(relative + f"/{name}/tripinfo.xml", "metric_integrity")
            check_metrics(metrics[name], trip)
            steps = sources.xml(relative + f"/{name}/summary.xml", "active_vehicle_timeline").findall("step")
            require(len(steps) == 1800 and [int(float(x.get("time"))) for x in steps] == list(range(1800)), "Summary timeline incomplete")
            active[name] = [int(x.get("running")) for x in steps]
            native = compact_signals(sources.xml(relative + f"/{name}/tls_states.xml.gz", "native_signal_timeline"), geo["programs"])
            if str(offset) in signals:
                require(signals[str(offset)] == native, "Signals differ for the same offset")
            else:
                signals[str(offset)] = native
        intervals, totals = pack_edges(sources.table(relative + "/edge_interval_comparison.csv", "edge_time_series"), sources.table(relative + "/edge_totals_comparison.csv", "edge_totals"))
        focal = sources.table(relative + "/NE_cases.csv", "focal_NE_cases")
        routes = sources.load(relative + "/closure/executed_routes.json", "executed_diversion_routes")
        base_routes = sources.load(relative + "/base/executed_routes.json", "executed_base_routes")
        baseline = base_routes["W_E.0000"]["edges"]; diverted = routes["W_E.0000"]["edges"]
        require("1257993561#5" in baseline and "1257993561#5" not in diverted and all(routes[v]["edges"] == diverted for v in ids if v.startswith("W_E.")), "Executed detour population differs")
        case = {"id": cid, "schedule": record["schedule"], "offset": offset, "metrics": metrics, "active": active,
                "comparison": comparison, "edgeIntervals": intervals, "edgeTotals": totals, "NE": focal,
                "routes": {"base": baseline, "closure": diverted}, "frames": None,
                "source": relative, "animated": cid in ANIMATED}
        if cid in ANIMATED:
            case["frames"] = {}
            for name in ("base", "closure"):
                frames, samples = pack_fcd(sources.xml(relative + f"/{name}/fcd.xml.gz", "animated_native_positions"), ids, lanes)
                require([len(f) for f in frames] == active[name], "FCD vehicle counts and summary.running differ")
                case["frames"][name] = frames; trajectory_stats[cid + "/" + name] = {"frames": 1800, "samples": samples, "resolution_s": 1}
        cases[cid] = case
    sources.load("data/osm/sources.json", "OSM_provenance")
    payload = {"schema": "digitaltwins-viewer-1", "geometry": geo, "vehicles": ids, "cases": cases, "signals": signals,
        "catalog": catalog, "summary": summary, "matrix": [{"id": r["combination"], "schedule": r["schedule"], "offset": int(r["offset_s"]),
                  "delta": float(r["delta_total_duration_s"]), "pct": float(r["delta_total_duration_pct"])} for r in matrix],
        "interestEdges": list(EDGES), "closedEdge": EDGES[0], "animationResolution_s": 1,
        "trajectory_stats": trajectory_stats,
        "movementDescriptions": {s["id"]: s["description"] for s in sources.manifests["SIM-003"]["demand"]["streams"]},
        "metricLabels": {x["id"]: metric_rows(x["results"]) for x in catalog}}
    return payload, sources, checked


def build(output="outputs/visualization"):
    out = (ROOT / output).resolve()
    require(out.parent == ROOT / "outputs" and out.name not in {Path(p).name for p in ROOTS.values()}, "Output must be a visualization directory directly under outputs")
    if out.exists() and any(out.iterdir()):
        require((out / "manifest.json").is_file() and json.loads((out / "manifest.json").read_text()).get("kind") == "digitaltwins_visualization", "Existing output is not an owned viewer bundle")
    out.mkdir(exist_ok=True); (out / "figures").mkdir(exist_ok=True)
    print("Verifying sources and compacting saved evidence", flush=True)
    data, sources, checked = collect(); write_sheets(data["catalog"])
    figures = {"sensitivity_matrix": SENSITIVITY + "/visual/total_time_matrix", "WE_impacts": SENSITIVITY + "/visual/WE_means_and_medians",
               "closure_routes": "outputs/closure_experiment_verified/visual/routes_comparison",
               "network_components": "outputs/pilot_controlled_verified/visual/network_components"}
    for name, relative in figures.items():
        for ext in (".png", ".svg"):
            path = sources.add(relative + ext, "static_verified_figure"); shutil.copyfile(path, out / "figures" / (name + ext))
    data["sources"] = list(sources.entries.values())
    here = Path(__file__).parent
    template = (here / "viewer.html").read_text()
    html = template.replace("<!--STYLE-->", "<style>" + (here / "viewer.css").read_text() + "</style>")
    html = html.replace("<!--DATA-->", '<script id="viewer-data" type="application/json">' + safe_json(data) + '</script>')
    html = html.replace("<!--SCRIPT-->", '<script>' + (here / "viewer.js").read_text() + '</script>')
    (out / "index.html").write_text(html)
    dump(out / "source_catalog.json", {"classification": "existing synthetic simulation evidence; no real traffic observations", "sources": data["sources"],
        "inventory": {c["id"]: c["inventory"] for c in data["catalog"]}, "animated": list(ANIMATED),
        "resolution_s": 1, "position_policy": "Native FCD x/y only; no interpolation or positions inferred from aggregates.",
        "TLS_policy": "Lossless phase-change compression of native records, identical across base/closure and schedules sharing offset.",
        "edge_period_s": 60, "edge_time_series_selection": list(EDGES), "all_edge_totals": 350})
    dump(out / "catalog.json", data["catalog"])
    files = [p for p in out.rglob("*") if p.is_file() and p.name != "manifest.json"]
    code = [p for p in here.iterdir() if p.is_file()]
    dump(out / "manifest.json", {"kind": "digitaltwins_visualization", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_artifacts_checked": checked, "sources": data["sources"], "simulation_runs": 0, "external_dependencies": [],
        "animation": data["trajectory_stats"], "all_combinations": 15, "signal_connections_mapped": len(data["geometry"]["signals"]),
        "html_bytes": (out / "index.html").stat().st_size,
        "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in code},
        "generated_sheets_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (ROOT / "docs/simulations").glob("*.md")},
        "outputs": {str(p.relative_to(out)): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(files)}})
    print(json.dumps({"viewer": str(out / "index.html"), "html_bytes": (out / "index.html").stat().st_size,
        "animated_runs": 4, "combinations": 15, "mapped_signal_connections": len(data["geometry"]["signals"]), "simulation_runs": 0}), flush=True)
