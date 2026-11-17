"""Georreferenciación y conservación del visor previo; sin iniciar un servidor."""
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

from digitaltwins.doctor import sha256
from digitaltwins.nicegui_app.data import ROOT, SumoProjection, load_original
from digitaltwins.visualization.builder import Sources, safe_json

LOCATION = {"projParameter": "+proj=utm +zone=16 +ellps=WGS84 +datum=WGS84 +units=m +no_defs",
            "netOffset": "-260204.62,-1515196.25"}
POINTS = [
    ("11490960275", -89.20827, 13.7049317, 968.61, 988.16),
    ("4022414503", -89.2084362, 13.703769, 949.45, 859.65),
    ("1545263045", -89.2091522, 13.7032359, 871.44, 801.36),
]


def anchors():
    net, osm = ET.Element("net"), ET.Element("osm")
    for vid, lon, lat, x, y in POINTS:
        ET.SubElement(net, "junction", id=vid, x=str(x), y=str(y))
        ET.SubElement(osm, "node", id=vid, lon=str(lon), lat=str(lat))
    return net, osm


class NiceGuiDataTests(unittest.TestCase):
    def test_original_osm_anchors_preserve_latitude_longitude_order(self):
        projection = SumoProjection(LOCATION)
        for _, lon, lat, x, y in POINTS:
            result = projection.to_leaflet(x, y)
            self.assertAlmostEqual(result[0], lat, delta=2e-7)
            self.assertAlmostEqual(result[1], lon, delta=2e-7)
        matched = projection.validate_anchors(*anchors())
        self.assertEqual(len(matched), 3)
        self.assertLess(max(p["error_m"] for p in matched), .03)

    def test_offset_sign_error_is_rejected_against_independent_osm_nodes(self):
        projection = SumoProjection({**LOCATION, "netOffset": "260204.62,1515196.25"})
        with self.assertRaisesRegex(ValueError, "original OSM anchor"):
            projection.validate_anchors(*anchors())

    def test_projection_roundtrip_covers_network_bounds(self):
        projection = SumoProjection(LOCATION)
        for xy in [(0., 0.), (1350.62, 1098.75), (0., 1098.75), (1350.62, 0.), (675.31, 549.375)]:
            ll = projection.to_leaflet(*xy)
            result = projection.from_leaflet(*ll)
            self.assertAlmostEqual(result[0], xy[0], delta=.0001)
            self.assertAlmostEqual(result[1], xy[1], delta=.0001)

    def test_missing_projection_or_nonfinite_coordinate_stops_georeferencing(self):
        for spec in ["!", "-", ".", ""]:
            with self.assertRaises(ValueError):
                SumoProjection({**LOCATION, "projParameter": spec})
        with self.assertRaises(ValueError):
            SumoProjection(LOCATION).to_leaflet(float("nan"), 0)

    def test_insufficient_anchors_cannot_be_replaced_by_approximations(self):
        net, osm = anchors(); net.remove(net[0])
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            SumoProjection(LOCATION).validate_anchors(net, osm)

    def fixture(self, root, schema="digitaltwins-viewer-1"):
        folder = root / "outputs/visualization"; folder.mkdir(parents=True)
        index = folder / "index.html"
        index.write_text('<script id="viewer-data" type="application/json">' + safe_json({"schema": schema, "cases": {}}) + "</script>")
        (folder / "manifest.json").write_text(json.dumps({"outputs": {"index.html": {"sha256": sha256(index)}}}))
        return index

    def test_previous_viewer_is_read_without_rewriting_its_bytes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as temp:
            root = Path(temp); index = self.fixture(root); before = index.read_bytes()
            parsed = load_original(Sources(root))
            self.assertEqual(parsed["schema"], "digitaltwins-viewer-1")
            self.assertEqual(index.read_bytes(), before)

    def test_changed_previous_viewer_is_rejected_before_export(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as temp:
            root = Path(temp); index = self.fixture(root); index.write_text(index.read_text() + "altered")
            with self.assertRaisesRegex(ValueError, "Viewer006 artifact changed"):
                load_original(Sources(root))

    def test_unsupported_previous_viewer_schema_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "outputs") as temp:
            root = Path(temp); self.fixture(root, schema="unknown")
            with self.assertRaisesRegex(ValueError, "Unsupported viewer006 schema"):
                load_original(Sources(root))


if __name__ == "__main__":
    unittest.main()
