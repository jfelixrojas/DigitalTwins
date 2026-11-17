"""Garantías críticas: giros por nodo y balance de vehículos, con datos sintéticos."""

import json
from pathlib import Path
import tempfile
import unittest

from digitaltwins.pilot import ROOT, audit_network, collect_metrics, request_diagnostics
import xml.etree.ElementTree as ET


class PilotChecks(unittest.TestCase):
    def setUp(self):
        parent = ROOT / "outputs/intervention002"
        parent.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-test-", dir=parent)
        self.directory = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def network(self, connection=True, via="2"):
        path = self.directory / "net.xml"
        path.write_text('<net><edge id="10" from="1" to="2"><lane index="0"/></edge>'
                        '<edge id="20" from="2" to="3"><lane index="0"/></edge>'
                        '<junction id="2" type="priority"/>' +
                        ('<connection from="10" to="20" fromLane="0" toLane="0" dir="l"/>' if connection else '') + '</net>')
        osm = {"restrictions": [{"id": "900", "tags": {"restriction": "no_left_turn"}, "missing_members": [],
            "members": [{"role": "from", "type": "way", "ref": "10"},
                        {"role": "to", "type": "way", "ref": "20"},
                        {"role": "via", "type": "node", "ref": via}]}]}
        return audit_network(path, osm)[0]

    def test_forbidden_turn_is_detected(self):
        self.assertEqual(self.network()["restriction_violations"], 1)

    def test_absent_forbidden_turn_is_respected(self):
        self.assertEqual(self.network(False)["restriction_checks"][0]["status"], "respected")

    def test_unmapped_via_is_not_falsely_certified(self):
        self.assertEqual(self.network(via="999")["restriction_checks"][0]["status"], "manual_check_unmapped_via_node")

    def metrics_fixture(self, inserted=1, arrival="10", loaded=1):
        (self.directory / "statistics.xml").write_text(
            f'<statistics><vehicles loaded="{loaded}" inserted="{inserted}" running="0" waiting="0"/>'
            '<teleports total="0"/><safety collisions="0"/><vehicleTripStatistics duration="10"/></statistics>')
        (self.directory / "tripinfo.xml").write_text(f'<tripinfos><tripinfo id="0" arrival="{arrival}" duration="10"/></tripinfos>')
        (self.directory / "summary.xml").write_text('<summary><step time="1800" running="0" waiting="0" duration="123"/></summary>')

    def test_completed_vehicle_and_balances(self):
        self.metrics_fixture()
        result = collect_metrics(self.directory, 2, 1)
        self.assertEqual((result["completed_vehicles"], result["rejected_trips"]), (1, 1))
        self.assertNotIn("duration", result["final_summary"])

    def test_successful_process_cannot_hide_bad_balance(self):
        self.metrics_fixture(inserted=2, loaded=2)
        with self.assertRaisesRegex(ValueError, "balance"):
            collect_metrics(self.directory, 2, 2)

    def test_zero_completions_is_failure(self):
        self.metrics_fixture(inserted=0, arrival="-1")
        with self.assertRaises(ValueError):
            collect_metrics(self.directory, 1, 1)

    def test_rejections_distinguish_direction_and_components(self):
        graph = {"a": {"b"}, "b": set(), "c": set()}
        requests = {"0": ET.fromstring('<trip from="b" to="a"/>'),
                    "1": ET.fromstring('<trip from="a" to="c"/>')}
        self.assertEqual(request_diagnostics(graph, requests, {})["rejection_reason_counts"],
                         {"no_directed_path": 1, "different_weak_components": 1})


if __name__ == "__main__":
    unittest.main()
