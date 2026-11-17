"""Integridad de la selección visual, sin simulaciones ni fuentes externas."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from digitaltwins.visualization.builder import (
    EDGES, ROOT, Sources, check_metrics, compact_signals, geometry,
    pack_edges, pack_fcd, safe_json,
)


class VisualizationTests(unittest.TestCase):
    def fcd(self):
        return ET.fromstring('<fcd><timestep time="0"><vehicle id="W_E.0" lane="e_0" x="4.91" y="516.43" speed="0"/></timestep><timestep time="1"><vehicle id="W_E.0" lane="e_0" x="6.52" y="517.82" speed="2.13"/></timestep><timestep time="2"/></fcd>')

    def test_native_fcd_positions_and_empty_steps_are_preserved(self):
        frames, count = pack_fcd(self.fcd(), ["W_E.0"], {"e_0": {}}, horizon=3)
        self.assertEqual(frames, [[[0, 4.91, 516.43, 0.0]], [[0, 6.52, 517.82, 2.13]], []])
        self.assertEqual(count, 2)

    def test_fcd_rejects_missing_times_duplicate_ids_and_unknown_lanes(self):
        missing = self.fcd(); missing.remove(missing[1])
        duplicate = self.fcd(); duplicate[0].append(copy.deepcopy(duplicate[0][0]))
        wrong_lane = self.fcd(); wrong_lane[0][0].set("lane", "absent")
        invalid = self.fcd(); invalid[1][0].set("x", "nan")
        for root in [missing, duplicate, wrong_lane, invalid]:
            with self.subTest(xml=ET.tostring(root)), self.assertRaises(ValueError):
                pack_fcd(root, ["W_E.0"], {"e_0": {}}, horizon=3)

    def network(self, index="1", via=":j_0_0"):
        return ET.fromstring(f'<net><location netOffset="0,0"/><edge id="a"><lane id="a_0" shape="0,0 10,0" length="10" speed="10"/></edge><edge id=":j_0" function="internal"><lane id=":j_0_0" shape="10,0 11,2" length="3" speed="5"/></edge><tlLogic id="j" programID="0" offset="0"><phase duration="2" state="Gr"/><phase duration="2" state="rG"/></tlLogic><connection from="a" to="a" tl="j" linkIndex="{index}" via="{via}"/></net>')

    def test_signal_uses_connection_index_and_native_via_geometry(self):
        geo = geometry(self.network(), {"edges": []})
        signal = geo["signals"][0]
        self.assertEqual((signal["tls"], signal["index"], signal["via"]), ("j", 1, ":j_0_0"))
        self.assertEqual(geo["programs"]["j"]["states"][0][signal["index"]], "r")
        self.assertEqual(next(l["shape"] for l in geo["lanes"] if l["id"] == signal["via"]), [[10, 0], [11, 2]])
        self.assertEqual([r["id"] for r in geo["roads"]], ["a"])

    def test_signal_rejects_negative_or_outside_index_and_missing_via(self):
        for root in [self.network(index="-1"), self.network(index="2"), self.network(via="missing")]:
            with self.assertRaises(ValueError):
                geometry(root, {"edges": []})

    def tls(self):
        return ET.fromstring('<tlsStates><tlsState time="0" id="j" programID="0" phase="0" state="Gr"/><tlsState time="1" id="j" programID="0" phase="0" state="Gr"/><tlsState time="2" id="j" programID="0" phase="1" state="rG"/><tlsState time="3" id="j" programID="0" phase="1" state="rG"/></tlsStates>')

    def test_native_signal_compression_is_lossless_at_every_second(self):
        programs = {"j": {"program": "0", "states": ["Gr", "rG"]}}
        root = self.tls(); compact = compact_signals(root, programs, horizon=4)
        self.assertEqual(compact, {"j": [[0, 0], [2, 1]]})
        for native in root:
            t = int(native.get("time"))
            phase = next(p for begin, p in reversed(compact["j"]) if begin <= t)
            self.assertEqual(programs["j"]["states"][phase], native.get("state"))

    def test_tls_rejects_missing_samples_wrong_vectors_phases_and_order(self):
        programs = {"j": {"program": "0", "states": ["Gr", "rG"]}}
        missing = self.tls(); missing.remove(missing[2])
        wrong = self.tls(); wrong[0].set("state", "GG")
        phase = self.tls(); phase[0].set("phase", "-1")
        order = self.tls(); order[0], order[1] = order[1], order[0]
        for root in [missing, wrong, phase, order]:
            with self.assertRaises(ValueError):
                compact_signals(root, programs, horizon=4)

    def edge_rows(self):
        return [{"edge": eid, "begin_s": t, "end_s": t + 60,
                 **{scenario + suffix: value for scenario in ["base", "closure"] for suffix, value in [
                     ("_entered_veh", 2), ("_flow_in_veh_h", 120), ("_occupancy_pct", 8.5), ("_mean_vehicles", .7)]}}
                for eid in EDGES for t in range(0, 1800, 60)]

    def test_flow_rate_occupancy_and_vehicle_presence_keep_different_units(self):
        rows = self.edge_rows()
        packed, _ = pack_edges(list(reversed(rows)), [])
        self.assertEqual(packed[EDGES[0]]["base"][0], [120, 8.5, .7])
        rows[0]["base_flow_in_veh_h"] = 2
        with self.assertRaises(ValueError):
            pack_edges(rows, [])

    def test_edge_coverage_cannot_hide_duplicate_interval(self):
        rows = self.edge_rows(); rows[0]["begin_s"] = 60; rows[0]["end_s"] = 120
        with self.assertRaises(ValueError):
            pack_edges(rows, [])

    def test_metric_totals_means_and_denominators_match_native_trips(self):
        trip = ET.fromstring('<tripinfos><tripinfo arrival="10" duration="10" waitingTime="2" timeLoss="5" routeLength="100"/></tripinfos>')
        metrics = {"completed": 1, **{key: {"total": value, "mean": value, "count": 1} for key, value in [
            ("duration_s", 10), ("waiting_time_s", 2), ("time_loss_s", 5), ("route_length_m", 100)]}}
        check_metrics(metrics, trip)
        metrics["time_loss_s"]["mean"] = 2
        with self.assertRaises(ValueError):
            check_metrics(metrics, trip)

    def test_inline_json_cannot_terminate_script_or_corrupt_labels(self):
        payload = {"label": "</script><script>alert('x') & español"}
        encoded = safe_json(payload)
        self.assertNotIn("</script>", encoded)
        self.assertEqual(json.loads(encoded), payload)
        with self.assertRaises(ValueError):
            safe_json({"number": float("nan")})

    def test_sources_reject_hash_change_and_paths_outside_root(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as folder:
            root = Path(folder); (root / "fixture.txt").write_text("native")
            sources = Sources(root); sources.expected["fixture.txt"] = "0" * 64
            with self.assertRaises(ValueError):
                sources.add("fixture.txt", "test")
            with self.assertRaises(ValueError):
                sources.add("../protection_before.json", "test")


if __name__ == "__main__":
    unittest.main()
