"""Cierre virtual efectivo, observación local y comparación reproducible con la 003."""

import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from .closure_analysis import analyze, normalized_tripinfo
from .controlled import canonical_edge_data, canonical_summary, canonical_tripinfo, output_indicators
from .diagnostics import Network, shortest_path
from .doctor import sha256
from .pilot import require, warning_summary, write_json

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "outputs/pilot_controlled_verified"
SCENARIO = ROOT / "scenarios/closure_experiment"


def validate_routes(vehicles, requests, net, closed_edge=None):
    """Validación estricta independiente del modo de permisos transitorios de SUMO."""
    require(len(vehicles) == len(requests), "Vehicle count changed")
    require({v.get("id") for v in vehicles} == set(requests), "Vehicle IDs changed")
    for v in vehicles:
        request = requests[v.get("id")]; route = v.find("route").get("edges").split()
        net.check_route(route)
        require(route[0] == request["from"] and route[-1] == request["to"], "OD changed")
        require(float(v.get("depart")) == float(request["depart"]), "Scheduled departure changed")
        if closed_edge:
            require(closed_edge not in route, "Alternative uses closed edge")


def prepare_routes(net, route_path, requests, spec, out):
    original = ET.parse(route_path); vehicles = original.getroot().findall("vehicle")
    validate_routes(vehicles, requests, net)
    exposed = {v.get("id") for v in vehicles if spec["closed_edge"] in v.find("route").get("edges").split()}
    require(len(exposed) == 45 and all(requests[v]["stream"] == "W_E" for v in exposed), "Unexpected exposed population")
    target = net.edges[spec["closed_edge"]]
    disallowed = {l.get("disallow", "") for l in target.findall("lane")}
    require(len(disallowed) == 1 and not any(l.get("allow") for l in target.findall("lane")), "Review differing target permissions")
    original_disallowed = next(iter(disallowed)).split()
    closing = ET.parse(SCENARIO / "closure.add.xml")
    rerouter = closing.getroot().find("rerouter"); interval = rerouter.find("interval"); rule = interval.find("closingReroute")
    require(rerouter.get("edges").split() == spec["trigger_edges"] and rerouter.get("probability") == "1", "Unexpected rerouter")
    require(float(interval.get("begin")) == spec["begin_s"] and float(interval.get("end")) == spec["end_s"], "Closure interval differs")
    require(rule.get("id") == spec["closed_edge"] and set(rule.get("disallow").split()) == set(original_disallowed) | {spec["closed_class"]}, "Closure must only subtract passenger permission")
    require(len(closing.getroot().findall("rerouter")) == 1 and len(interval) == 1, "Only one closure action is permitted")
    shutil.copyfile(SCENARIO / "closure.add.xml", out / "closure.add.xml")
    proposed = deepcopy(original)
    for vehicle in proposed.getroot().findall("vehicle"):
        if vehicle.get("id") in exposed:
            sequence = vehicle.find("route").get("edges").split()
            # El punto de información está en el origen, antes de cualquier desvío.
            require(sequence[0] in spec["trigger_edges"], "Rerouter does not precede detour")
            alternative = shortest_path(net.graph, net.costs, sequence[0], sequence[-1], spec["closed_edge"])
            require(alternative is not None, "An exposed destination became unreachable")
            vehicle.find("route").set("edges", " ".join(alternative["edges"]))
    validate_routes(proposed.getroot().findall("vehicle"), requests, net, spec["closed_edge"])
    proposed.write(out / "proposed_alternatives.rou.xml", encoding="utf-8", xml_declaration=True)
    # Variante solo para validación estática con duarouter; nunca se simula con ella.
    validation_net = deepcopy(net.xml)
    for edge in validation_net.findall("edge"):
        if edge.get("id") == spec["closed_edge"]:
            for lane in edge.findall("lane"):
                lane.set("disallow", rule.get("disallow"))
    ET.ElementTree(validation_net).write(out / "validation_only_closed.net.xml", encoding="utf-8", xml_declaration=True)
    return exposed


def observe_run(directory, executable, env, spec, commands):
    """Solo pasos de simulación y getters TraCI; no se envían setters de control."""
    home = Path(env["SUMO_HOME"]); sys.path.insert(0, str(home / "tools"))
    import traci
    from sumolib.miscutils import getFreeSocketPort
    port = getFreeSocketPort()
    require(port is not None, "Local TraCI socket unavailable; SUMO needs permission for a temporary localhost port")
    original_env = dict(os.environ); original_cwd = Path.cwd()
    command = [executable, "-c", "controlled.sumocfg", "--no-step-log", "true", "--duration-log.statistics", "true", "--error-log", "sumo.errors.log"]
    entry = {"stage": directory.name, "argv": command + ["--remote-port", str(port)], "cwd": str(directory),
             "transport": "temporary local TraCI, simulationStep and read-only getters"}
    commands.append(entry); write_json(directory.parent / "commands.json", commands)
    connection = None; changes = []; passage_ids = set(); bad_permissions = []
    target_lanes = []
    try:
        os.environ.update(env); os.chdir(directory)
        with (directory / "sumo.log").open("w") as log, (directory / "permission_monitor.csv").open("w", newline="") as output:
            traci.start(command, port=port, label=directory.name, stdout=log)
            connection = traci.getConnection(directory.name)
            entry["traci_version"] = list(connection.getVersion())
            require(not connection.vehicle.getIDList(), "Initial state must contain no inserted vehicles")
            all_lanes = sorted(connection.lane.getIDList())
            target_lanes = [l for l in all_lanes if connection.lane.getEdgeID(l) == spec["closed_edge"]]
            require(len(target_lanes) == 2, "Expected both closed edge lanes")
            snapshot = lambda: {l: sorted(connection.lane.getDisallowed(l)) for l in all_lanes}
            initial = snapshot(); first = None
            writer = csv.DictWriter(output, fieldnames=["step_end_s", "lane", "passenger_allowed", "disallowed_classes", "vehicle_ids"])
            writer.writeheader(); prior = {l: initial[l] for l in target_lanes}
            for step in range(spec["end_s"]):
                connection.simulationStep()
                require(connection.simulation.getTime() == step + 1, "Unexpected simulation step")
                if step == 0:
                    first = snapshot()
                for lane in target_lanes:
                    forbidden = sorted(connection.lane.getDisallowed(lane)); ids = list(connection.lane.getLastStepVehicleIDs(lane))
                    writer.writerow({"step_end_s": step + 1, "lane": lane, "passenger_allowed": int("passenger" not in forbidden),
                                     "disallowed_classes": " ".join(forbidden), "vehicle_ids": " ".join(ids)})
                    if forbidden != prior[lane]:
                        changes.append({"first_step_end_s": step + 1, "lane": lane, "before": prior[lane], "after": forbidden}); prior[lane] = forbidden
                    passage_ids.update(ids)
                    if directory.name != "base" and "passenger" not in forbidden:
                        bad_permissions.append([step + 1, lane])
            last = snapshot()
            connection.close(); connection = None
        closure = directory.name != "base"
        expected = {l: sorted(set(v) | ({"passenger"} if closure and l in target_lanes else set())) for l, v in initial.items()}
        write_json(directory / "permission_snapshots.json", {"initial_before_scheduler": initial, "after_first_step": first, "after_last_step": last})
        monitor = {"steps": spec["end_s"], "step_length_s": 1, "target_lanes": target_lanes,
                   "samples": spec["end_s"] * len(target_lanes), "permission_violation_samples": bad_permissions,
                   "unique_vehicles_seen_on_target": sorted(passage_ids), "permission_changes": changes,
                   "all_lane_permissions_match_expected_first_and_last": first == expected and last == expected,
                   "initial_snapshot_note": "Before time-0 events and insertion; first post-step sample covers [0,1). No vehicles exist before the scheduler starts."}
        write_json(directory / "closure_monitor.json", monitor)
        require(first == expected and last == expected and not bad_permissions, "Unexpected lane permission change")
        if closure:
            require(not passage_ids, "A vehicle traversed the closed edge")
        entry["completed_monitor_loop"] = True
    finally:
        if connection is not None:
            connection.close()
        os.chdir(original_cwd); os.environ.clear(); os.environ.update(original_env)
        write_json(directory.parent / "commands.json", commands)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/closure_experiment")
    args = parser.parse_args(argv); out = (ROOT / args.output).resolve()
    require(out.parent == ROOT / "outputs" and not out.exists(), "Select a NEW direct child of DigitalTwins/outputs")
    spec = json.loads((SCENARIO / "experiment.json").read_text())
    require(spec["reference"] == str(REFERENCE.relative_to(ROOT)) and spec["sumo_version"] == "1.28.0", "Unexpected reference/version")
    require(spec["closed_edge"] == "1257993561#5" and spec["closed_class"] == "passenger" and
            (spec["begin_s"], spec["end_s"], spec["routing_mode_closure"]) == (0, 1800, 8), "Scope differs from approved experiment")
    frozen = json.loads((REFERENCE / "manifest.json").read_text())
    for name, expected in frozen["artifacts"].items():
        require(sha256(REFERENCE / name) == expected["sha256"], "Reference artifact changed: " + name)
    for name, digest in frozen["code_sha256"].items():
        require(sha256(ROOT / "src/digitaltwins" / name) == digest, "Legacy source differs: " + name)
    home = Path(os.environ.get("SUMO_HOME", "/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/share/sumo"))
    env = {**os.environ, "SUMO_HOME": str(home), "PROJ_NETWORK": "OFF", "PYTHONDONTWRITEBYTECODE": "1",
           "PROJ_DATA": str(Path(frozen["proj_database"]["path"]).parent)}
    env["PATH"] = str(home.parent.parent / "bin") + os.pathsep + env.get("PATH", "")
    require(sha256(Path(env["PROJ_DATA"]) / "proj.db") == frozen["proj_database"]["sha256"], "PROJ data changed")
    out.mkdir(); (out / "logs").mkdir(); commands = []; tools = {}
    def run(stage, command):
        with (out / "logs" / (stage + ".log")).open("w") as log:
            result = subprocess.run(list(map(str, command)), cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        commands.append({"stage": stage, "argv": list(map(str, command)), "cwd": str(out), "returncode": result.returncode})
        write_json(out / "commands.json", commands)
        require(result.returncode == 0, "Stage failed, raw evidence retained: " + stage)
        return (out / "logs" / (stage + ".log")).read_text()
    for name in ("sumo", "duarouter"):
        path = shutil.which(name, path=env["PATH"]); require(path, "Missing " + name)
        text = run(name + "-version", [path, "--version"])
        require(text.splitlines()[0] == f"Eclipse SUMO {name} 1.28.0", "Version differs")
        require(sha256(Path(path)) == frozen["tools"][name]["sha256"], "Tool binary differs from 003")
        tools[name] = {"path": path, "sha256": sha256(Path(path)), "version_output": text}
    for name in ("controlled.net.xml", "controlled.rou.xml", "controlled.trips.xml", "arrival_schedule.json", "demand_spec.json", "ATTRIBUTION.txt"):
        shutil.copyfile(REFERENCE / name, out / name)
        require(sha256(REFERENCE / name) == sha256(out / name), "Copied input differs: " + name)
    shutil.copyfile(SCENARIO / "experiment.json", out / "experiment_spec.json")
    demand = json.loads((out / "demand_spec.json").read_text())
    require((demand["seed"], demand["step_length_s"], demand["simulation_end_s"]) == (42, 1, 1800), "Reference conditions differ")
    schedule = json.loads((out / "arrival_schedule.json").read_text()); requests = {r["id"]: r for r in schedule}
    require(len(requests) == len(schedule) == 150, "Demand differs")
    net = Network(out / "controlled.net.xml", ROOT / "outputs/pilot_verified/pilot.osm.xml")
    exposed = prepare_routes(net, out / "controlled.rou.xml", requests, spec, out)
    run("strict-alternative-validation", [tools["duarouter"]["path"], "--net-file", out / "validation_only_closed.net.xml",
        "--route-files", out / "proposed_alternatives.rou.xml", "--output-file", out / "validated_alternatives.rou.xml",
        "--skip-new-routes", "true", "--error-log", out / "validation.errors.log"])
    proposed = ET.parse(out / "proposed_alternatives.rou.xml").getroot().findall("vehicle")
    checked = ET.parse(out / "validated_alternatives.rou.xml").getroot().findall("vehicle")
    validate_routes(checked, requests, net, spec["closed_edge"])
    require({v.get("id"): v.find("route").get("edges") for v in proposed} ==
            {v.get("id"): v.find("route").get("edges") for v in checked}, "Strict router changed a proposal")
    write_json(out / "demand_validation.json", {"requests": 150, "ODs": 6, "exposed_ids": sorted(exposed),
        "all_original_ids_ODs_and_departures_preserved": True, "proposed_alternatives_strictly_validated": 150,
        "all_ODs_reachable_without_closed_edge": True, "alternatives_are_not_simulator_inputs": True,
        "simulation_network_and_demand_byte_identical_to_003": True})
    for name in ("base", "closure", "closure_repeat"):
        directory = out / name; directory.mkdir()
        shutil.copyfile(REFERENCE / "base/edge_measures.add.xml", directory / "edge_measures.add.xml")
        config = ET.parse(REFERENCE / "base/controlled.sumocfg")
        output = config.getroot().find("output")
        for tag, value in (("vehroute-output", "vehroute.xml"), ("vehroute-output.exit-times", "true"),
                           ("vehroute-output.sorted", "true"), ("vehroute-output.write-unfinished", "true")):
            ET.SubElement(output, tag, value=value)
        if name != "base":
            config.getroot().find("input/additional-files").set("value", "edge_measures.add.xml,../closure.add.xml")
            ET.SubElement(ET.SubElement(config.getroot(), "routing"), "device.rerouting.mode", value="8")
        config.write(directory / "controlled.sumocfg", encoding="utf-8", xml_declaration=True)
        print("Simulating " + name, flush=True)
        observe_run(directory, tools["sumo"]["path"], env, spec, commands)
        indicators, _ = output_indicators(directory)
        write_json(directory / "temporal_indicators.json", indicators)
    print("Comparing executed routes and paired impacts", flush=True)
    metrics, routes, events, comparison, edges = analyze(out, requests, net, spec["closed_edge"], exposed)
    base_regression = {"trip_attributes_identical_after_removing_only_added_vehroute_device":
                      normalized_tripinfo(out / "base/tripinfo.xml") == normalized_tripinfo(REFERENCE / "base/tripinfo.xml"),
                      "edge_intervals_identical": canonical_edge_data(out / "base/edge_data.xml") == canonical_edge_data(REFERENCE / "base/edge_data.xml"),
                      "network_timeseries_identical_except_cpu": canonical_summary(out / "base/summary.xml") == canonical_summary(REFERENCE / "base/summary.xml")}
    write_json(out / "base_regression.json", base_regression); require(all(base_regression.values()), "Instrumented base differs from 003")
    repeat = {"metrics_identical": metrics["closure"] == metrics["closure_repeat"],
              "all_trip_attributes_identical": canonical_tripinfo(out / "closure/tripinfo.xml") == canonical_tripinfo(out / "closure_repeat/tripinfo.xml"),
              "edge_intervals_identical": canonical_edge_data(out / "closure/edge_data.xml") == canonical_edge_data(out / "closure_repeat/edge_data.xml"),
              "network_timeseries_identical_except_cpu": canonical_summary(out / "closure/summary.xml") == canonical_summary(out / "closure_repeat/summary.xml"),
              "executed_routes_and_exit_times_identical": routes["closure"] == routes["closure_repeat"],
              "rerouting_events_identical": events["closure"] == events["closure_repeat"],
              "permission_samples_identical": sha256(out / "closure/permission_monitor.csv") == sha256(out / "closure_repeat/permission_monitor.csv"),
              "configurations_identical": sha256(out / "closure/controlled.sumocfg") == sha256(out / "closure_repeat/controlled.sumocfg")}
    write_json(out / "reproducibility.json", repeat); require(all(repeat.values()), "Closure repeat differs")
    require(set(routes["base"]) == set(routes["closure"]) == set(requests), "Missing executed vehicle IDs; inspect retained results")
    require({e["id"] for e in events["closure"]} == exposed and len(events["closure"]) == 45, "Unexpected rerouting population")
    require(all(e["on_edge"] in spec["trigger_edges"] and e["time_s"] == float(requests[e["id"]]["depart"]) for e in events["closure"]), "Reroute occurred after origin")
    warnings = {n: warning_summary(out / n) for n in ("validation.errors.log", "base/sumo.errors.log", "closure/sumo.errors.log", "closure_repeat/sumo.errors.log")}
    write_json(out / "warnings.json", warnings)
    write_json(out / "summary.json", {"comparison_verified": True, "classification": "synthetic counterfactual, uncalibrated",
        "closed_edge": spec["closed_edge"], "base": metrics["base"], "closure": metrics["closure"],
        "system_comparison": comparison["system"], "reproducibility": repeat, "base_regression": base_regression,
        "executed_reroutes": 45, "closed_edge_executed_passages": 0})
    from .closure_plots import render
    render(out, net, spec, comparison, routes, edges)
    code = ["closure.py", "closure_analysis.py", "closure_plots.py", "controlled.py", "diagnostics.py", "pilot.py", "doctor.py"]
    artifacts = [p for p in out.rglob("*") if p.is_file() and ".mplconfig" not in p.parts and p != out / "manifest.json"]
    write_json(out / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "reference_manifest": str(REFERENCE / "manifest.json"), "reference_manifest_sha256": sha256(REFERENCE / "manifest.json"),
        "source_osm": frozen["source_osm"], "source_topology": frozen["source_topology"], "proj_database": frozen["proj_database"],
        "tools": tools, "traci_package": str(home / "tools/traci"), "experiment": spec, "demand": demand,
        "code_sha256": {n: sha256(ROOT / "src/digitaltwins" / n) for n in code},
        "scenario_sha256": {p.name: sha256(p) for p in SCENARIO.iterdir() if p.is_file()},
        "declared_differences_from_003": ["vehroute output and temporary read-only TraCI observation in both scenarios",
            "vehroute device token added to tripinfo", "closure only: one hard rerouter and routing mode 8; all other lane permissions retained"],
        "observational_inputs": [], "network_file_changed": False, "demand_file_changed": False,
        "artifacts": {str(p.relative_to(out)): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(artifacts)}})
    print(json.dumps({"output": str(out), "base_completed": metrics["base"]["completed"], "closure_completed": metrics["closure"]["completed"],
                      "duration_change_s": comparison["system"]["duration_s"]["delta_mean"], "reproducible": True}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
