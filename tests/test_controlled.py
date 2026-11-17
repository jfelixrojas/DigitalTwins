"""Unidades de demanda, direcciones, permisos y agregación de estados sintéticos."""

import json
from pathlib import Path
import tempfile
import unittest

from digitaltwins.controlled import ROOT, generate_departures, output_indicators
from digitaltwins.diagnostics import Network, components, reachable, shortest_path


class ControlledChecks(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT/"scenarios/pilot_controlled/demand.json").read_text())
        work = ROOT/"outputs/intervention003"
        work.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="tests-", dir=work)
        self.path = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_rates_generate_150_explicit_departures(self):
        rows = generate_departures(self.spec)
        self.assertEqual(len(rows), 150)
        self.assertEqual(len({r["id"] for r in rows}), 150)
        self.assertEqual(sum(r["stream"] == "W_E" for r in rows),45)
        self.assertEqual(sum(r["stream"] == "N_W" for r in rows),15)

    def test_rate_units_and_exclusive_interval_end(self):
        values=[float(r["depart"]) for r in generate_departures(self.spec) if r["stream"]=="W_E"]
        self.assertEqual(values[:3],[0,20,40]);self.assertEqual(values[-1],880)
        self.assertTrue(all(float(r["depart"]) < 900 for r in generate_departures(self.spec)))

    def test_generation_deterministic_and_invalid_rate_rejected(self):
        self.assertEqual(generate_departures(self.spec),generate_departures(self.spec))
        self.spec["streams"][0]["rate_veh_h"] = 0
        with self.assertRaises(ValueError):generate_departures(self.spec)

    def test_weak_components_do_not_imply_directed_paths(self):
        graph={"a":{"b"},"b":{"c"},"c":{"b"},"x":set()}
        self.assertEqual([len(c) for c in components(graph)],[3,1])
        self.assertEqual([len(c) for c in components(graph,True)],[2,1,1])
        self.assertNotIn("a",reachable(graph,"c"))

    def test_alternative_query_preserves_graph(self):
        graph={"s":{"a","b"},"a":{"t"},"b":{"t"},"t":set()}; costs={e:1 for e in graph}
        saved={e:set(v) for e,v in graph.items()}
        self.assertEqual(shortest_path(graph,costs,"s","t","a")["edges"],["s","b","t"])
        self.assertIsNone(shortest_path(graph,costs,"s","t","s")); self.assertEqual(graph,saved)

    def test_passenger_permissions_include_connection_and_internal_lane(self):
        self.path.joinpath("osm.xml").write_text('<osm><way id="10"/><way id="20"/><way id="30"/></osm>')
        lane=lambda id: f'<lane id="{id}_0" index="0" speed="10" length="10" shape="0,0 10,0"/>'
        self.path.joinpath("net.xml").write_text('<net>'+''.join(f'<edge id="{id}" from="1" to="2">{lane(id)}</edge>' for id in (10,20,30))+
            '<edge id=":via" function="internal"><lane id=":via_0" disallow="passenger"/></edge>'+
            '<connection from="10" to="20" fromLane="0" toLane="0" via=":via_0"/>'+
            '<connection from="10" to="30" fromLane="0" toLane="0" disallow="passenger"/></net>')
        self.assertEqual(Network(self.path/"net.xml",self.path/"osm.xml").graph["10"],set())

    def indicators_fixture(self, inserted="2"):
        self.path.joinpath("edge_data.xml").write_text('<meandata><interval begin="0" end="60" id="x"><edge id="a" sampledSeconds="120" entered="3" left="2" occupancy="9"/></interval></meandata>')
        self.path.joinpath("summary.xml").write_text(f'<summary><step time="0" inserted="{inserted}" running="1" ended="1" halting="0"/></summary>')

    def test_aggregation_units_and_missing_speed(self):
        self.indicators_fixture();_,rows=output_indicators(self.path)
        self.assertEqual(rows[0]["mean_vehicles"],2)
        self.assertEqual(rows[0]["flow_in_veh_h"],180)
        self.assertIsNone(rows[0]["speed_m_s"])

    def test_temporal_vehicle_balance_counterexample(self):
        self.indicators_fixture("3")
        with self.assertRaisesRegex(ValueError,"conservation"):output_indicators(self.path)


if __name__ == "__main__":unittest.main()
