"""Escenario sintético controlado, diagnóstico y repetición local sin cierres."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from .doctor import sha256
from .diagnostics import Network, attribute_report, candidate_report, connectivity_report, shortest_path, warning_review
from .pilot import collect_metrics, require, write_json, warning_summary

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "outputs/pilot_verified"


def generate_departures(spec):
    """Cantidades de vehículos a partir de tasas veh/h y tiempos en segundos."""
    rows = []
    for stream in spec["streams"]:
        rate = Decimal(str(stream["rate_veh_h"]))
        require(rate > 0, "Arrival rate must be positive")
        start, end = Decimal(str(stream["begin_s"])), Decimal(str(spec["demand_end_s"]))
        require(0 <= start < end, "Invalid demand interval")
        step, i = Decimal(3600) / rate, 0
        while start + i * step < end:
            rows.append({"id": f'{stream["id"]}.{i:04d}', "stream": stream["id"],
                         "depart": str(start + i * step), "from": stream["from"], "to": stream["to"]})
            i += 1
    return sorted(rows, key=lambda r: (Decimal(r["depart"]), r["id"]))


def canonical_tripinfo(path):
    return {t.get("id"): dict(t.attrib) for t in ET.parse(path).getroot().findall("tripinfo")}


def canonical_summary(path):
    return [{k:v for k,v in s.attrib.items() if k != "duration"} for s in ET.parse(path).getroot().findall("step")]


def canonical_edge_data(path):
    return [{"interval": dict(i.attrib), "edges": {e.get("id"): dict(e.attrib) for e in i.findall("edge")}}
            for i in ET.parse(path).getroot().findall("interval")]


def output_indicators(directory):
    rows = []
    for interval in canonical_edge_data(directory / "edge_data.xml"):
        begin, end = float(interval["interval"]["begin"]), float(interval["interval"]["end"])
        duration = end - begin
        require(duration > 0, "Non-positive aggregation interval")
        for eid, data in interval["edges"].items():
            numeric = lambda key: float(data[key]) if key in data else None
            rows.append({"begin_s": begin, "end_s": end, "edge": eid,
                         "entered_veh": numeric("entered"), "left_veh": numeric("left"),
                         "departed_veh": numeric("departed"), "arrived_veh": numeric("arrived"),
                         "flow_in_veh_h": float(data.get("entered", 0)) * 3600 / duration,
                         "flow_out_veh_h": float(data.get("left", 0)) * 3600 / duration,
                         "mean_vehicles": float(data.get("sampledSeconds", 0)) / duration,
                         "occupancy_pct": numeric("occupancy"), "density_veh_km": numeric("density"),
                         "speed_m_s": numeric("speed"), "waiting_time_vehicle_s": numeric("waitingTime"),
                         "time_loss_vehicle_s": numeric("timeLoss")})
    with (directory / "edge_indicators.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    temporal = canonical_summary(directory / "summary.xml")
    for r in temporal:
        require(int(r["inserted"]) == int(r["running"]) + int(r["ended"]), "Network vehicle conservation failed at " + r["time"])
    with (directory / "network_timeseries.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(temporal[0])); w.writeheader(); w.writerows(temporal)
    return {"max_vehicles_running": max(int(r["running"]) for r in temporal),
            "max_halting_vehicles": max(int(r["halting"]) for r in temporal),
            "aggregation_intervals": len({r["begin_s"] for r in rows}), "edge_interval_rows": len(rows),
            "max_edge_mean_vehicles": max(r["mean_vehicles"] for r in rows),
            "max_edge_occupancy_pct": max(r["occupancy_pct"] or 0 for r in rows),
            "mean_vehicles_definition": "sampledSeconds/interval_duration; per-edge time average, not queue length or CTM cell state.",
            "flow_definition": "3600*entered/interval_duration and 3600*left/interval_duration; departures/arrivals are reported separately.",
            "network_conservation_checked_each_step": True}, rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/pilot_controlled")
    parser.add_argument("--demand", default="scenarios/pilot_controlled/demand.json")
    args = parser.parse_args(argv)
    out = (ROOT / args.output).resolve()
    protected_roots = [ROOT / "outputs" / n for n in ("pilot_verified", "pilot", "intervention001", "intervention002")]
    require(out.is_relative_to(ROOT / "outputs") and out != ROOT / "outputs" and not any(out.is_relative_to(p) for p in protected_roots), "Output overlaps protected evidence or is outside outputs")
    require(not out.exists(), "Output exists: select a new directory")
    spec_path = (ROOT / args.demand).resolve(); spec = json.loads(spec_path.read_text())
    require(spec["sumo_version"] == "1.28.0", "This experiment pins SUMO 1.28.0")
    frozen = json.loads((REFERENCE / "manifest.json").read_text())
    for name in ("pilot.net.xml", "pilot.osm.xml", "pilot.rou.xml"):
        require(sha256(REFERENCE / name) == frozen["artifacts"][name]["sha256"], "Reference artifact changed: " + name)
    sources = json.loads((ROOT / "data/osm/sources.json").read_text())
    topology = next(s for s in sources["sources"] if s["id"] == "osm-sv-topology-20261014")
    topology_path = ROOT.parent / topology["path_from_dc_x"]
    require(sha256(topology_path) == topology["sha256"], "National topology source changed")
    prefix = Path("/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO")
    home = Path(os.environ.get("SUMO_HOME", prefix / "share/sumo"))
    binary_dir = home.parent.parent / "bin"
    env = {**os.environ, "SUMO_HOME": str(home), "PROJ_DATA": frozen["proj_database"]["path"].rsplit("/", 1)[0],
           "PROJ_NETWORK": "OFF", "PYTHONDONTWRITEBYTECODE": "1"}
    env["PATH"] = str(binary_dir) + ":/opt/homebrew/bin:" + env.get("PATH", "")
    require(sha256(Path(env["PROJ_DATA"]) / "proj.db") == frozen["proj_database"]["sha256"], "Pinned PROJ database changed")
    out.mkdir(parents=True); (out / "logs").mkdir()
    commands = []

    def run(stage, command, cwd=out):
        print(stage, flush=True)
        log = out / "logs" / (stage + ".log")
        with log.open("w") as handle:
            result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, timeout=600)
        commands.append({"stage": stage, "argv": list(map(str, command)), "cwd": str(cwd), "returncode": result.returncode})
        write_json(out / "commands.json", commands)
        require(result.returncode == 0, f"{stage} failed; inspect {log}")
        return log.read_text()

    versions = {}
    for name in ("sumo", "duarouter"):
        executable = shutil.which(name, path=env["PATH"])
        require(executable, "Missing " + name)
        text = run(name + "-version", [executable, "--version"])
        require(text.splitlines()[0] == f"Eclipse SUMO {name} 1.28.0", "Unexpected SUMO version")
        versions[name] = {"path": executable, "sha256": sha256(Path(executable)), "output": text}
    shutil.copyfile(REFERENCE / "pilot.net.xml", out / "controlled.net.xml")
    shutil.copyfile(spec_path, out / "demand_spec.json")
    net = Network(out / "controlled.net.xml", REFERENCE / "pilot.osm.xml")
    require([len(c) for c in net.weak] == [321, 21, 8], "Passenger graph differs from the reference; review permissions")
    connectivity = connectivity_report(net, topology_path, frozen["bbox_crs84"], out)
    for stream in spec["streams"]:
        require(shortest_path(net.graph, net.costs, stream["from"], stream["to"]), "Unreachable controlled OD: " + stream["id"])
    departures = generate_departures(spec)
    trips = ET.Element("routes"); ET.SubElement(trips, "vType", spec["vehicle_type"])
    for row in departures:
        ET.SubElement(trips, "trip", {k:row[k] for k in ("id", "depart", "from", "to")},
                      type=spec["vehicle_type"]["id"], departLane="best", departSpeed="0")
    ET.ElementTree(trips).write(out / "controlled.trips.xml", encoding="utf-8", xml_declaration=True)
    write_json(out / "arrival_schedule.json", departures)
    run("route-controlled-demand", [versions["duarouter"]["path"], "--net-file", out / "controlled.net.xml",
        "--route-files", out / "controlled.trips.xml", "--output-file", out / "controlled.rou.xml",
        "--routing-threads", "1", "--seed", str(spec["seed"]), "--error-log", out / "routing.errors.log"])
    vehicles = ET.parse(out / "controlled.rou.xml").getroot().findall("vehicle")
    requests = {d["id"]: d for d in departures}
    require({v.get("id") for v in vehicles} == set(requests), "Controlled requests were rejected or changed")
    stream_routes = {}; controlled_sequences = []
    for vehicle in vehicles:
        seq = vehicle.find("route").get("edges").split(); r = requests[vehicle.get("id")]
        net.check_route(seq)
        require(seq[0] == r["from"] and seq[-1] == r["to"] and Decimal(vehicle.get("depart")) == Decimal(r["depart"]), "OD or requested departure changed")
        if r["stream"] in stream_routes:
            require(stream_routes[r["stream"]] == seq, "A stream has multiple baseline routes; make route rules explicit")
        stream_routes[r["stream"]] = seq; controlled_sequences.append(seq)
    write_json(out / "controlled_movements.json", {"routes_by_stream": stream_routes,
        "lane_movements_by_stream": {sid: [c for a,b in zip(seq,seq[1:]) for c in net.connections if c["from"] == a and c["to"] == b] for sid,seq in stream_routes.items()},
        "requested": len(requests), "accepted": len(vehicles), "rejected_ids": []})
    old_sequences = [v.find("route").get("edges").split() for v in ET.parse(REFERENCE / "pilot.rou.xml").getroot().findall("vehicle")]
    attribute_report(net, old_sequences, controlled_sequences, out)
    candidates = candidate_report(net, spec["future_closure_candidates"], spec["streams"], stream_routes, out)
    # Validar secuencias alternativas en la red abierta: no se modifica ni cierra ningún enlace.
    alternatives = ET.Element("routes"); ET.SubElement(alternatives, "vType", spec["vehicle_type"])
    proposed = {}
    for index, candidate in enumerate(candidates):
        for od in candidate["ODs"]:
            vid = f'candidate{index+1}.{od["stream"]}'
            sequence = od["alternative_route_without_candidate"]["edges"]
            proposed[vid] = sequence
            vehicle = ET.SubElement(alternatives, "vehicle", id=vid, type=spec["vehicle_type"]["id"], depart="0")
            ET.SubElement(vehicle, "route", edges=" ".join(sequence))
    ET.ElementTree(alternatives).write(out/"alternative_paths_to_validate.rou.xml", encoding="utf-8", xml_declaration=True)
    run("validate-alternative-paths", [versions["duarouter"]["path"], "--net-file", out/"controlled.net.xml",
        "--route-files", out/"alternative_paths_to_validate.rou.xml", "--output-file", out/"alternative_paths_validated.rou.xml",
        "--skip-new-routes", "true", "--error-log", out/"alternative_validation.errors.log"])
    checked = {v.get("id"):v.find("route").get("edges").split() for v in ET.parse(out/"alternative_paths_validated.rou.xml").getroot().findall("vehicle")}
    require(checked == proposed, "Router rejected or changed an alternative sequence")
    write_json(out/"alternative_validation.json", {"paths":len(checked), "all_sequences_preserved":True,
        "strict_routing":True, "network_modified":False, "closure_simulation_executed":False})
    warning_review(net, REFERENCE, out)
    runs = []
    for name in ("base", "repeat"):
        directory = out / name; directory.mkdir()
        measures = ET.Element("additional")
        ET.SubElement(measures, "edgeData", id="controlled_edges", file="edge_data.xml",
                      period=str(spec["aggregation_period_s"]), excludeEmpty="false", trackVehicles="false", withInternal="false")
        ET.ElementTree(measures).write(directory / "edge_measures.add.xml", encoding="utf-8", xml_declaration=True)
        config = ET.Element("configuration")
        inp = ET.SubElement(config, "input")
        for tag,value in (("net-file", "../controlled.net.xml"), ("route-files", "../controlled.rou.xml"), ("additional-files", "edge_measures.add.xml")):
            ET.SubElement(inp, tag, value=value)
        time = ET.SubElement(config, "time")
        for tag,value in (("begin", "0"), ("end", str(spec["simulation_end_s"])), ("step-length", str(spec["step_length_s"]))):
            ET.SubElement(time, tag, value=value)
        ET.SubElement(ET.SubElement(config,"random_number"), "seed", value=str(spec["seed"]))
        output = ET.SubElement(config, "output")
        for tag,value in (("tripinfo-output","tripinfo.xml"),("summary-output","summary.xml"),("statistic-output","statistics.xml"),("collision-output","collisions.xml"),("tripinfo-output.write-unfinished","true")):
            ET.SubElement(output, tag, value=value)
        ET.ElementTree(config).write(directory / "controlled.sumocfg", encoding="utf-8", xml_declaration=True)
        run("sumo-" + name, [versions["sumo"]["path"], "-c", directory / "controlled.sumocfg",
                            "--no-step-log", "true", "--duration-log.statistics", "true", "--error-log", directory / "sumo.errors.log"], directory)
        metrics = collect_metrics(directory, len(requests), len(vehicles))
        indicators, _ = output_indicators(directory)
        per_stream = {}
        infos = canonical_tripinfo(directory / "tripinfo.xml")
        for stream in spec["streams"]:
            group = [v for vid,v in infos.items() if requests[vid]["stream"] == stream["id"]]
            per_stream[stream["id"]] = {"count": len(group), "mean_duration_s": sum(float(v["duration"]) for v in group)/len(group),
                "mean_time_loss_s": sum(float(v["timeLoss"]) for v in group)/len(group), "mean_waiting_time_s": sum(float(v["waitingTime"]) for v in group)/len(group)}
        metrics.update(indicators=indicators, per_stream=per_stream)
        write_json(directory / "metrics.json", metrics); runs.append(metrics)
    repeat = {"metrics_identical": runs[0] == runs[1],
              "all_vehicle_attributes_identical": canonical_tripinfo(out/"base/tripinfo.xml") == canonical_tripinfo(out/"repeat/tripinfo.xml"),
              "edge_interval_attributes_identical": canonical_edge_data(out/"base/edge_data.xml") == canonical_edge_data(out/"repeat/edge_data.xml"),
              "network_time_series_identical_excluding_cpu_duration": canonical_summary(out/"base/summary.xml") == canonical_summary(out/"repeat/summary.xml"),
              "configurations_identical": sha256(out/"base/controlled.sumocfg") == sha256(out/"repeat/controlled.sumocfg")}
    write_json(out / "reproducibility.json", repeat); require(all(repeat.values()), "Controlled repetition differs")
    warning_report = {p: warning_summary(out/p) for p in ("routing.errors.log","alternative_validation.errors.log","base/sumo.errors.log","repeat/sumo.errors.log")}
    write_json(out / "warnings.json", warning_report)
    final = {"technical_success": True, "scenario": "controlled_synthetic_base_no_closure", "calibrated": False,
             "network_hash_identical_to_002": sha256(out/"controlled.net.xml") == frozen["artifacts"]["pilot.net.xml"]["sha256"],
             "requested": len(requests), "accepted": len(vehicles), "base": {k:v for k,v in runs[0].items() if k != "per_vehicle"},
             "reproducibility": repeat, "closure_simulated": False}
    write_json(out / "summary.json", final)
    artifacts = ["controlled.net.xml","demand_spec.json","controlled.trips.xml","controlled.rou.xml","base/controlled.sumocfg","base/edge_measures.add.xml","repeat/controlled.sumocfg","repeat/edge_measures.add.xml"]
    write_json(out / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(),
        "reference_manifest": str(REFERENCE/"manifest.json"), "reference_manifest_sha256": sha256(REFERENCE/"manifest.json"),
        "source_osm": frozen["source"], "source_topology": topology, "proj_database": frozen["proj_database"],
        "tools": versions, "python": sys.version, "demand": spec,
        "code_sha256": {p.name:sha256(p) for p in (Path(__file__), Path(__file__).with_name("diagnostics.py"),Path(__file__).with_name("pilot.py"),Path(__file__).with_name("doctor.py"),Path(__file__).with_name("plots.py"))},
        "artifacts": {p:{"sha256":sha256(out/p),"bytes":(out/p).stat().st_size} for p in artifacts},
        "network_changes": [], "observational_inputs": [], "boundary_and_demand_for_future_comparison": "Keep OD, departures, vehicle IDs/types, seeds, horizon, network attributes and signal programs fixed; specify route-reassignment policy separately."})
    (out / "ATTRIBUTION.txt").write_text((REFERENCE/"ATTRIBUTION.txt").read_text())
    from .plots import render
    render(net, out, spec, candidates)
    print(json.dumps({"output":str(out),"completed":runs[0]["completed_vehicles"],"requested":len(requests),"reproducible":True}),flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
