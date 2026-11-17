"""Validación temporal y análisis descriptivo de los pares sintéticos de la 005."""

from collections import Counter
import gzip
import json
import statistics
import xml.etree.ElementTree as ET

from .closure_analysis import (edge_comparison, executed_routes, group_comparison,
    paired_comparison, scenario_metrics, write_csv, distribution)
from .controlled import canonical_summary, output_indicators
from .pilot import require, warning_summary, write_json

FOCAL_IDS = ("N_E.0007", "N_E.0013")
FOCAL_TLS = "4011718406"
APPROACH = {"398538074", "1182057749", "1182057747"}


def xml(path):
    with (gzip.open(path, "rb") if str(path).endswith(".gz") else open(path, "rb")) as handle:
        return ET.parse(handle).getroot()


def phase_at(program, time_s, extra_offset_s):
    phases = program.findall("phase"); cycle = sum(float(p.get("duration")) for p in phases)
    local = (time_s - float(program.get("offset", "0")) - extra_offset_s) % cycle
    cumulative = 0.
    for i, phase in enumerate(phases):
        cumulative += float(phase.get("duration"))
        if local < cumulative:
            return i, phase.get("state")
    raise ValueError("Invalid phase durations")


def validate_signals(path, programs, offset_s, horizon=1800):
    rows = xml(path).findall("tlsState"); observed = {}
    for row in rows:
        tid, time_s = row.get("id"), float(row.get("time")); require(tid in programs, "Unknown signal ID")
        expected_phase, expected_state = phase_at(programs[tid], time_s, offset_s)
        require(row.get("programID") == programs[tid].get("programID"), "Signal program ID changed")
        require((int(row.get("phase")), row.get("state")) == (expected_phase, expected_state),
                f"Effective signal differs from declared offset: {tid}, time={time_s}, offset={offset_s}")
        key = (time_s, tid); require(key not in observed, "Duplicate TLS sample")
        observed[key] = dict(row.attrib)
    require(len(observed) == horizon * len(programs), "Incomplete signal timeline")
    require({t for t, _ in observed} == set(range(horizon)), "Missing signal timestamps")
    return observed


def analyze_pair(pair, requests, net, programs, offset_s, high_threshold_s=60):
    metrics, infos, routes, events, timelines = {}, {}, {}, {}, {}
    exposed = {vid for vid, request in requests.items() if request["stream"] == "W_E"}
    checks = {}; errors = {}
    for name in ("base", "closure"):
        directory = pair / name
        metrics[name], infos[name] = scenario_metrics(directory, requests)
        indicators, _ = output_indicators(directory); write_json(directory / "temporal_indicators.json", indicators)
        routes[name], events[name] = executed_routes(directory / "vehroute.xml", requests, net,
                                                    "1257993561#5" if name == "closure" else None)
        require(set(routes[name]) == set(requests), "An inserted ID is missing from vehroute output")
        write_json(directory / "executed_routes.json", routes[name]); write_json(directory / "rerouting_events.json", events[name])
        timelines[name] = validate_signals(directory / "tls_states.xml.gz", programs, offset_s)
        steps = canonical_summary(directory / "summary.xml")
        running_area = sum(int(s["running"]) for s in steps)
        if metrics[name]["completed"] == len(requests):
            require(running_area == metrics[name]["duration_s"]["total"], "Vehicle-time integral and trip durations differ")
        monitor = json.loads((directory / "closure_monitor.json").read_text())
        require(monitor["all_lane_permissions_match_expected_first_and_last"], "Unexpected permission changes")
        if name == "closure":
            require(not monitor["unique_vehicles_seen_on_target"] and not monitor["permission_violation_samples"], "Closure ineffective")
            for interval in xml(directory / "edge_data.xml").findall("interval"):
                e = next(e for e in interval.findall("edge") if e.get("id") == "1257993561#5")
                require(all(float(e.get(k, 0)) == 0 for k in ("sampledSeconds", "entered", "left")), "Native edge output contradicts closure")
        checks[name] = {"signal_samples_validated": len(timelines[name]), "vehicle_time_integral": running_area,
                        "completed": metrics[name]["completed"], "requested": len(requests), "permission_samples": monitor["samples"],
                        "all_departures_equal_schedule": all(float(infos[name][v]["depart"]) == float(requests[v]["depart"]) for v in infos[name])}
        errors[name] = warning_summary(directory / "sumo.errors.log")
    require(timelines["base"] == timelines["closure"], "Base/closure effective signals differ")
    require(len(events["closure"]) == 45 and {e["id"] for e in events["closure"]} == exposed, "Unexpected rerouting population")
    require(all(e["on_edge"] == "198404000" and e["time_s"] == float(requests[e["id"]]["depart"]) for e in events["closure"]), "Late rerouting")
    paired = paired_comparison(requests, infos["base"], infos["closure"], routes["base"], routes["closure"], exposed)
    write_csv(pair / "paired_vehicle_impacts.csv", paired)
    comparison = {"system": group_comparison(paired),
        "by_stream": {s: group_comparison([r for r in paired if r["stream"] == s]) for s in sorted({r["stream"] for r in paired})},
        "exposed_W_E": group_comparison([r for r in paired if r["originally_exposed"]]),
        "not_directly_exposed": group_comparison([r for r in paired if not r["originally_exposed"]])}
    write_json(pair / "comparison.json", comparison)
    edge_rows, edge_totals = edge_comparison(pair / "base/edge_data.xml", pair / "closure/edge_data.xml", routes["base"], routes["closure"])
    write_csv(pair / "edge_interval_comparison.csv", edge_rows); write_csv(pair / "edge_totals_comparison.csv", edge_totals)
    temporal_cases, trajectories, intersections = focal_cases(pair, requests, net, routes, timelines, paired, high_threshold_s)
    write_csv(pair / "NE_cases.csv", temporal_cases); write_csv(pair / "NE_trajectories.csv", trajectories)
    write_csv(pair / "NE_intersection_events.csv", intersections)
    write_json(pair / "warnings.json", errors)
    validation = {"signals_same_within_pair": True, "declared_offsets_effective": True, "runs": checks,
                  "closure_effective": True, "all_executed_routes_valid": True, "all_original_requests_preserved": True,
                  "complete_paired_population": comparison["system"]["paired_completed"], "reroutes_at_origin": 45}
    write_json(pair / "validation.json", validation)
    return comparison, metrics, temporal_cases


def focal_cases(pair, requests, net, routes, timelines, paired, threshold):
    lane_edges = {l.get("id"): e.get("id") for e in net.xml.findall("edge") for l in e.findall("lane")}
    trajectories = []; summaries = {}; intersection_rows = []
    for name in ("base", "closure"):
        local = {vid: [] for vid in FOCAL_IDS}
        for step in xml(pair / name / "fcd.xml.gz").findall("timestep"):
            time_s = float(step.get("time"))
            for v in step.findall("vehicle"):
                if v.get("id") not in FOCAL_IDS:
                    continue
                vid = v.get("id"); edge = lane_edges[v.get("lane")]
                sig = timelines[name][(time_s, FOCAL_TLS)]
                row = {"scenario": name, "id": vid, "time_s": time_s,
                       "elapsed_since_scheduled_depart_s": time_s - float(requests[vid]["depart"]),
                       "edge": edge, "lane": v.get("lane"), "pos_m": float(v.get("pos")), "speed_m_s": float(v.get("speed")),
                       "in_focal_approach": edge in APPROACH, "tls_id": FOCAL_TLS,
                       "tls_phase": int(sig["phase"]), "tls_link0_state": sig["state"][0]}
                trajectories.append(row); local[vid].append(row)
        for vid in FOCAL_IDS:
            approach = [r for r in local[vid] if r["in_focal_approach"]]
            require(approach, "Missing focal approach samples")
            route = routes[name][vid]; index = route["edges"].index("1182057747")
            exit_s = route["exit_times_s"][index]
            summaries[(name, vid)] = {"first_approach_sample_s": approach[0]["time_s"],
                "state_at_approach_sample": approach[0]["tls_link0_state"], "focal_incoming_exit_s": exit_s,
                "halt_samples_approach": sum(r["speed_m_s"] <= .1 for r in approach),
                "halt_while_focal_red_samples": sum(r["speed_m_s"] <= .1 and r["tls_link0_state"] == "r" for r in approach),
                "halt_while_focal_green_samples": sum(r["speed_m_s"] <= .1 and r["tls_link0_state"] in "Gg" for r in approach)}
            for i, (a, b) in enumerate(zip(route["edges"], route["edges"][1:])):
                connections = [c for c in net.connections if c["from"] == a and c["to"] == b and "tl" in c]
                if not connections:
                    continue
                tid = connections[0]["tl"]; link = int(connections[0]["linkIndex"]); exit_t = route["exit_times_s"][i]
                before = max(0, min(1799, int(exit_t) - 1)); at = min(1799, int(exit_t))
                samples = [r for r in local[vid] if r["edge"] == a]
                intersection_rows.append({"scenario": name, "id": vid, "incoming_edge": a, "next_edge": b,
                    "tls_id": tid, "representative_link_index": link, "incoming_exit_s": exit_t,
                    "first_observed_on_incoming_s": samples[0]["time_s"] if samples else None,
                    "state_one_second_before_exit": timelines[name][(before, tid)]["state"][link],
                    "state_at_exit_timestamp": timelines[name][(at, tid)]["state"][link],
                    "note": "Exit timestamp and native position samples have 1s resolution; representative connection if multiple lanes share movement."})
    rows = []
    for vid in FOCAL_IDS:
        impact = next(r for r in paired if r["id"] == vid)
        row = {"id": vid, "scheduled_depart_s": float(requests[vid]["depart"]), "delta_duration_s": impact["delta_duration_s"],
               "delta_waiting_time_s": impact["delta_waiting_time_s"], "delta_time_loss_s": impact["delta_time_loss_s"],
               "high_additional_delay": impact["delta_duration_s"] is not None and impact["delta_duration_s"] >= threshold,
               "high_threshold_s": threshold}
        for name in ("base", "closure"):
            row.update({name + "_" + k: v for k, v in summaries[(name, vid)].items()})
        rows.append(row)
    return rows, trajectories, intersection_rows


def descriptive(values):
    return {**distribution(values), "population_sd": statistics.pstdev(values) if values else None,
            "range": max(values) - min(values) if values else None}


def summarize(rows, focal_rows):
    eligible = [r for r in rows if r["paired_completed"] == 150]
    values = [r["delta_total_duration_s"] for r in eligible]
    result = {"evaluated_pairs": len(rows), "complete_population_pairs": len(eligible),
              "higher_total_travel_time": sum(v > 0 for v in values), "lower_total_travel_time": sum(v < 0 for v in values),
              "unchanged_total_travel_time": sum(v == 0 for v in values),
              "total_duration_change_s": descriptive(values),
              "total_duration_change_pct": descriptive([r["delta_total_duration_pct"] for r in eligible]),
              "W_E_positive_median_pairs": sum(r["W_E_median_delta_duration_s"] > 0 for r in eligible),
              "W_E_median_change_s": descriptive([r["W_E_median_delta_duration_s"] for r in eligible]),
              "by_offset": {}, "by_schedule": {}, "focal_cases": {}}
    for field, dest in (("offset_s", "by_offset"), ("schedule", "by_schedule")):
        for key in sorted({r[field] for r in eligible}):
            chosen = [r for r in eligible if r[field] == key]
            result[dest][str(key)] = {"delta_total_duration_s": descriptive([r["delta_total_duration_s"] for r in chosen]),
                "positive": sum(r["delta_total_duration_s"] > 0 for r in chosen),
                "W_E_median_positive": sum(r["W_E_median_delta_duration_s"] > 0 for r in chosen)}
    for vid in FOCAL_IDS:
        chosen = [r for r in focal_rows if r["id"] == vid]
        result["focal_cases"][vid] = {"high_delay_pairs": sum(r["high_additional_delay"] for r in chosen),
             "delta_duration_s": descriptive([r["delta_duration_s"] for r in chosen]),
             "high_by_offset": {str(off): sum(r["high_additional_delay"] for r in chosen if r["offset_s"] == off) for off in (0, 30, 60)}}
    return result
