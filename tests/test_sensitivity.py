"""Comprobar perturbaciones reales, conservación temporal y desfases efectivos."""

from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from digitaltwins.controlled import generate_departures
from digitaltwins.sensitivity import ROOT, perturb_schedule, offset_definitions
from digitaltwins.sensitivity_analysis import phase_at, validate_signals, summarize


class SensitivityChecks(unittest.TestCase):
    def setUp(self):
        spec = json.loads((ROOT / "scenarios/pilot_controlled/demand.json").read_text())
        self.original = generate_departures(spec); self.streams = [s["id"] for s in spec["streams"]]
        self.program = ET.fromstring('<tlLogic id="s" programID="0" type="static" offset="7"><phase duration="30" state="Gr"/><phase duration="60" state="rG"/></tlLogic>')

    def test_original_schedule_is_exact_and_not_mutated(self):
        rows, audit = perturb_schedule(self.original, self.streams, None)
        self.assertEqual(rows, self.original); self.assertEqual(audit, [])
        rows[0]["depart"] = "10"; self.assertEqual(self.original[0]["depart"], "0")

    def test_four_schedules_are_distinct_bounded_and_ordered(self):
        hashes = {json.dumps(self.original, sort_keys=True)}; originals = {r["id"]: r for r in self.original}
        for seed in (101, 102, 103, 104):
            rows, _ = perturb_schedule(self.original, self.streams, seed)
            hashes.add(json.dumps(rows, sort_keys=True))
            for r in rows:
                t = int(r["depart"]); self.assertTrue(0 <= t < 900)
                self.assertLessEqual(abs(t - int(originals[r["id"]]["depart"])), 15)
            for stream in self.streams:
                group = sorted((r for r in rows if r["stream"] == stream), key=lambda r: r["id"])
                times = [int(r["depart"]) for r in group]
                self.assertTrue(all(a < b for a, b in zip(times, times[1:])))
        self.assertEqual(len(hashes), 5)

    def test_seed_determinism(self):
        self.assertEqual(perturb_schedule(self.original, self.streams, 101), perturb_schedule(self.original, self.streams, 101))

    def test_temporal_change_preserves_IDs_ODs_and_stream_counts(self):
        rows, audit = perturb_schedule(self.original, self.streams, 104)
        self.assertEqual(len(rows), 150); self.assertEqual(len(audit), 150)
        original = {r["id"]: {k: v for k, v in r.items() if k != "depart"} for r in self.original}
        self.assertEqual({r["id"]: {k: v for k, v in r.items() if k != "depart"} for r in rows}, original)
        self.assertEqual(Counter(r["stream"] for r in rows), Counter(r["stream"] for r in self.original))

    def test_offsets_preserve_program_IDs_phases_and_relative_coordination(self):
        second = deepcopy(self.program); second.set("id", "t"); second.set("offset", "22")
        programs = {"s": self.program, "t": second}; original = ET.tostring(self.program)
        root = offset_definitions(programs, 60); definitions = {x.get("id"): x for x in root}
        self.assertEqual(definitions["s"].get("offset"), "67"); self.assertEqual(definitions["t"].get("offset"), "82")
        self.assertEqual(definitions["s"].get("programID"), "0"); self.assertEqual(len(definitions["s"]), 0)
        self.assertEqual(ET.tostring(self.program), original)
        self.assertEqual(phase_at(self.program, 7, 0), (0, "Gr"))
        self.assertEqual(phase_at(self.program, 7, 30), (1, "rG"))

    def test_non_90_second_program_is_rejected(self):
        self.program.find("phase").set("duration", "31")
        with self.assertRaisesRegex(ValueError, "90-second"):
            offset_definitions({"s": self.program}, 30)

    def test_silently_ignored_offset_is_detected_from_effective_states(self):
        work = ROOT / "outputs/closure_sensitivity/audit/tests"; work.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as tmp:
            path = Path(tmp) / "states.xml"; root = ET.Element("tlsStates")
            for t in range(90):
                phase, state = phase_at(self.program, t, 30)
                ET.SubElement(root, "tlsState", time=str(t), id="s", programID="0", phase=str(phase), state=state)
            ET.ElementTree(root).write(path)
            self.assertEqual(len(validate_signals(path, {"s": self.program}, 30, horizon=90)), 90)
            with self.assertRaisesRegex(ValueError, "declared offset"):
                validate_signals(path, {"s": self.program}, 0, horizon=90)

    def test_descriptive_sign_changes_preserve_zero_and_denominators(self):
        rows = [{"schedule": "original", "offset_s": off, "paired_completed": 150,
                 "delta_total_duration_s": delta, "delta_total_duration_pct": delta / 100,
                 "W_E_median_delta_duration_s": median} for off, delta, median in ((0, 405, 15), (30, -100, -1), (60, 0, 0))]
        summary = summarize(rows, [])
        self.assertEqual(summary["higher_total_travel_time"], 1); self.assertEqual(summary["lower_total_travel_time"], 1)
        self.assertEqual(summary["unchanged_total_travel_time"], 1); self.assertEqual(summary["W_E_positive_median_pairs"], 1)
        self.assertEqual(summary["total_duration_change_s"]["range"], 505)


if __name__ == "__main__":
    unittest.main()
