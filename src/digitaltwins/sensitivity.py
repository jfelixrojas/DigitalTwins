"""Cinco calendarios por tres desfases virtuales, reutilizando el cierre de la 004."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

from .closure import observe_run, validate_routes
from .closure_analysis import write_csv
from .controlled import canonical_tripinfo, canonical_edge_data, canonical_summary
from .diagnostics import Network
from .doctor import sha256
from .pilot import require, write_json
from .sensitivity_analysis import analyze_pair, summarize, xml, FOCAL_IDS

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "outputs/closure_experiment_verified"
SPEC = ROOT / "scenarios/closure_sensitivity/experiment.json"


def perturb_schedule(original, stream_order, seed, bound=15, end=900):
    if seed is None:
        return deepcopy(original), []
    rng = random.Random(seed); rows = []; audit = []
    for stream in stream_order:
        group = sorted((r for r in original if r["stream"] == stream), key=lambda r: float(r["depart"]))
        previous = -1
        for request in group:
            departure = int(request["depart"])
            require(float(request["depart"]) == departure, "Original schedule must have integer departures")
            low, high = max(0, departure - bound, previous + 1), min(end - 1, departure + bound)
            require(low <= high, "Cannot preserve departure order within bounds")
            new = rng.randint(low, high); row = {**request, "depart": str(new)}
            rows.append(row); audit.append({"id": row["id"], "original_s": departure, "new_s": new,
                "displacement_s": new - departure, "feasible_low_s": low, "feasible_high_s": high})
            previous = new
    require(len(rows) == len(original) and {r["id"] for r in rows} == {r["id"] for r in original}, "Temporal perturbation lost IDs")
    return sorted(rows, key=lambda r: (int(r["depart"]), r["id"])), audit


def offset_definitions(programs, extra):
    root = ET.Element("additional")
    for tid, p in sorted(programs.items()):
        cycle = sum(float(x.get("duration")) for x in p.findall("phase"))
        require(p.get("type") == "static" and cycle == 90, "Offsets require the original static 90-second cycles")
        offset = (float(p.get("offset", "0")) + extra) % cycle
        ET.SubElement(root, "tlLogic", id=tid, programID=p.get("programID"), offset=str(int(offset)))
    return root


def build_config(directory, common, schedule, offset_path, closure):
    source = REFERENCE / ("closure" if closure else "base")
    config = ET.parse(source / "controlled.sumocfg"); inp = config.getroot().find("input")
    relative = lambda path: os.path.relpath(path, directory)
    inp.find("net-file").set("value", relative(common / "controlled.net.xml"))
    inp.find("route-files").set("value", relative(schedule / "controlled.rou.xml"))
    additional = ["edge_measures.add.xml", "observations.add.xml", relative(offset_path)]
    if closure:
        additional.append(relative(common / "closure.add.xml"))
    inp.find("additional-files").set("value", ",".join(additional))
    ET.SubElement(config.getroot().find("output"), "fcd-output", value="fcd.xml.gz")
    config.write(directory / "controlled.sumocfg", encoding="utf-8", xml_declaration=True)
    shutil.copyfile(source / "edge_measures.add.xml", directory / "edge_measures.add.xml")
    additional = ET.Element("additional")
    ET.SubElement(additional, "timedEvent", type="SaveTLSStates", dest="tls_states.xml.gz")
    ET.ElementTree(additional).write(directory / "observations.add.xml", encoding="utf-8", xml_declaration=True)


def run_pair(pair, schedule, common, offset_path, off, spec, env, tool, net, programs):
    pair.mkdir(parents=True); commands = []
    requests = {r["id"]: r for r in json.loads((schedule / "arrival_schedule.json").read_text())}
    validate_routes(ET.parse(schedule / "controlled.rou.xml").getroot().findall("vehicle"), requests, net)
    for name in ("base", "closure"):
        directory = pair / name; directory.mkdir()
        build_config(directory, common, schedule, offset_path, name == "closure")
        observe_run(directory, tool, env, spec, commands)
    return analyze_pair(pair, requests, net, programs, off)


def comparison_row(sid, seed, off, comparison, metrics):
    system = comparison["system"]; direct = comparison["exposed_W_E"]; indirect = comparison["not_directly_exposed"]
    return {"combination": f"{sid}_offset{off:03d}", "schedule": sid, "schedule_seed": seed, "offset_s": off,
            "simulation_seed": 42, "paired_completed": system["paired_completed"],
            "base_inserted": metrics["base"]["inserted"], "closure_inserted": metrics["closure"]["inserted"],
            "base_completed": metrics["base"]["completed"], "closure_completed": metrics["closure"]["completed"],
            "base_pending": metrics["base"]["pending"], "closure_pending": metrics["closure"]["pending"],
            "base_total_duration_s": metrics["base"]["duration_s"]["total"], "closure_total_duration_s": metrics["closure"]["duration_s"]["total"],
            "delta_total_duration_s": system["duration_s"]["closure_total"] - system["duration_s"]["base_total"],
            "delta_total_duration_pct": system["duration_s"]["delta_of_mean_pct"], "delta_mean_duration_s": system["duration_s"]["delta_mean"],
            "median_individual_duration_change_s": system["duration_s"]["paired_deltas"]["median"],
            "p05_individual_duration_change_s": system["duration_s"]["paired_deltas"]["p05"],
            "p95_individual_duration_change_s": system["duration_s"]["paired_deltas"]["p95"],
            "delta_mean_waiting_time_s": system["waiting_time_s"]["delta_mean"],
            "delta_mean_time_loss_s": system["time_loss_s"]["delta_mean"], "delta_mean_route_length_m": system["route_length_m"]["delta_mean"],
            "base_max_running_veh": metrics["base"]["max_running_veh"], "closure_max_running_veh": metrics["closure"]["max_running_veh"],
            "W_E_mean_delta_duration_s": direct["duration_s"]["delta_mean"], "W_E_median_delta_duration_s": direct["duration_s"]["paired_deltas"]["median"],
            "W_E_total_delta_duration_s": direct["duration_s"]["closure_total"] - direct["duration_s"]["base_total"],
            "indirect_total_delta_duration_s": indirect["duration_s"]["closure_total"] - indirect["duration_s"]["base_total"],
            "N_E_mean_delta_duration_s": comparison["by_stream"]["N_E"]["duration_s"]["delta_mean"],
            "base_teleports": int(metrics["base"]["teleports"]["total"]), "closure_teleports": int(metrics["closure"]["teleports"]["total"]),
            "base_collisions": int(metrics["base"]["safety"]["collisions"]), "closure_collisions": int(metrics["closure"]["safety"]["collisions"])}


def without_fcd_token(path):
    rows = canonical_tripinfo(path)
    for vid, row in rows.items():
        row["devices"] = " ".join(v for v in row.get("devices", "").split() if v != "fcd_" + vid)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output", default="outputs/closure_sensitivity")
    args = parser.parse_args(argv); out = (ROOT / args.output).resolve()
    require(out.parent == ROOT / "outputs" and (not out.exists() or {p.name for p in out.iterdir()} <= {"audit"}),
            "Select an unused output directory; previous experiments are never overwritten")
    out.mkdir(exist_ok=True); (out / "common").mkdir(); (out / "schedules").mkdir(); (out / "combinations").mkdir()
    experiment = json.loads(SPEC.read_text()); frozen = json.loads((REFERENCE / "manifest.json").read_text())
    require(experiment["simulation_seed"] == 42 and experiment["schedule_seeds"] == [None, 101, 102, 103, 104]
            and experiment["global_extra_offsets_s"] == [0, 30, 60], "Experimental matrix differs")
    for name, item in frozen["artifacts"].items():
        require(sha256(REFERENCE / name) == item["sha256"], "Canonical 004 artifact changed: " + name)
    for name, digest in frozen["code_sha256"].items():
        require(sha256(ROOT / "src/digitaltwins" / name) == digest, "Canonical implementation changed: " + name)
    home = Path(os.environ.get("SUMO_HOME", "/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/share/sumo"))
    env = {**os.environ, "SUMO_HOME": str(home), "PROJ_DATA": str(Path(frozen["proj_database"]["path"]).parent),
           "PROJ_NETWORK": "OFF", "PYTHONDONTWRITEBYTECODE": "1"}
    require(sha256(Path(env["PROJ_DATA"]) / "proj.db") == frozen["proj_database"]["sha256"], "PROJ database changed")
    tool = str(home.parent.parent / "bin/sumo")
    require(sha256(Path(tool)) == frozen["tools"]["sumo"]["sha256"], "SUMO binary changed")
    version = subprocess.run([tool, "--version"], env=env, capture_output=True, text=True, check=True).stdout
    require(version.splitlines()[0] == "Eclipse SUMO sumo 1.28.0", "SUMO version differs")
    common = out / "common"
    for name in ("controlled.net.xml", "closure.add.xml", "validated_alternatives.rou.xml", "ATTRIBUTION.txt"):
        shutil.copyfile(REFERENCE / name, common / name)
    net = Network(common / "controlled.net.xml", ROOT / "outputs/pilot_verified/pilot.osm.xml")
    programs = {p.get("id"): p for p in net.xml.findall("tlLogic")}; require(len(programs) == 18, "Signal population differs")
    original = json.loads((REFERENCE / "arrival_schedule.json").read_text()); require(len(original) == 150, "Original demand count differs")
    stream_order = [s["id"] for s in frozen["demand"]["streams"]]
    schedules = []; schedule_manifest = {}; rows = []; focal_rows = []; stream_rows = []
    for off in experiment["global_extra_offsets_s"]:
        root = offset_definitions(programs, off)
        ET.ElementTree(root).write(common / f"offset{off:03d}.add.xml", encoding="utf-8", xml_declaration=True)
    # La combinación original se ejecuta y verifica antes de generar perturbaciones.
    for seed in experiment["schedule_seeds"]:
        sid = "original" if seed is None else f"jitter{seed}"; folder = out / "schedules" / sid; folder.mkdir()
        schedule, perturbations = perturb_schedule(original, stream_order, seed, experiment["jitter_bound_s"])
        requests = {r["id"]: r for r in schedule}
        if seed is None:
            shutil.copyfile(REFERENCE / "arrival_schedule.json", folder / "arrival_schedule.json")
            shutil.copyfile(REFERENCE / "controlled.rou.xml", folder / "controlled.rou.xml")
        else:
            tree = ET.parse(REFERENCE / "controlled.rou.xml"); vehicles = tree.getroot().findall("vehicle")
            for v in vehicles:
                v.set("depart", requests[v.get("id")]["depart"]); tree.getroot().remove(v)
            for v in sorted(vehicles, key=lambda v: (float(v.get("depart")), v.get("id"))):
                tree.getroot().append(v)
            tree.write(folder / "controlled.rou.xml", encoding="utf-8", xml_declaration=True)
            write_json(folder / "arrival_schedule.json", schedule)
        write_json(folder / "perturbations.json", perturbations)
        validate_routes(ET.parse(folder / "controlled.rou.xml").getroot().findall("vehicle"), requests, net)
        # Las alternativas estrictamente validadas en la 004 se conservan por ID;
        # cambiar horarios no altera la validez topológica de sus secuencias.
        alternatives = ET.parse(REFERENCE / "validated_alternatives.rou.xml")
        for v in alternatives.getroot().findall("vehicle"):
            v.set("depart", requests[v.get("id")]["depart"])
        validate_routes(alternatives.getroot().findall("vehicle"), requests, net, "1257993561#5")
        schedule_manifest[sid] = {"seed": seed, "count": 150, "schedule_sha256": sha256(folder / "arrival_schedule.json"),
            "route_file_sha256": sha256(folder / "controlled.rou.xml"), "min_depart_s": min(float(r["depart"]) for r in schedule),
            "max_depart_s": max(float(r["depart"]) for r in schedule), "changed_departures": sum(r["displacement_s"] != 0 for r in perturbations)}
        schedules.append(sid)
        for off in experiment["global_extra_offsets_s"]:
            cid = f"{sid}_offset{off:03d}"; print(f"Running {cid} ({len(rows)+1}/15)", flush=True)
            pair = out / "combinations" / cid
            comparison, metrics, focal = run_pair(pair, folder, common, common / f"offset{off:03d}.add.xml", off,
                                                   frozen["experiment"], env, tool, net, programs)
            row = comparison_row(sid, seed, off, comparison, metrics); rows.append(row)
            for case in focal:
                focal_rows.append({"combination": cid, "schedule": sid, "offset_s": off, **case})
            for stream, data in comparison["by_stream"].items():
                stream_rows.append({"combination": cid, "schedule": sid, "offset_s": off, "stream": stream,
                    "paired_completed": data["paired_completed"], "base_mean_duration_s": data["duration_s"]["base_mean"],
                    "closure_mean_duration_s": data["duration_s"]["closure_mean"], "mean_delta_duration_s": data["duration_s"]["delta_mean"],
                    "median_delta_duration_s": data["duration_s"]["paired_deltas"]["median"],
                    "p05_delta_duration_s": data["duration_s"]["paired_deltas"]["p05"], "p95_delta_duration_s": data["duration_s"]["paired_deltas"]["p95"]})
            if seed is None and off == 0:
                require(row["delta_total_duration_s"] == 405, "Original +405s result not reproduced")
                # FCD no debe cambiar la dinámica ni los atributos de la 004.
                regression = {"delta_total_duration_s": row["delta_total_duration_s"]}
                for name in ("base", "closure"):
                    regression[name + "_trip_attributes_identical_except_possible_fcd_device_token"] = without_fcd_token(pair / name / "tripinfo.xml") == without_fcd_token(REFERENCE / name / "tripinfo.xml")
                    regression[name + "_edge_intervals_identical"] = canonical_edge_data(pair / name / "edge_data.xml") == canonical_edge_data(REFERENCE / name / "edge_data.xml")
                    regression[name + "_network_series_identical_except_cpu"] = canonical_summary(pair / name / "summary.xml") == canonical_summary(REFERENCE / name / "summary.xml")
                write_json(out / "original_regression.json", regression)
                require(all(v is True for k, v in regression.items() if k != "delta_total_duration_s"), "Native instrumentation altered original simulation")
            write_csv(out / "matrix_comparison.csv", rows)
            print(f"Verified {cid}: delta_total={row['delta_total_duration_s']:+.0f}s, completed={row['base_completed']}/{row['closure_completed']}", flush=True)
    require(len({m["schedule_sha256"] for m in schedule_manifest.values()}) == 5, "Schedules are not genuinely distinct")
    write_json(out / "schedules_manifest.json", schedule_manifest)
    write_csv(out / "NE_cases.csv", focal_rows); write_csv(out / "movement_comparison.csv", stream_rows)
    summary = summarize(rows, focal_rows); write_json(out / "summary.json", summary)
    cid = experiment["repeat_combination"]; original_pair = out / "combinations" / cid
    print("Repeating " + cid, flush=True)
    run_pair(out / "repetition" / cid, out / "schedules/jitter101", common, common / "offset030.add.xml", 30,
             frozen["experiment"], env, tool, net, programs)
    repeat_checks = {}
    for name in ("base", "closure"):
        old = original_pair / name; new = out / "repetition" / cid / name
        repeat_checks[name] = {"tripinfo": canonical_tripinfo(old / "tripinfo.xml") == canonical_tripinfo(new / "tripinfo.xml"),
            "edge_intervals": canonical_edge_data(old / "edge_data.xml") == canonical_edge_data(new / "edge_data.xml"),
            "network_series_except_cpu": canonical_summary(old / "summary.xml") == canonical_summary(new / "summary.xml"),
            "TLS_states": [dict(x.attrib) for x in xml(old / "tls_states.xml.gz")] == [dict(x.attrib) for x in xml(new / "tls_states.xml.gz")],
            "FCD_trajectories": ET.tostring(xml(old / "fcd.xml.gz")) == ET.tostring(xml(new / "fcd.xml.gz")),
            "permissions": sha256(old / "permission_monitor.csv") == sha256(new / "permission_monitor.csv")}
    require(all(all(c.values()) for c in repeat_checks.values()), "New combination is not reproducible")
    write_json(out / "reproducibility.json", {"combination": cid, "checks": repeat_checks})
    from .sensitivity_plots import render
    render(out, rows, stream_rows, focal_rows)
    code_names = ["sensitivity.py", "sensitivity_analysis.py", "sensitivity_plots.py"]
    artifacts = [p for p in out.rglob("*") if p.is_file() and not p.is_relative_to(out / "audit") and ".mplconfig" not in p.parts]
    write_json(out / "manifest.json", {"created_at_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
        "SUMO": frozen["tools"]["sumo"], "version_output": version, "reference_manifest_sha256": sha256(REFERENCE / "manifest.json"),
        "experiment": experiment, "experiment_spec_sha256": sha256(SPEC), "schedules": schedule_manifest,
        "offset_files_sha256": {str(o): sha256(common / f"offset{o:03d}.add.xml") for o in (0, 30, 60)},
        "source_osm": frozen["source_osm"], "source_topology": frozen["source_topology"], "proj_database": frozen["proj_database"],
        "code_sha256": {n: sha256(ROOT / "src/digitaltwins" / n) for n in code_names}, "unchanged_004_code_sha256": frozen["code_sha256"],
        "matrix_runs": 30, "repeat_runs": 2, "observational_inputs": [],
        "artifacts": {str(p.relative_to(out)): {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in sorted(artifacts)}})
    print(json.dumps({"output": str(out), "pairs": 15, "increases": summary["higher_total_travel_time"],
        "reductions": summary["lower_total_travel_time"], "range_s": summary["total_duration_change_s"], "reproducible": True}), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr); raise SystemExit(1)
