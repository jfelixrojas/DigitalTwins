"""Diagnóstico de movimientos passenger y datos OSM locales, siempre en lectura."""

from collections import Counter, defaultdict
import csv
import heapq
import json
from pathlib import Path
import re
import sqlite3
import xml.etree.ElementTree as ET

from .pilot import passenger_allowed, require, tags, write_json


def reachable(graph, start, excluded=None):
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node in seen or node == excluded:
            continue
        seen.add(node)
        stack.extend(graph.get(node, set()) - seen)
    return seen


def components(graph, strong=False):
    reverse = {v: set() for v in graph}
    for a, values in graph.items():
        for b in values:
            reverse[b].add(a)
    if not strong:
        both = {v: graph[v] | reverse[v] for v in graph}
        unseen, result = set(graph), []
        while unseen:
            group = reachable(both, min(unseen))
            unseen -= group; result.append(group)
    else:
        # Solo 350 enlaces: intersección de alcanzabilidades, sin librerías adicionales.
        unseen, result = set(graph), []
        while unseen:
            start = min(unseen)
            group = reachable(graph, start) & reachable(reverse, start)
            unseen -= group; result.append(group)
    return sorted(result, key=lambda g: (-len(g), min(g)))


def shortest_path(graph, costs, start, end, excluded=None):
    if start not in graph or end not in graph or start == excluded or end == excluded:
        return None
    queue = [(costs[start], start, (start,))]; seen = set()
    while queue:
        cost, node, path = heapq.heappop(queue)
        if node in seen or node == excluded:
            continue
        if node == end:
            return {"edges": list(path), "free_flow_edge_time_s": cost}
        seen.add(node)
        for nxt in sorted(graph[node]):
            if nxt not in seen and nxt != excluded:
                heapq.heappush(queue, (cost + costs[nxt], nxt, path + (nxt,)))
    return None


class Network:
    def __init__(self, net_path, osm_path):
        self.xml = ET.parse(net_path).getroot()
        osm = ET.parse(osm_path).getroot()
        self.ways = {w.get("id"): w for w in osm.findall("way")}
        self.osm_nodes = {n.get("id"): n for n in osm.findall("node")}
        self.edges = {e.get("id"): e for e in self.xml.findall("edge") if e.get("function") != "internal"}
        self.junctions = {j.get("id"): j for j in self.xml.findall("junction") if j.get("type") != "internal"}
        all_lanes = {l.get("id"): l for l in self.xml.iter("lane")}
        lanes = {eid: {l.get("index") for l in e.findall("lane") if passenger_allowed(l)} for eid, e in self.edges.items()}
        self.graph = {eid: set() for eid in self.edges if lanes[eid]}
        self.connections = []
        for c in self.xml.findall("connection"):
            a, b = c.get("from"), c.get("to")
            if a not in self.graph or b not in self.graph or c.get("fromLane") not in lanes[a] or c.get("toLane") not in lanes[b]:
                continue
            if not passenger_allowed(c) or (c.get("via") in all_lanes and not passenger_allowed(all_lanes[c.get("via")])):
                continue
            self.graph[a].add(b); self.connections.append(dict(c.attrib))
        self.costs = {e: min(float(l.get("length")) / float(l.get("speed")) for l in self.edges[e].findall("lane") if passenger_allowed(l)) for e in self.graph}
        self.shapes = {e: [tuple(map(float, v.split(","))) for v in edge.find("lane").get("shape").split()] for e, edge in self.edges.items()}
        self.weak = components(self.graph)
        self.strong = components(self.graph, strong=True)
        self.component_index = {e: i for i, group in enumerate(self.weak) for e in group}

    def way_id(self, edge):
        return re.match(r"^-?(\d+)", edge)[1]

    def way_tags(self, edge):
        return tags(self.ways[self.way_id(edge)])

    def check_route(self, sequence):
        require(sequence and all(e in self.graph for e in sequence), "Route has an unknown or prohibited edge")
        require(all(b in self.graph[a] for a, b in zip(sequence, sequence[1:])), "Route has a prohibited movement")


def connectivity_report(net, national_index, bbox, out):
    """Comparar incidencias nodales con el índice nacional, sin crear conexiones."""
    db = sqlite3.connect(Path(national_index).as_uri() + "?mode=ro&immutable=1", uri=True)
    db.execute("PRAGMA query_only=ON"); db.execute("PRAGMA trusted_schema=OFF")
    reports = []
    try:
        for i, group in enumerate(net.weak):
            wids = sorted({net.way_id(e) for e in group})
            node_ids = sorted({n.get("ref") for w in wids for n in net.ways[w].findall("nd")})
            points = [(float(net.osm_nodes[n].get("lon")), float(net.osm_nodes[n].get("lat"))) for n in node_ids]
            missing = []
            if i:
                for node in node_ids:
                    rows = db.execute("SELECT DISTINCT w.id,w.tags_json,n.lon,n.lat FROM memberships m JOIN ways w ON w.id=m.way_id JOIN nodes n ON n.id=m.node_id WHERE m.node_id=?", (int(node),))
                    for wid, text, lon, lat in rows:
                        if str(wid) in net.ways:
                            continue
                        coords = list(db.execute("SELECT n.lon,n.lat FROM memberships m JOIN nodes n ON n.id=m.node_id WHERE m.way_id=? ORDER BY m.ordinal", (wid,)))
                        inside = any(bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3] for x, y in coords)
                        missing.append({"node": node, "coordinates_crs84": [lon, lat], "outside_way": wid,
                                        "way_tags": json.loads(text), "any_way_node_inside_bbox": inside})
            reports.append({"component": i, "edge_count": len(group), "edges": sorted(group),
                "osm_ways": [{"id": w, "tags": tags(net.ways[w])} for w in wids],
                "bounds_crs84": [min(x for x,y in points), min(y for x,y in points), max(x for x,y in points), max(y for x,y in points)],
                "omitted_national_way_incidences": missing,
                "access_restrictions_observed": [{"id": w, "tags": {k:v for k,v in tags(net.ways[w]).items() if k in ("access", "vehicle", "motor_vehicle", "motorcar", "bridge", "layer", "tunnel")}} for w in wids if any(k in tags(net.ways[w]) for k in ("access", "vehicle", "motor_vehicle", "motorcar", "bridge", "layer", "tunnel"))]})
    finally:
        db.close()
    edge_ids = sorted(net.graph); counts = {}
    with (out / "passenger_reachability.csv").open("w", newline="") as handle:
        writer = csv.writer(handle); writer.writerow(["origin_edge/destination_edge", *edge_ids])
        for start in edge_ids:
            found = reachable(net.graph, start); counts[start] = len(found)
            writer.writerow([start, *[int(end in found) for end in edge_ids]])
    result = {"weak_components": reports, "strong_component_edge_counts": [len(g) for g in net.strong],
              "graph_scope": "Passenger lane permissions, connection permissions and via-lane permissions; topological reachability, not observed real-world access.",
              "reachable_ordered_edge_pairs_including_diagonal": sum(counts.values()),
              "possible_ordered_edge_pairs_including_diagonal": len(edge_ids)**2,
              "reachable_destination_count_by_origin": counts,
              "lane_change_constraints_present": sum(any(k in l.attrib for k in ("changeLeft", "changeRight")) for l in net.xml.iter("lane")),
              "network_modified": False, "bbox_modified": False}
    write_json(out / "connectivity.json", result)
    return result


def attribute_report(net, old_routes, controlled_routes, out):
    uses = Counter(e for seq in old_routes for e in seq)
    controlled = Counter(e for seq in controlled_routes for e in seq)
    rows = []
    for eid, edge in sorted(net.edges.items()):
        default = sorted({word for p in edge.iter("param") if p.get("key") == "osmDefaults" for word in p.get("value").split()})
        t = net.way_tags(eid)
        rows.append({"edge": eid, "osm_way": net.way_id(eid), "name": t.get("name", ""),
            "highway": t.get("highway"), "default_fields": default,
            "lanes_sumo": len(edge.findall("lane")), "speed_m_s": float(edge.find("lane").get("speed")),
            "source_lanes": t.get("lanes"), "source_maxspeed": t.get("maxspeed"),
            "source_oneway": t.get("oneway"), "old_route_uses": uses[eid], "controlled_route_uses": controlled[eid],
            "roosevelt": "Roosevelt" in t.get("name", ""),
            "priority": "high" if default and (uses[eid] or controlled[eid] or "Roosevelt" in t.get("name", "")) else "review" if default else "source_attribute_available"})
    write_json(out / "edge_attribute_audit.json", {"edges": rows,
        "default_lane_edges": sum("numLanes" in r["default_fields"] for r in rows),
        "default_speed_edges": sum("speed" in r["default_fields"] for r in rows),
        "default_edges_on_old_routes": sum(bool(r["default_fields"]) and r["old_route_uses"] > 0 for r in rows),
        "default_edges_on_controlled_routes": sum(bool(r["default_fields"]) and r["controlled_route_uses"] > 0 for r in rows),
        "high_priority_default_edges": [r["edge"] for r in rows if r["priority"] == "high"]})
    with (out / "edge_attribute_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return rows


def candidate_report(net, candidates, streams, routes, out):
    """Solo consultas de rutas alternativas. No modifica la red ni ejecuta cierres."""
    result = []
    for candidate in candidates:
        require(candidate in net.graph, "Unknown candidate edge")
        alternatives = []
        for stream in streams:
            base = routes[stream["id"]]
            alternative = shortest_path(net.graph, net.costs, stream["from"], stream["to"], candidate)
            require(alternative is not None, "Candidate disconnects a controlled OD")
            net.check_route(alternative["edges"])
            alternatives.append({"stream": stream["id"], "baseline_uses_candidate": candidate in base,
                                 "baseline_route": base, "alternative_route_without_candidate": alternative})
        result.append({"edge": candidate, "osm_tags": net.way_tags(candidate),
                       "length_m": float(net.edges[candidate].find("lane").get("length")),
                       "all_controlled_ODs_have_alternative": True, "ODs": alternatives,
                       "scope": "Static graph query only; no edge disabled, no closure simulation, no congestion or detour travel time prediction."})
    write_json(out / "closure_candidates.json", result)
    return result


def warning_review(net, reference, out):
    inherited = json.loads((reference / "warnings.json").read_text())["netconvert.errors.log"]
    rows = []
    for message in inherited["messages"]:
        if "total messages" in message:
            category = "aggregation_summary"
        elif any(s in message for s in ("pt stop", "PT line", "free-floating", "compound 'bus'", "waterway.river")):
            category = "mode_filter_or_incomplete_public_transport"
        elif "traffic light" in message or "Could not build program" in message:
            category = "signal_without_retained_movements"
        elif "Minor green" in message:
            category = "lane_and_turn_capacity_requires_review"
        else:
            category = "converter_geometry_requires_review"
        rows.append({"message": message, "classification": category,
                     "confirmed_physical_error": False,
                     "referenced_edges_in_network": [e for e in re.findall(r"edge '([^']+)'", message) if e in net.edges],
                     "referenced_junctions": [j for j in re.findall(r"junction '([^']+)'", message) if j in net.junctions]})
    programs = []
    for logic in net.xml.findall("tlLogic"):
        phases = [dict(p.attrib) for p in logic.findall("phase")]
        programs.append({**logic.attrib, "cycle_s": sum(float(p["duration"]) for p in phases),
                         "phases": phases, "classification": "SUMO-generated virtual program, not real controller records",
                         "movements": [c for c in net.connections if c.get("tl") == logic.get("id")]})
    source_signals = sorted(n for n,element in net.osm_nodes.items() if tags(element).get("highway") == "traffic_signals")
    built = {p["id"] for p in programs}
    write_json(out / "signals.json", {"source_traffic_signal_nodes": source_signals,
        "source_nodes_without_generated_program": sorted(set(source_signals) - built), "programs": programs})
    write_json(out / "inherited_warning_review.json", {"source": str(reference/"netconvert.errors.log"),
        "network_corrections_applied": [], "warnings_hidden": False, "review": rows,
        "external_edges_shorter_than_1m": [eid for eid,e in net.edges.items() if float(e.find("lane").get("length")) < 1],
        "assessment": "No observed geometric truth is available to prove physical errors. Preserve grade separation, source directions and geometry; review shape offsets, short edges, turn radii and inferred lane capacity before calibration."})
