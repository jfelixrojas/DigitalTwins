"""Diagnóstico local de solo lectura; no importa ni instala paquetes externos."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import sys


COMMANDS = (
    "sumo", "sumo-gui", "netconvert", "netedit", "duarouter", "osmium",
    "ogrinfo", "gdalinfo", "proj", "git", "brew", "uv",
)
PACKAGES = (
    "osmnx", "geopandas", "pyrosm", "osmium", "sumolib", "traci",
    "libsumo", "eclipse-sumo", "shapely", "pyproj", "fiona", "pyogrio",
    "gdal", "networkx", "pandas", "numpy", "pyarrow", "duckdb", "pytest",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(root: Path, verify_source: bool = False) -> dict:
    """Consultar el intérprete actual y las fuentes referenciadas desde DC_X."""
    commands = {name: shutil.which(name) for name in COMMANDS}
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            packages[name] = None

    manifest = json.loads((root / "data/osm/sources.json").read_text(encoding="utf-8"))
    sources = []
    for source in manifest["sources"]:
        path = root.parent / source["path_from_dc_x"]
        row = {"id": source["id"], "path": str(path), "exists": path.is_file()}
        if row["exists"]:
            try:
                row["size_matches"] = path.stat().st_size == source["size_bytes"]
                if verify_source:
                    row["sha256_matches"] = sha256(path) == source["sha256"]
            except OSError as exc:
                row["error"] = str(exc)
        sources.append(row)

    source_checks_passed = all(
        row["exists"] and row.get("size_matches", False)
        and (not verify_source or row.get("sha256_matches", False))
        for row in sources
    )
    sumo_home = os.environ.get("SUMO_HOME")
    random_trips = Path(sumo_home) / "tools/randomTrips.py" if sumo_home else None
    conversion_available = bool(commands["netconvert"] and commands["osmium"])
    simulation_available = bool(commands["sumo"] and commands["duarouter"])
    return {
        "python": {"executable": sys.executable, "version": platform.python_version(),
                   "supported": sys.version_info >= (3, 11)},
        "platform": platform.platform(),
        "commands": commands,
        "packages": packages,
        "SUMO_HOME": sumo_home,
        "randomTrips_available": bool(random_trips and random_trips.is_file()),
        "sources": sources,
        "source_sha256_checked": verify_source,
        "source_checks_passed": source_checks_passed,
        "conversion_tools_available": conversion_available,
        "simulation_tools_available": simulation_available,
        "pilot_recipe_prerequisites_met": bool(
            sys.version_info >= (3, 11) and source_checks_passed and verify_source
            and conversion_available and simulation_available
            and random_trips and random_trips.is_file()
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-source", action="store_true", help="Verificar SHA-256 de las fuentes")
    parser.add_argument("--require-sumo", action="store_true", help="Fallar si faltan requisitos de la receta piloto")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    try:
        report = inspect(root, args.verify_source)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["python"]["supported"] or not report["source_checks_passed"]:
        return 1
    if args.require_sumo and not report["pilot_recipe_prerequisites_met"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
