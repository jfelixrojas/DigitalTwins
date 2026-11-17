#!/bin/sh
set -eu
dt_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$dt_root"
if [ ! -x .venv-nicegui/bin/python ]; then
    printf '%s\n' 'Falta .venv-nicegui. Consulta docs/nicegui_prototype_report.md para preparar el entorno.' >&2
    exit 1
fi
export PYTHONPATH="$dt_root/src" PYTHONDONTWRITEBYTECODE=1 PROJ_NETWORK=OFF
exec .venv-nicegui/bin/python -B -m digitaltwins.nicegui_app "$@"
