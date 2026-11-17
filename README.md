# DigitalTwins

Laboratorio experimental de movilidad urbana de **El Salvador**, basado en
conteos vehiculares, registros semafóricos y Waze. El propósito y los límites
están en [docs/concept.md](docs/concept.md). La infraestructura real es una
fuente de observación; toda intervención se simula en un entorno aislado.

La intervención 004 compara la base controlada con un cierre virtual efectivo
de `1257993561#5`, Roosevelt hacia el este. **Los 150 vehículos completan ambos
escenarios**; los 45 W_E se desvían sin atravesar el enlace cerrado. El recorrido
medio aumenta de 132,90 a 135,60 s (+2,03 %), aunque baja `timeLoss`. Dos corridas
del cierre reproducen métricas, rutas ejecutadas y permisos. Es un experimento
sintético; el gemelo aún no está calibrado.

CTM será la referencia física experimental y LTM el comparador; SUMO es el
entorno microscópico inicial. No hay modelos CTM, LTM o IA implementados.

## Contenido del repositorio

Git conserva código, escenarios, pruebas, documentación y el manifiesto de
fuentes. Los datos OSM y los archivos generados de `outputs/` quedan excluidos;
los enlaces de los informes a esa carpeta corresponden a evidencias locales.
Clonar este repositorio no descarga esas fuentes ni los resultados verificados.
Las recetas requieren los insumos locales fijados en
[data/osm/sources.json](data/osm/sources.json) y las herramientas documentadas.

## Reproducir el cierre virtual — intervención 004

Desde esta raíz, usando una salida nueva:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.closure --output outputs/closure_reproduction
```

El comando ejecuta base, cierre y repetición, valida las alternativas de forma
estricta y genera comparaciones por red, movimiento, vehículo y enlace. Mantiene
la red y la demanda verificadas de la 003; `closingReroute` prohíbe `passenger`
durante 0–1800 s. TraCI, incluido con SUMO, observa permisos mediante un puerto
local temporal; el entorno debe permitir ese socket.

Resultados: [informe](docs/closure_experiment_report.md),
[comparación estructurada](outputs/closure_experiment_verified/comparison.json),
[repetición](outputs/closure_experiment_verified/reproducibility.json),
[manifiesto](outputs/closure_experiment_verified/manifest.json) y
[receta](scenarios/closure_experiment/README.md).

## Reproducir el escenario controlado — intervención 003

Desde esta raíz, con SUMO 1.28.0 y los paquetes de visualización ya presentes
en el Mac:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.controlled --output outputs/pilot_controlled_reproduction
```

El directorio de salida debe ser nuevo. El comando verifica los insumos
fijados de la intervención 002, copia su red, diagnostica conectividad y
atributos, genera la demanda explícita, valida alternativas sin cerrar vías,
ejecuta dos simulaciones y produce seis figuras PNG/SVG. La especificación
está en [scenarios/pilot_controlled/](scenarios/pilot_controlled/README.md).

Resultados verificados: [informe](docs/pilot_controlled_report.md),
[métricas](outputs/pilot_controlled_verified/summary.json),
[repetición](outputs/pilot_controlled_verified/reproducibility.json),
[manifiesto](outputs/pilot_controlled_verified/manifest.json) y
[figuras](outputs/pilot_controlled_verified/visual/manifest.json).
SUMO-GUI y Netedit fallan por falta de un servidor X; las figuras se generan
localmente desde los XML. No se instalaron herramientas en esta intervención.

## Reproducir el piloto aleatorio — regresión de la intervención 002

Desde esta raíz, con las herramientas instaladas:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.pilot --output outputs/pilot_reproduction
```

El directorio de salida debe ser nuevo; el ejecutor conserva las evidencias
anteriores y no las sobrescribe. Usa el PBF local fijado, recorta, convierte,
audita movimientos, genera demanda y ejecuta dos corridas con semilla 42.
Todos los productos quedan dentro de `outputs/`.

Resultados entregados: [informe](docs/pilot_report.md),
[métricas](outputs/pilot_verified/summary.json),
[reproducibilidad](outputs/pilot_verified/reproducibility.json) y
[manifiesto de insumos](outputs/pilot_verified/manifest.json).

Este piloto solicita 150 viajes aleatorios y acepta/completa 109. La
regresión completa de la intervención 003 conserva esos resultados y los
atributos por vehículo: [comparación](outputs/intervention003/regression_comparison.json).
Sus evidencias originales permanecen protegidas en `outputs/pilot_verified/`.

## Empezar sin instalar nada

Desde la raíz de este repositorio, con Python 3.11 o posterior:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.doctor --verify-source
```

El diagnóstico usa la biblioteca estándar y solo lee archivos. Comprueba
tamaños y hashes del manifiesto [data/osm/sources.json](data/osm/sources.json),
busca ejecutables en `PATH` y consulta las versiones de paquetes del intérprete
actual. Devuelve código 1 ante fuentes ausentes o distintas. Para exigir además
los requisitos de la receta piloto:

```sh
DIGITALTWINS_SUMO_PREFIX=/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO
export SUMO_HOME="$DIGITALTWINS_SUMO_PREFIX/share/sumo"
export PATH="$DIGITALTWINS_SUMO_PREFIX/bin:/opt/homebrew/bin:$PATH"
PYTHONPATH=src python3 -B -m digitaltwins.doctor --verify-source --require-sumo
```

En el Mac hay Python 3.11.5, SUMO 1.28.0 y Osmium 1.19.1. El ejecutor del
piloto configura su entorno automáticamente, sin editar perfiles globales.
Reutiliza los datos PROJ de PyProj existentes y registra su hash; XQuartz no
se instaló. El [plan aprobado](docs/intervention002_install_plan.md) y las
evidencias en `outputs/intervention002/` detallan la instalación.

## Recursos y primer piloto

- [Inventario OSM y diagnóstico](docs/osm_inventory.md): rutas absolutas,
  cobertura, versiones, atributos, duplicaciones, licencias y limitaciones.
- [Fuentes sin copias](data/osm/README.md): datos originales en los repositorios
  vecinos, consultados exclusivamente en lectura.
- [Receta piloto](scenarios/pilot/README.md): recorte local de Alameda Franklin
  Delano Roosevelt y su entorno en San Salvador, conversión a SUMO y demanda
  sintética con semilla fija; instrucciones verificadas en la intervención 002.
- [Demanda controlada](scenarios/pilot_controlled/README.md): seis pares
  origen-destino, tasas periódicas, diagnósticos y reglas de comparación futura.
- [Cierre virtual](scenarios/closure_experiment/README.md): cierre efectivo,
  rutas realmente ejecutadas, conservación de demanda y comparación emparejada.

Los originales permanecen en `../savia-x-lab` y `../x_red_social`. Los caminos
del manifiesto se resuelven desde el directorio padre `DC_X`, por lo que el
conjunto puede reubicarse manteniendo esa estructura. No hay imports ni
dependencias de código de SAVIA-X en el paquete `digitaltwins`.

## Organización

```text
DigitalTwins/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .gitignore
├── docs/                 # documentos existentes e inventario nuevo
├── data/osm/             # manifiesto y notas; sin extractos duplicados
├── scenarios/            # piloto aleatorio y especificación controlada
├── src/digitaltwins/     # ejecutores, diagnóstico y figuras
├── tests/                # 25 pruebas de rutas, cierres, unidades y balances
└── outputs/              # productos generados, excluidos de Git
```

El diagnóstico y los ejecutores usan la biblioteca estándar. El piloto requiere las
herramientas SUMO/Osmium y una base PROJ compatible; en este Mac se reutiliza
la existente en PyProj. `pyproject.toml` no instala esas herramientas y usa
setuptools para un eventual empaquetado. El diagnóstico no requiere instalar
el paquete ni crear un entorno virtual.

Las figuras de la intervención 003 usan Matplotlib 3.10.3, PyProj 3.7.2 y
NumPy 1.26.4 ya instalados. Matplotlib y PyProj se declaran como dependencias
opcionales `visualization`; el comando controlado completo las necesita.
No se descargan datos, mapas ni dependencias durante su ejecución.

Pruebas focales, sin instalar pytest:

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Datos OSM: **© OpenStreetMap contributors**, procesados por Geofabrik,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Conservar atribución y procedencia en los productos derivados; los detalles
de cada recurso están en el inventario.
