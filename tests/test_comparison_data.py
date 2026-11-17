"""Metadatos individuales de ambos escenarios, sin ejecutar SUMO."""
import copy
import unittest
import xml.etree.ElementTree as ET
from digitaltwins.nicegui_app.data import vehicle_catalog


class ComparisonDataTests(unittest.TestCase):
    def fixture(self):
        trips = {s: ET.fromstring('<tripinfos><tripinfo id="W_E.0000" depart="0" arrival="10" duration="10" waitingTime="2" timeLoss="3" routeLength="100"/></tripinfos>') for s in ("base", "closure")}
        trips["closure"][0].set("arrival", "13"); trips["closure"][0].set("duration", "13")
        routes = {"base": {"W_E.0000": {"edges": ["a", "b"]}}, "closure": {"W_E.0000": {"edges": ["a", "c", "b"]}}}
        return trips, routes

    def test_individual_ids_lifetimes_and_executed_routes_are_preserved(self):
        trips, routes = self.fixture()
        actual = vehicle_catalog(trips, routes, ["W_E.0000"], {"a", "b", "c"})["vehicles"]["W_E.0000"]
        self.assertEqual(actual["base"]["depart_s"], 0)
        self.assertEqual(actual["base"]["arrival_s"], 10)
        self.assertEqual(actual["closure"]["arrival_s"], 13)
        self.assertEqual(actual["closure"]["route"], ["a", "c", "b"])
        self.assertEqual(actual["base"]["waiting_time_s"], 2)

    def test_duplicate_or_missing_ids_cannot_be_replaced_by_another_vehicle(self):
        for duplicate in (False, True):
            trips, routes = self.fixture()
            if duplicate:
                trips["closure"].append(copy.deepcopy(trips["closure"][0]))
            else:
                routes["closure"] = {"other": {"edges": ["a", "b"]}}
            with self.assertRaises(ValueError):
                vehicle_catalog(trips, routes, ["W_E.0000"], {"a", "b", "c"})

    def test_unknown_route_edges_are_rejected(self):
        trips, routes = self.fixture(); routes["closure"]["W_E.0000"]["edges"] = ["a", "invented", "b"]
        with self.assertRaises(ValueError):
            vehicle_catalog(trips, routes, ["W_E.0000"], {"a", "b", "c"})

    def test_nonfinite_or_unfinished_lifetimes_are_rejected(self):
        for arrival in ("-1", "nan", "0"):
            trips, routes = self.fixture(); trips["closure"][0].set("arrival", arrival)
            with self.assertRaises(ValueError):
                vehicle_catalog(trips, routes, ["W_E.0000"], {"a", "b", "c"})
