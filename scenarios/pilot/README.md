# Piloto SUMO de Alameda Roosevelt

La intervención 002 ejecutó y repitió el escenario base con SUMO 1.28.0:
**150 solicitudes sintéticas, 109 rutas válidas, 109 recorridos completados**,
sin pendientes, teletransportes ni colisiones. Los 41 viajes rechazados se
conservan con IDs, extremos y causas. El resultado es una prueba técnica;
la demanda y los semáforos no están calibrados con observaciones reales.

El [informe](../../docs/pilot_report.md) registra resultados, advertencias,
instalación, restricciones de giro y recomendaciones. Las salidas finales
están en [outputs/pilot_verified](../../outputs/pilot_verified/).

## Reproducir todo el proceso

Desde la raíz de DigitalTwins:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.pilot --output outputs/pilot_reproduction
```

Usar un directorio de salida nuevo en cada ejecución. El comando rechaza
sobrescribir uno existente y solo escribe dentro de `DigitalTwins/outputs/`.
No instala herramientas ni consulta Internet. Conserva las evidencias si una
etapa falla y devuelve código distinto de cero.

El ejecutor necesita Python 3.11 o posterior, SUMO **1.28.0**, `netconvert`,
`duarouter`, Osmium y una base PROJ compatible. En este Mac se instalaron SUMO
mediante su paquete oficial y Osmium 1.19.1 mediante Homebrew, con aprobación.
Se reutilizan los datos PROJ 9.5.1 de PyProj ya existente; no se cambió ningún
entorno Python. Los hashes y rutas efectivos quedan en cada manifiesto.

El ejecutor detecta la instalación oficial macOS 1.28.0 y configura el entorno
solo para sus procesos. En otra instalación establecer `SUMO_HOME` y `PATH`.
Para ejecutar el diagnóstico existente en este Mac:

```sh
DIGITALTWINS_SUMO_PREFIX=/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO
export SUMO_HOME="$DIGITALTWINS_SUMO_PREFIX/share/sumo"
export PATH="$DIGITALTWINS_SUMO_PREFIX/bin:/opt/homebrew/bin:$PATH"
PYTHONPATH=src python3 -B -m digitaltwins.doctor --verify-source --require-sumo
```

`PROJ_DATA` puede señalar otro directorio compatible que contenga `proj.db`.
Si no se define, el ejecutor busca datos empaquetados y después los datos de
PyProj ya instalado, sin importar su runtime ni descargar recursos. Registra
el hash de la base realmente utilizada y fija `PROJ_NETWORK=OFF`.

XQuartz no se instaló y la interfaz gráfica no se probó. Su ausencia no
bloquea este proceso por línea de comandos.

## Entrada, ventana y conversiones

Se lee el PBF de octubre fijado en `data/osm/sources.json`, conservando su
ubicación original de solo lectura. SHA-256:
`73369769b9a7f45dd9f0b3a44511da0c29101c7268805b9c9f415114a6c27672`.

La ventana inicial sigue siendo `[-89.216,13.699,-89.207,13.705]`, CRS84,
longitud/latitud, alrededor de Alameda Franklin Delano Roosevelt en San
Salvador. No se amplió manualmente. La estrategia `smart` completa vías y
relaciones `restriction`, por lo que las geometrías pueden salir de ella.

Las etapas registradas en `commands.json` son:

1. Comprobación del hash original y versiones exactas de herramientas SUMO.
2. `osmium extract --strategy=smart -S types=restriction` con el bbox indicado.
3. `osmium cat` a OSM XML y `osmium check-refs` para nodos de vías.
4. Auditoría de miembros de restricciones del XML.
5. `netconvert` con `--keep-edges.by-vclass passenger`, `--osm.turn-lanes true`,
   `--osm.annotate-defaults true` y `--output.original-names true`.
6. Comprobación de movimientos, componentes y restricciones en la red SUMO.
7. Generación de solicitudes originales y rutas válidas, sin volver a sortear
   los viajes rechazados para llenar la cuota.
8. Simulación base y repetición, comparación de métricas, balances y hashes.

La red final tiene 350 enlaces externos dirigidos, 604 carriles, 243 nodos
junction externos (incluidos 21 extremos), 810 conexiones externas entre
carriles y 18 programas semafóricos. Sus tres componentes débiles contienen
321, 21 y 8 enlaces. Las 11 restricciones de giro del recorte tienen miembros
completos y se comprobaron contra los movimientos para automóviles.

## Demanda, corridas y criterios

La semilla es **42**, `begin=0`, `end=900`, `period=6`, clase `passenger`;
el horizonte de simulación termina en 1800 segundos. Se mantiene la receta
inicial y se hace explícito el tratamiento de fallos de enrutamiento.

En SUMO 1.28.0 `randomTrips.py --validate` intenta volver a sortear OD sin ruta.
Se añadió `--min-success-rate 1` para conservar los rechazos originales y
`--threads 1` para fijar la ejecución de validación. Una primera generación
con `--no-validate` conserva las 150 solicitudes. La segunda usa `--validate`,
`--verbose` y `--error-log`, con los mismos parámetros y semilla.

La herramienta oficial usa internamente `duarouter --ignore-errors` para
separar rutas válidas; ese comportamiento está documentado en las evidencias.
No se interpreta como que todos los viajes fueron aceptados. No se suprimen
los registros ni se ignoran errores del simulador. Los 109 viajes aceptados
conservan origen, destino y hora de salida de sus solicitudes originales.

De los 41 rechazos, 29 cruzan componentes diferentes y 12 no tienen camino
dirigido dentro de su componente. No se eliminan calles ni se inventan
conexiones para hacerlos desaparecer. Ambas simulaciones completan los 109
recorridos, con duración media 114,83 s, espera media detenida 33,47 s y
`timeLoss` medio 54,05 s.

El éxito requiere red no vacía, conexiones y rutas válidas, ausencia de
violaciones de giro detectadas, al menos un vehículo completado y balances
coherentes. Se exige además igualdad de métricas entre base y repetición.
Las marcas de generación XML y las medidas de CPU/reloj no se consideran
métricas deterministas.

## Artefactos y diagnóstico

Cada directorio de salida contiene:

- `pilot.osm.pbf`, `pilot.osm.xml` y `pilot.net.xml`.
- `requested.trips.xml`, `pilot.trips.xml` y `pilot.rou.xml`.
- `base/` y `repeat/`, con `pilot.sumocfg`, `tripinfo.xml`, `statistics.xml`,
  `summary.xml`, `collisions.xml`, `sumo.errors.log` y `metrics.json`.
- `summary.json`, `osm_audit.json`, `network_audit.json`, `routing_audit.json`,
  `warnings.json` y `reproducibility.json`.
- `manifest.json`, `environment.json`, `commands.json`, `logs/` y `ATTRIBUTION.txt`.

`pilot.sumocfg` en este directorio fuente es la plantilla; el ejecutor genera
las dos configuraciones finales con rutas y salidas locales en `outputs/`.
La red y las rutas de ambas corridas son compartidas y sus configuraciones
tienen contenido idéntico.

Las advertencias de conversión, defaults y semáforos sintéticos deben
revisarse antes de atribuir fidelidad al tráfico real. La primera ejecución
con avisos de PROJ se conserva en `outputs/pilot/`; la corregida y entregada,
en `outputs/pilot_verified/`. Los detalles están en el informe.

Pruebas focales sin instalar pytest:

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Datos: **© OpenStreetMap contributors**, procesados por **Geofabrik GmbH**,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Conservar esos avisos
al compartir derivados. No se accede a sistemas de control, conteos ni Waze.
