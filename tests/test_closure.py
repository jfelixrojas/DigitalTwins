"""Pruebas focales contra omisiones de demanda, cierres ficticios y comparaciones sesgadas."""

from copy import deepcopy
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from digitaltwins.closure import ROOT, validate_routes
from digitaltwins.closure_analysis import executed_routes, group_comparison, normalized_tripinfo, paired_comparison, percent, quantile


class FixtureNetwork:
    def check_route(self, seq):
        allowed = {("s", "closed"), ("closed", "t"), ("s", "detour"), ("detour", "t")}
        if not seq or any(pair not in allowed for pair in zip(seq, seq[1:])):
            raise ValueError("Prohibited movement")


class ClosureChecks(unittest.TestCase):
    def setUp(self):
        work = ROOT / "outputs/intervention004/tests"; work.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=work); self.path = Path(self.temp.name)
        self.requests = {"W_E.0000": {"id": "W_E.0000", "stream": "W_E", "depart": "0", "from": "s", "to": "t"}}

    def tearDown(self):
        self.temp.cleanup()

    def vehicle(self, route="s detour t"):
        return ET.fromstring('<vehicle id="W_E.0000" depart="0"><route edges="' + route + '"/></vehicle>')

    def test_prevalidation_rejects_closed_edge(self):
        with self.assertRaisesRegex(ValueError, "closed"):
            validate_routes([self.vehicle("s closed t")], self.requests, FixtureNetwork(), "closed")

    def test_prevalidation_rejects_invalid_turn_even_with_correct_OD(self):
        with self.assertRaisesRegex(ValueError, "movement"):
            validate_routes([self.vehicle("s t")], self.requests, FixtureNetwork(), "closed")

    def test_missing_vehicle_or_changed_departure_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "count"):
            validate_routes([], self.requests, FixtureNetwork())
        v = self.vehicle(); v.set("depart", "1")
        with self.assertRaisesRegex(ValueError, "departure"):
            validate_routes([v], self.requests, FixtureNetwork())

    def test_destination_change_is_rejected(self):
        v = self.vehicle(); changed = deepcopy(self.requests); changed["W_E.0000"]["to"] = "detour"
        with self.assertRaisesRegex(ValueError, "OD"):
            validate_routes([v], changed, FixtureNetwork())

    def test_executed_route_separates_replaced_proposal(self):
        path = self.path / "vehroute.xml"
        path.write_text('<routes><vehicle id="W_E.0000" depart="0" arrival="20"><routeDistribution>'
            '<route replacedOnEdge="s" replacedAtTime="0" reason="closure" edges="s closed t"/>'
            '<route edges="s detour t" exitTimes="5 10 20"/></routeDistribution></vehicle></routes>')
        routes, events = executed_routes(path, self.requests, FixtureNetwork(), "closed")
        self.assertNotIn("closed", routes["W_E.0000"]["visited_edges"])
        self.assertIn("closed", events[0]["original_edges"])
        self.assertEqual(len(events), 1)

    def test_completed_route_requires_exit_times(self):
        path = self.path / "vehroute.xml"
        path.write_text('<routes><vehicle id="W_E.0000" depart="0" arrival="20"><route edges="s detour t" exitTimes="5 10"/></vehicle></routes>')
        with self.assertRaisesRegex(ValueError, "exit times"):
            executed_routes(path, self.requests, FixtureNetwork(), "closed")

    def test_pending_pair_is_retained_with_missing_impact(self):
        b = {"W_E.0000": {"arrival": "20", "duration": "20", "waitingTime": "3", "timeLoss": "5", "routeLength": "100", "departDelay": "0"}}
        c = {"W_E.0000": {"arrival": "-1"}}
        rows = paired_comparison(self.requests, b, c, {}, {}, {"W_E.0000"})
        self.assertEqual(len(rows), 1); self.assertIsNone(rows[0]["delta_duration_s"])
        group = group_comparison(rows)
        self.assertEqual(group["requested"], 1); self.assertEqual(group["paired_completed"], 0)
        self.assertIsNone(group["duration_s"]["delta_mean"])

    def test_longer_trip_with_lower_time_loss_is_not_an_improvement_in_duration(self):
        b = {"W_E.0000": {"arrival": "20", "duration": "20", "waitingTime": "3", "timeLoss": "5", "routeLength": "100", "departDelay": "0"}}
        c = deepcopy(b); c["W_E.0000"].update(arrival="25", duration="25", timeLoss="4", routeLength="120")
        rows = paired_comparison(self.requests, b, c, {}, {}, {"W_E.0000"})
        self.assertEqual(rows[0]["delta_duration_s"], 5); self.assertEqual(rows[0]["delta_duration_s_pct"], 25)
        self.assertEqual(rows[0]["delta_time_loss_s"], -1); self.assertEqual(rows[0]["delta_route_length_m"], 20)

    def test_percentiles_and_zero_denominator(self):
        self.assertAlmostEqual(quantile([0, 10, 20, 30], .95), 28.5)
        self.assertIsNone(percent(3, 0)); self.assertIsNone(quantile([], .5))

    def test_normalization_removes_only_added_device_token(self):
        path = self.path / "tripinfo.xml"
        path.write_text('<tripinfos><tripinfo id="v" duration="20" devices="vehroute_v tripinfo_v other"/></tripinfos>')
        row = normalized_tripinfo(path)["v"]
        self.assertEqual(row["devices"], "tripinfo_v other"); self.assertEqual(row["duration"], "20")


if __name__ == "__main__":
    unittest.main()
