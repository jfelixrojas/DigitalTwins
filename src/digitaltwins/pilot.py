"""Construir, auditar y repetir el piloto local; sin instalaciones ni acceso de red."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from .doctor import sha256


ROOT = Path(__file__).resolve().parents[2]
SUMO_VERSION = "1.28.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def tags(element):
    return {t.get("k"): t.get("v") for t in element.findall("tag")}


def audit_osm(path):
    """Examinar el recorte y la completitud de sus restricciones, sin inferir datos."""
    root = ET.parse(path).getroot()
    ids = {kind: {e.get("id") for e in root.findall(kind)} for kind in ("node", "way", "relation")}
    ways = {e.get("id"): tags(e) for e in root.findall("way")}
    roads = {k: v for k, v in ways.items() if "highway" in v}
    restrictions = []
    for rel in root.findall("relation"):
        t = tags(rel)
        if t.get("type") != "restriction":
            continue
        members = [dict(m.attrib) for m in rel.findall("member")]
        missing = [m for m in members if m["ref"] not in ids.get(m["type"], set())]
        restrictions.append({"id": rel.get("id"), "tags": t, "members": members,
                             "missing_members": missing})
    return {
        "objects": {k: len(v) for k, v in ids.items()},
        "highway_ways": len(roads),
        "highway_classes": dict(Counter(t["highway"] for t in roads.values())),
        "highway_tag_counts": {k: sum(k in t for t in roads.values()) for k in
                               ("oneway", "lanes", "maxspeed", "junction", "turn:lanes", "access")},
        "traffic_signal_nodes": sum(tags(n).get("highway") == "traffic_signals" for n in root.findall("node")),
        "restrictions": restrictions,
        "incomplete_restrictions": sum(bool(r["missing_members"]) for r in restrictions),
    }


def passenger_allowed(lane):
    allow, disallow = lane.get("allow", "").split(), lane.get("disallow", "").split()
    return (not allow or "all" in allow or "passenger" in allow) and not ({"all", "passenger"} & set(disallow))


def audit_network(path, osm):
    root = ET.parse(path).getroot()
    edges = {e.get("id"): e for e in root.findall("edge") if e.get("function") != "internal"}
    lanes = {e: {l.get("index") for l in edge.findall("lane") if passenger_allowed(l)} for e, edge in edges.items()}
    graph = {e: set() for e in edges if lanes[e]}
    connections = [c for c in root.findall("connection") if c.get("from") in graph
                   and c.get("to") in graph and c.get("fromLane") in lanes[c.get("from")]
                   and c.get("toLane") in lanes[c.get("to")]]
    for c in connections:
        graph[c.get("from")].add(c.get("to"))
    undirected = {e: set(v) for e, v in graph.items()}
    for e, values in graph.items():
        for v in values:
            undirected[v].add(e)
    unseen, sizes = set(graph), []
    while unseen:
        stack = [unseen.pop()]; size = 0
        while stack:
            e = stack.pop(); size += 1
            next_edges = undirected[e] & unseen
            unseen.difference_update(next_edges); stack.extend(next_edges)
        sizes.append(size)

    by_osm = defaultdict(set)
    for eid, edge in edges.items():
        originals = [eid] + [p.get("value", "") for p in edge.iter("param") if p.get("key") == "origId"]
        for value in originals:
            for token in re.split(r"[;\s]+", value):
                match = re.match(r"^-?(\d+)(?:#|$)", token)
                if match:
                    by_osm[match[1]].add(eid)
    checks = []
    for rel in osm["restrictions"]:
        roles = defaultdict(list)
        for m in rel["members"]:
            roles[m.get("role", "")].append(m)
        row = {"relation_id": rel["id"], "restriction": rel["tags"].get("restriction"),
               "members": rel["members"]}
        if rel["missing_members"]:
            row["status"] = "incomplete_source_relation"
        elif len(roles["from"]) != 1 or len(roles["to"]) != 1 or len(roles["via"]) != 1:
            row["status"] = "manual_check_member_arity"
        elif roles["via"][0]["type"] != "node":
            row["status"] = "manual_check_via_way"
        else:
            start = by_osm[roles["from"][0]["ref"]]
            end = by_osm[roles["to"][0]["ref"]]
            via = roles["via"][0]["ref"]
            outgoing = [c for c in connections if c.get("from") in start
                        and edges[c.get("from")].get("to") == via]
            relevant = [c for c in outgoing if c.get("to") in end and edges[c.get("to")].get("from") == via]
            restriction = row["restriction"] or ""
            if not start or not end:
                row["status"] = "outside_retained_passenger_network"
            elif not any(edges[e].get("to") == via for e in start) or not any(edges[e].get("from") == via for e in end):
                row["status"] = "manual_check_unmapped_via_node"
            elif set(re.split(r"[;,\s]+", rel["tags"].get("except", ""))) & {"motorcar", "motor_vehicle", "vehicle"}:
                row["status"] = "passenger_exempt"
            elif restriction.startswith("no_"):
                forbidden = [c for c in relevant if restriction != "no_u_turn" or c.get("dir") == "t"]
                row.update(status="violation" if forbidden else "respected", forbidden_connections=[dict(c.attrib) for c in forbidden])
            elif restriction.startswith("only_"):
                forbidden = [c for c in outgoing if c.get("to") not in end]
                row.update(status="violation" if forbidden else ("respected" if relevant else "manual_check_no_allowed_movement"), forbidden_connections=[dict(c.attrib) for c in forbidden])
            else:
                row["status"] = "manual_check_unsupported_tag"
            row["via_node_id"] = via
        checks.append(row)
    junctions = [j for j in root.findall("junction") if j.get("type") != "internal"]
    defaults = Counter(p.get("key") for p in root.iter("param") if "default" in p.get("key", "").lower())
    summary = {
        "edges_external": len(edges),
        "edges_internal": sum(e.get("function") == "internal" for e in root.findall("edge")),
        "lanes_external": sum(len(e.findall("lane")) for e in edges.values()),
        "junctions_external_including_dead_ends": len(junctions),
        "junction_types": dict(Counter(j.get("type") for j in junctions)),
        "connections_total_including_internal": len(root.findall("connection")),
        "passenger_lane_connections_external": len(connections),
        "passenger_edges": len(graph), "weak_component_edge_counts": sorted(sizes, reverse=True),
        "traffic_light_programs": [{**t.attrib, "phase_count": len(t.findall("phase"))} for t in root.findall("tlLogic")],
        "traffic_light_junction_ids": [j.get("id") for j in junctions if j.get("type", "").startswith("traffic_light")],
        "default_parameter_counts": dict(defaults),
        "restriction_checks": checks,
        "restriction_violations": sum(c["status"] == "violation" for c in checks),
    }
    return summary, graph


def route_records(path, kind):
    return {e.get("id"): e for e in ET.parse(path).getroot().findall(kind)}


def request_diagnostics(graph, requested, accepted):
    undirected = {e: set(v) for e, v in graph.items()}
    for e, neighbors in graph.items():
        for n in neighbors:
            undirected[n].add(e)
    components = {}
    for start in graph:
        if start in components:
            continue
        label = start; stack = [start]
        while stack:
            node = stack.pop()
            if node in components:
                continue
            components[node] = label; stack.extend(undirected[node] - components.keys())
    rejected = []
    for vid in sorted(set(requested) - set(accepted)):
        trip = requested[vid]; start, end = trip.get("from"), trip.get("to")
        seen, stack = set(), [start]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node); stack.extend(graph.get(node, set()) - seen)
        reason = ("different_weak_components" if components.get(start) != components.get(end)
                  else "no_directed_path" if end not in seen else "router_rejection_requires_review")
        rejected.append({"id": vid, "from": start, "to": end, "reason": reason})
    return {"rejected": rejected, "rejection_reason_counts": dict(Counter(r["reason"] for r in rejected))}


def warning_summary(path):
    lines = path.read_text().splitlines() if path.exists() else []
    return {"warning_lines": sum(l.startswith("Warning:") for l in lines),
            "error_lines": sum(l.startswith("Error:") for l in lines),
            "aggregated_groups": [{"count": int(m.group(1)), "type": m.group(2)} for line in lines
                if (m := re.match(r"Warning: (\d+) total messages of type: (.*)", line))],
            "messages": lines}


def collect_metrics(directory, requested_count, accepted_count):
    statistics = ET.parse(directory / "statistics.xml").getroot()
    vehicles = statistics.find("vehicles")
    require(vehicles is not None, "SUMO statistics missing vehicles")
    trips = ET.parse(directory / "tripinfo.xml").getroot().findall("tripinfo")
    arrived = [t for t in trips if float(t.get("arrival", "-1")) >= 0 and not t.get("vaporized")]
    unfinished = [t for t in trips if float(t.get("arrival", "-1")) < 0]
    removed = [t for t in trips if float(t.get("arrival", "-1")) >= 0 and t.get("vaporized")]
    inserted = int(vehicles.get("inserted"))
    running, waiting = int(vehicles.get("running")), int(vehicles.get("waiting"))
    per_vehicle = [{k: t.get(k) for k in ("id", "depart", "arrival", "duration", "waitingTime", "timeLoss", "departDelay", "routeLength", "vaporized")}
                   for t in sorted(trips, key=lambda t: t.get("id"))]
    final_step = ET.parse(directory / "summary.xml").getroot().findall("step")[-1]
    result = {
        "requested_trips": requested_count, "valid_routes": accepted_count,
        "rejected_trips": requested_count - accepted_count,
        "loaded_vehicles": int(vehicles.get("loaded")), "inserted_vehicles": inserted,
        "completed_vehicles": len(arrived), "running_at_end": running,
        "waiting_to_depart_at_end": waiting, "pending_at_end": running + waiting,
        "removed_vehicles": len(removed), "unfinished_tripinfo_records": len(unfinished),
        "teleports": dict(statistics.find("teleports").attrib),
        "safety": dict(statistics.find("safety").attrib),
        "trip_statistics": dict(statistics.find("vehicleTripStatistics").attrib),
        "final_summary": dict(final_step.attrib), "per_vehicle": per_vehicle,
    }
    # Las duraciones de CPU/reloj y las marcas de generación XML no son métricas reproducibles.
    for key in ("duration",):
        result["final_summary"].pop(key, None)
    require(0 < accepted_count <= requested_count, "No valid routes or inconsistent routing counts")
    require(result["loaded_vehicles"] == accepted_count, "Accepted routes and loaded vehicles differ")
    require(inserted == len(arrived) + running + len(removed), "Inserted vehicle balance failed")
    require(accepted_count == inserted + waiting, "Loaded vehicle balance failed")
    require(len(arrived) > 0, "No vehicle completed its route")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/pilot")
    parser.add_argument("--bbox", default=None, help="oeste,sur,este,norte; justificar cambios en el informe")
    args = parser.parse_args(argv)
    out = (ROOT / args.output).resolve()
    require(out.is_relative_to(ROOT / "outputs") and out != ROOT / "outputs", "Output must be a child of DigitalTwins/outputs")
    require(not out.exists(), "Output already exists; choose a new directory to preserve evidence")
    manifest_path = ROOT / "data/osm/sources.json"
    source_manifest = json.loads(manifest_path.read_text())
    source = next(s for s in source_manifest["sources"] if s["id"] == source_manifest["recommended_source_id"])
    source_path = ROOT.parent / source["path_from_dc_x"]
    require(source_path.stat().st_size == source["size_bytes"] and sha256(source_path) == source["sha256"], "Original PBF hash mismatch")
    bbox = [float(v) for v in args.bbox.split(",")] if args.bbox else source_manifest["pilot_candidate"]["bbox_crs84"]
    require(len(bbox) == 4 and bbox[0] < bbox[2] and bbox[1] < bbox[3], "Invalid bbox")
    home = Path(os.environ.get("SUMO_HOME", "/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/share/sumo"))
    require((home / "tools/randomTrips.py").is_file(), "SUMO_HOME/tools/randomTrips.py is missing")
    prefix = home.parent.parent
    env = {**os.environ, "SUMO_HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1", "PROJ_NETWORK": "OFF"}
    env["PATH"] = str(prefix / "bin") + os.pathsep + "/opt/homebrew/bin" + os.pathsep + env.get("PATH", "")
    proj_candidates = [Path(env["PROJ_DATA"])] if env.get("PROJ_DATA") else []
    proj_candidates.append(home.parent / "proj")
    pyproj = importlib.util.find_spec("pyproj")
    if pyproj and pyproj.origin:
        proj_candidates.append(Path(pyproj.origin).parent / "proj_dir/share/proj")
    proj_data = next((p for p in proj_candidates if (p / "proj.db").is_file()), None)
    require(proj_data is not None, "PROJ proj.db missing; set PROJ_DATA to an existing compatible data directory")
    env["PROJ_DATA"] = str(proj_data)
    tools = {name: shutil.which(name, path=env["PATH"]) for name in ("sumo", "netconvert", "duarouter", "osmium")}
    require(all(tools.values()), "Required command missing: " + str(tools))
    out.mkdir(parents=True)
    (out / "logs").mkdir()
    commands = []

    def run(name, command):
        print(name, flush=True)
        log = out / "logs" / (name + ".log")
        with log.open("w") as handle:
            process = subprocess.run([str(x) for x in command], cwd=out, env=env,
                                     stdout=handle, stderr=subprocess.STDOUT, timeout=600)
        commands.append({"stage": name, "argv": [str(x) for x in command], "cwd": str(out),
                         "returncode": process.returncode, "log": str(log.relative_to(out))})
        write_json(out / "commands.json", commands)
        require(process.returncode == 0, f"{name} failed ({process.returncode}); see {log}")
        return log.read_text()

    versions = {}
    for name, command in tools.items():
        text = run(name + "-version", [command, "--version"])
        if name != "osmium":
            require(re.search(r"^Eclipse SUMO " + name + r" (?:Version )?" + re.escape(SUMO_VERSION) + r"(?:\s|$)", text, re.MULTILINE), name + " is not SUMO " + SUMO_VERSION)
        versions[name] = {"path": command, "sha256": sha256(Path(command)), "version_output": text}
    write_json(out / "environment.json", {"python": sys.version, "executable": sys.executable,
                                         "SUMO_HOME": str(home), "PROJ_DATA": env.get("PROJ_DATA"), "tools": versions})
    run("extract", [tools["osmium"], "extract", "--bbox=" + ",".join(map(str, bbox)),
                    "--strategy=smart", "-S", "types=restriction", source_path, "-o", out / "pilot.osm.pbf"])
    run("convert-osm-xml", [tools["osmium"], "cat", out / "pilot.osm.pbf", "-o", out / "pilot.osm.xml"])
    run("check-node-references", [tools["osmium"], "check-refs", out / "pilot.osm.pbf"])
    osm = audit_osm(out / "pilot.osm.xml")
    write_json(out / "osm_audit.json", osm)
    require(osm["incomplete_restrictions"] == 0, "Extract has incomplete turn restrictions")
    run("netconvert", [tools["netconvert"], "--osm-files", out / "pilot.osm.xml", "--keep-edges.by-vclass", "passenger",
                       "--osm.turn-lanes", "true", "--osm.annotate-defaults", "true", "--output.original-names", "true",
                       "--output-file", out / "pilot.net.xml", "--error-log", out / "netconvert.errors.log"])
    network, graph = audit_network(out / "pilot.net.xml", osm)
    write_json(out / "network_audit.json", network)
    require(network["edges_external"] > 0 and network["passenger_lane_connections_external"] > 0, "Network empty or no usable movements")
    require(network["restriction_violations"] == 0, "A mapped turn restriction was violated")
    trip_command = [sys.executable, "-B", home / "tools/randomTrips.py", "-n", out / "pilot.net.xml",
                    "-b", "0", "-e", "900", "-p", "6", "--seed", "42", "--vehicle-class", "passenger"]
    run("requested-demand", trip_command + ["-o", out / "requested.trips.xml", "--no-validate"])
    # SUMO 1.28 redibuja OD fallidos por defecto. El umbral 1 conserva el rechazo
    # original: nunca redibuja para llenar la cuota y permite un balance auditable.
    run("validated-demand", trip_command + ["-o", out / "pilot.trips.xml", "-r", out / "pilot.rou.xml",
        "--validate", "--min-success-rate", "1", "--threads", "1", "--verbose", "--error-log", out / "routing.errors.log"])
    requested = route_records(out / "requested.trips.xml", "trip")
    accepted = route_records(out / "pilot.rou.xml", "vehicle")
    require(len(requested) == 150, "Expected 150 requested trips")
    require(set(accepted) <= set(requested), "Routing introduced trips outside the original request")
    for vehicle in accepted.values():
        route = vehicle.find("route")
        require(route is not None, "Vehicle missing route")
        route_edges = route.get("edges").split()
        require(route_edges and all(e in graph for e in route_edges), "Route has non-passenger or unknown edges")
        require(all(b in graph[a] for a, b in zip(route_edges, route_edges[1:])), "Route has an invalid movement")
    write_json(out / "routing_audit.json", {"requested": len(requested), "accepted": len(accepted),
        "rejected_ids": sorted(set(requested) - set(accepted)), "all_accepted_routes_checked": True,
        "resampling_disabled": True,
        **request_diagnostics(graph, requested, accepted),
        "router_policy": "Official randomTrips uses ignore-errors internally; all diagnostics retained. SUMO simulation remains strict."})
    metrics = []
    for name in ("base", "repeat"):
        directory = out / name; directory.mkdir()
        config = ET.parse(ROOT / "scenarios/pilot/pilot.sumocfg")
        config.find("./input/net-file").set("value", "../pilot.net.xml")
        config.find("./input/route-files").set("value", "../pilot.rou.xml")
        output = config.find("./output")
        output.find("tripinfo-output").set("value", "tripinfo.xml")
        output.find("summary-output").set("value", "summary.xml")
        for tag, value in (("statistic-output", "statistics.xml"), ("collision-output", "collisions.xml"),
                           ("tripinfo-output.write-unfinished", "true")):
            ET.SubElement(output, tag, value=value)
        config.write(directory / "pilot.sumocfg", encoding="utf-8", xml_declaration=True)
        run("sumo-" + name, [tools["sumo"], "-c", directory / "pilot.sumocfg", "--no-step-log", "true",
                            "--duration-log.statistics", "true", "--error-log", directory / "sumo.errors.log"])
        metric = collect_metrics(directory, len(requested), len(accepted))
        write_json(directory / "metrics.json", metric); metrics.append(metric)
    same = metrics[0] == metrics[1]
    write_json(out / "reproducibility.json", {"metrics_identical": same,
        "configurations_identical": sha256(out / "base/pilot.sumocfg") == sha256(out / "repeat/pilot.sumocfg"),
        "comparison": "Parsed counts, safety, teleport statistics and per-vehicle metrics; excludes wall-clock performance and XML headers."})
    require(same, "Repeated run metrics differ; inspect both reports")
    warnings = {name: warning_summary(out / name) for name in
                ("netconvert.errors.log", "routing.errors.log", "base/sumo.errors.log", "repeat/sumo.errors.log")}
    write_json(out / "warnings.json", warnings)
    require(not any("Cannot find proj.db" in p.read_text() for p in (out / "logs").glob("*.log")), "PROJ database still unavailable; inspect logs")
    artifacts = ["pilot.osm.pbf", "pilot.osm.xml", "pilot.net.xml", "requested.trips.xml", "pilot.trips.xml", "pilot.rou.xml",
                 "base/pilot.sumocfg", "repeat/pilot.sumocfg"]
    inputs = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "source": source,
              "source_manifest_sha256": sha256(manifest_path), "runner_sha256": sha256(Path(__file__)),
              "bbox_crs84": bbox, "seed": 42, "begin": 0, "demand_end": 900, "period": 6, "simulation_end": 1800,
              "randomTrips_sha256": sha256(home / "tools/randomTrips.py"),
              "typemap_sha256": sha256(home / "data/typemap/osmNetconvert.typ.xml"),
              "proj_database": {"path": str(proj_data / "proj.db"), "sha256": sha256(proj_data / "proj.db"),
                                "origin": "Existing runtime data; no download or modification"},
              "artifacts": {p: {"sha256": sha256(out / p), "size_bytes": (out / p).stat().st_size} for p in artifacts},
              "assumptions": ["Synthetic passenger demand, not calibrated traffic observations.",
                              "Default network attributes and traffic light programs are inferred, not observed.",
                              "No closures, operational sources, CTM, LTM or AI.",
                              "Validation preserves rejected OD requests instead of resampling them."]}
    require(sha256(source_path) == source["sha256"], "Original PBF changed during run")
    write_json(out / "manifest.json", inputs)
    write_json(out / "summary.json", {"technical_success": True, "calibrated_digital_twin": False,
        "network": network, "base": {k: v for k, v in metrics[0].items() if k != "per_vehicle"}, "repeat_identical": same})
    (out / "ATTRIBUTION.txt").write_text("© OpenStreetMap contributors. Processed by Geofabrik GmbH.\nODbL 1.0: https://opendatacommons.org/licenses/odbl/1-0/\nSource: Geofabrik El Salvador, 2026-10-14; see manifest.json.\n")
    print(json.dumps({"technical_success": True, "output": str(out), "requested": len(requested),
                      "accepted": len(accepted), "completed": metrics[0]["completed_vehicles"], "repeat_identical": same}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
