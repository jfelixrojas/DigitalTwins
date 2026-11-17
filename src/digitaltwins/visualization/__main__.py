import argparse
import sys
from .builder import build

parser = argparse.ArgumentParser(description="Generar visor y fichas desde evidencias existentes, sin ejecutar SUMO.")
parser.add_argument("--output", default="outputs/visualization")
args = parser.parse_args()
try:
    build(args.output)
except (ValueError, OSError) as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(1)
