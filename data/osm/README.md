# Fuentes OSM de solo lectura

`sources.json` fija cuatro recursos locales mediante ruta desde `DC_X`, ruta
absoluta de la inspección, tamaño, SHA-256, fecha de los datos y procedencia.
`osm-sv-pbf-20261014` es la entrada recomendada para SUMO.

No se copian, enlazan ni modifican los archivos originales. Leer el PBF por su
ruta; escribir recortes, XML y redes únicamente dentro de `outputs/pilot/`.
Para bases SQLite o GeoPackage usar `mode=ro&immutable=1`, `query_only=ON` y
extensiones deshabilitadas. No ejecutar preparadores históricos contra los
repositorios fuente.

Validación desde la raíz de DigitalTwins:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.doctor --verify-source
```

El PBF de octubre y el GeoPackage de agosto son cortes diferentes. El índice
topológico SQLite deriva exclusivamente del PBF. El ZIP contiene exactamente
el GeoPackage registrado, verificado mediante SHA-256 del miembro sin extraerlo.

Los datos son **© OpenStreetMap contributors**, procesados por Geofabrik,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Conservar estos avisos y los manifiestos junto a los derivados que se compartan.
