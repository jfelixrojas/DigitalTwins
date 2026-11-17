"""Comparación emparejada de estados SUMO sintéticos; cantidades y tasas separadas."""

from collections import Counter
import csv
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET

from .pilot import require, write_json

FIELDS = {"duration_s": "duration", "waiting_time_s": "waitingTime", "time_loss_s": "timeLoss",
          "route_length_m": "routeLength", "depart_delay_s": "departDelay"}


def write_csv(path, rows):
    require(bool(rows), "Cannot write an empty indicator table")
    with Path(path).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def percent(delta, base):
    return 100 * delta / base if base else None


def quantile(values, probability):
    """Percentil por interpolación lineal entre rangos (método 7)."""
    if not values:
        return None
    values = sorted(values); index = (len(values) - 1) * probability
    low = int(index); high = min(low + 1, len(values) - 1)
    return values[low] + (index - low) * (values[high] - values[low])


def distribution(values):
    return {"count": len(values), "mean": statistics.mean(values) if values else None,
            "median": quantile(values, .5), "p05": quantile(values, .05), "p25": quantile(values, .25),
            "p75": quantile(values, .75), "p95": quantile(values, .95),
            "min": min(values) if values else None, "max": max(values) if values else None}


def normalized_tripinfo(path):
    """Retirar solo el token de instrumentación vehroute añadido en la 004."""
    result = {}
    for trip in ET.parse(path).getroot().findall("tripinfo"):
        row = dict(trip.attrib); vid = row["id"]
        row["devices"] = " ".join(d for d in row.get("devices", "").split() if d != "vehroute_" + vid)
        result[vid] = row
    return result


def executed_routes(path, requests, net, closed_edge=None):
    """Separar propuestas reemplazadas del recorrido final con tiempos de salida."""
    result, events = {}, []
    for vehicle in ET.parse(path).getroot().findall("vehicle"):
        vid = vehicle.get("id"); require(vid in requests and vid not in result, "Unexpected/duplicate executed ID")
        routes = vehicle.findall("route") + vehicle.findall("routeDistribution/route")
        final = [r for r in routes if r.get("replacedOnEdge") is None]
        require(len(final) == 1, "Missing/ambiguous final executed route: " + vid)
        route = final[0]; edges = route.get("edges").split(); net.check_route(edges)
        require(edges[0] == requests[vid]["from"] and edges[-1] == requests[vid]["to"], "Executed OD changed")
        if closed_edge is not None:
            require(closed_edge not in edges, "Final closure route includes prohibited edge")
        exit_times = [float(v) for v in route.get("exitTimes", "").split()]
        require(len(exit_times) == len(edges), "Missing executed edge exit times")
        completed = float(vehicle.get("arrival", "-1")) >= 0
        if completed:
            require(all(t >= 0 for t in exit_times), "Completed route has an unvisited edge")
        visited = [e for e, t in zip(edges, exit_times) if t >= 0]
        result[vid] = {"edges": edges, "visited_edges": visited, "exit_times_s": exit_times,
                       "depart_s": float(vehicle.get("depart")), "arrival_s": float(vehicle.get("arrival", "-1")),
                       "completed": completed}
        for old in routes:
            if old.get("replacedOnEdge") is not None:
                old_edges = old.get("edges").split(); net.check_route(old_edges)
                events.append({"id": vid, "time_s": float(old.get("replacedAtTime")),
                               "on_edge": old.get("replacedOnEdge"), "reason": old.get("reason"),
                               "original_edges": old_edges, "final_edges": edges})
    return result, events


def scenario_metrics(directory, requests):
    root = ET.parse(directory / "statistics.xml").getroot()
    trips = {t.get("id"): dict(t.attrib) for t in ET.parse(directory / "tripinfo.xml").getroot().findall("tripinfo")}
    require(set(trips) <= set(requests), "Unknown tripinfo ID")
    completed = {vid: t for vid, t in trips.items() if float(t["arrival"]) >= 0 and not t.get("vaporized")}
    removed = [vid for vid, t in trips.items() if float(t["arrival"]) >= 0 and t.get("vaporized")]
    v = root.find("vehicles"); inserted, running, waiting = (int(v.get(k)) for k in ("inserted", "running", "waiting"))
    require(inserted == len(completed) + running + len(removed), "Inserted/completed balance failed")
    require(int(v.get("loaded")) == inserted + waiting, "Loaded/inserted balance failed")
    metrics = {"requested": len(requests), "loaded": int(v.get("loaded")), "inserted": inserted,
               "completed": len(completed), "rejected": len(requests) - int(v.get("loaded")),
               "running_at_end": running, "waiting_to_depart": waiting, "pending": running + waiting,
               "removed": len(removed), "missing_tripinfo_ids": sorted(set(requests) - set(trips)),
               "teleports": dict(root.find("teleports").attrib), "safety": dict(root.find("safety").attrib)}
    for field, attribute in FIELDS.items():
        values = [float(t[attribute]) for t in completed.values()]
        metrics[field] = {"total": sum(values), **distribution(values)}
    steps = ET.parse(directory / "summary.xml").getroot().findall("step")
    metrics.update(max_running_veh=max(int(s.get("running")) for s in steps),
                   max_halting_veh=max(int(s.get("halting")) for s in steps),
                   last_arrival_s=max((float(t["arrival"]) for t in completed.values()), default=None))
    write_json(directory / "system_metrics.json", metrics)
    return metrics, trips


def paired_comparison(requests, base, closure, base_routes, closure_routes, exposed):
    rows = []
    for vid, request in sorted(requests.items()):
        b, c = base.get(vid), closure.get(vid)
        bdone = bool(b and float(b["arrival"]) >= 0 and not b.get("vaporized"))
        cdone = bool(c and float(c["arrival"]) >= 0 and not c.get("vaporized"))
        row = {"id": vid, "stream": request["stream"], "originally_exposed": vid in exposed,
               "scheduled_depart_s": float(request["depart"]), "base_completed": bdone, "closure_completed": cdone,
               "executed_route_changed": base_routes.get(vid, {}).get("edges") != closure_routes.get(vid, {}).get("edges")}
        for field, attribute in FIELDS.items():
            bv = float(b[attribute]) if bdone else None; cv = float(c[attribute]) if cdone else None
            delta = cv - bv if bv is not None and cv is not None else None
            row.update({"base_" + field: bv, "closure_" + field: cv, "delta_" + field: delta,
                        "delta_" + field + "_pct": percent(delta, bv) if delta is not None else None})
        rows.append(row)
    return rows


def group_comparison(rows):
    paired = [r for r in rows if r["base_completed"] and r["closure_completed"]]
    result = {"requested": len(rows), "paired_completed": len(paired),
              "base_completed": sum(r["base_completed"] for r in rows), "closure_completed": sum(r["closure_completed"] for r in rows),
              "routes_changed": sum(r["executed_route_changed"] for r in rows)}
    for field in FIELDS:
        b = [r["base_" + field] for r in paired]; c = [r["closure_" + field] for r in paired]
        bm = statistics.mean(b) if b else None; cm = statistics.mean(c) if c else None
        delta = cm - bm if bm is not None else None
        result[field] = {"base_mean": bm, "closure_mean": cm, "delta_mean": delta,
                         "delta_of_mean_pct": percent(delta, bm) if delta is not None else None,
                         "base_total": sum(b), "closure_total": sum(c),
                         "paired_deltas": distribution([r["delta_" + field] for r in paired]),
                         "mean_individual_percent_change": statistics.mean(vals) if
                         (vals := [r["delta_" + field + "_pct"] for r in paired if r["delta_" + field + "_pct"] is not None]) else None}
    result["travel_time_impact_counts"] = {"increased": sum(r["delta_duration_s"] > 0 for r in paired),
                                            "decreased": sum(r["delta_duration_s"] < 0 for r in paired),
                                            "unchanged": sum(r["delta_duration_s"] == 0 for r in paired)}
    return result


def edge_comparison(base_path, closure_path, base_routes, closure_routes):
    def read_edges(path):
        return {(float(i.get("begin")), float(i.get("end")), e.get("id")): dict(e.attrib)
                for i in ET.parse(path).getroot().findall("interval") for e in i.findall("edge")}
    bdata, cdata = read_edges(base_path), read_edges(closure_path)
    require(bdata.keys() == cdata.keys(), "Edge interval scopes differ")
    rows, totals = [], {}
    for (begin, end, eid), b in sorted(bdata.items()):
        c = cdata[(begin, end, eid)]; period = end - begin
        row = {"begin_s": begin, "end_s": end, "edge": eid}
        for name, data in (("base", b), ("closure", c)):
            row.update({name + "_entered_veh": int(data["entered"]), name + "_left_veh": int(data["left"]),
                        name + "_flow_in_veh_h": 3600 * int(data["entered"]) / period,
                        name + "_mean_vehicles": float(data.get("sampledSeconds", 0)) / period,
                        name + "_occupancy_pct": float(data.get("occupancy", 0)),
                        name + "_waiting_time_vehicle_s": float(data.get("waitingTime", 0))})
        for field in ("entered_veh", "left_veh", "flow_in_veh_h", "mean_vehicles", "occupancy_pct", "waiting_time_vehicle_s"):
            row["delta_" + field] = row["closure_" + field] - row["base_" + field]
        rows.append(row)
        aggregate = totals.setdefault(eid, {"edge": eid, "base_entered_veh": 0, "closure_entered_veh": 0,
            "base_sampled_vehicle_s": 0., "closure_sampled_vehicle_s": 0., "base_max_occupancy_pct": 0., "closure_max_occupancy_pct": 0.})
        for name, data in (("base", b), ("closure", c)):
            aggregate[name + "_entered_veh"] += int(data["entered"])
            aggregate[name + "_sampled_vehicle_s"] += float(data.get("sampledSeconds", 0))
            aggregate[name + "_max_occupancy_pct"] = max(aggregate[name + "_max_occupancy_pct"], float(data.get("occupancy", 0)))
    busage = Counter(e for r in base_routes.values() for e in r["visited_edges"])
    cusage = Counter(e for r in closure_routes.values() for e in r["visited_edges"])
    for eid, row in totals.items():
        row.update(delta_entered_veh=row["closure_entered_veh"] - row["base_entered_veh"],
                   base_executed_route_uses=busage[eid], closure_executed_route_uses=cusage[eid],
                   delta_executed_route_uses=cusage[eid] - busage[eid])
    return rows, list(totals.values())


def analyze(out, requests, net, closed_edge, exposed):
    metrics, infos, routes, events = {}, {}, {}, {}
    for name in ("base", "closure", "closure_repeat"):
        metrics[name], infos[name] = scenario_metrics(out / name, requests)
        routes[name], events[name] = executed_routes(out / name / "vehroute.xml", requests, net, closed_edge if name != "base" else None)
        write_json(out / name / "executed_routes.json", routes[name])
        write_json(out / name / "rerouting_events.json", events[name])
    rows = paired_comparison(requests, infos["base"], infos["closure"], routes["base"], routes["closure"], exposed)
    write_csv(out / "paired_vehicle_impacts.csv", rows)
    comparison = {"population": "All original requests retained; travel statistics use explicitly counted pairs completed in both scenarios.",
                  "difference": "closure minus base; percentages of group means and mean individual percentages are distinct.",
                  "percentiles": "linear interpolation, method 7; descriptive deterministic impacts, not confidence intervals",
                  "system": group_comparison(rows),
                  "by_stream": {sid: group_comparison([r for r in rows if r["stream"] == sid]) for sid in sorted({r["stream"] for r in rows})},
                  "exposed_W_E": group_comparison([r for r in rows if r["originally_exposed"]]),
                  "not_directly_exposed": group_comparison([r for r in rows if not r["originally_exposed"]])}
    write_json(out / "comparison.json", comparison)
    edge_rows, edge_totals = edge_comparison(out / "base/edge_data.xml", out / "closure/edge_data.xml", routes["base"], routes["closure"])
    write_csv(out / "edge_interval_comparison.csv", edge_rows); write_csv(out / "edge_totals_comparison.csv", edge_totals)
    return metrics, routes, events, comparison, edge_totals
