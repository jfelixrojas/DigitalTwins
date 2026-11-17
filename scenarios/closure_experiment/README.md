# Primer cierre virtual — intervención 004

Se prohíbe `passenger` en los dos carriles del enlace dirigido `1257993561#5`
entre 0 y 1800 s. La red y los 150 vehículos originales son copias byte a byte
de los insumos verificados en `outputs/pilot_controlled_verified/`.

Desde la raíz de `DigitalTwins`, usando una salida nueva:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.closure --output outputs/closure_reproduction
```

Requiere las herramientas y bibliotecas ya instaladas: Python 3.11+, SUMO
1.28.0, su módulo TraCI incluido y Matplotlib/NumPy. No instala ni descarga
dependencias. TraCI utiliza un puerto local temporal para observar la simulación;
el entorno de ejecución debe permitir ese socket. No hay conexiones con
infraestructura vial ni servicios externos.

[experiment.json](experiment.json) fija alcance y asignación.
[closure.add.xml](closure.add.xml) contiene un único `closingReroute` con
restricciones efectivas. Su lista `disallow` conserva las clases originalmente
prohibidas y añade `passenger`, para no habilitar otras clases por accidente.
El rerouter se encuentra en `198404000`, origen de W_E y anterior a los desvíos.
Solo cambia rutas que contienen el enlace cerrado; no se asignan destinos nuevos
ni se añade un dispositivo de reruteo periódico.

En el cierre se utiliza `device.rerouting.mode=8`, recomendado para cargar rutas
originales con permisos temporalmente modificados. Este modo permite que la
ruta inicial llegue al rerouter; no habilita físicamente el paso por los
carriles. Un único rerouter conoce el cierre completo. No se activa
`--ignore-route-errors`.

La validación independiente comprueba los movimientos originales sobre la red
abierta y las 150 alternativas propuestas sobre una variante estática con el
cierre. `duarouter --skip-new-routes true` debe conservar las secuencias sin
reparación. Esa variante y esas propuestas son productos de validación, no
insumos de la simulación dinámica.

La base conserva la configuración de la 003 y añade únicamente salidas de rutas.
El cierre añade el rerouter y el modo 8. Semilla 42, paso 1 s, horizonte 1800 s,
OD, vehículos, salidas, conducción y programas semafóricos permanecen fijados.
Se ejecutan `base/`, `closure/` y `closure_repeat/`, cada uno con:

- `controlled.sumocfg`, `edge_measures.add.xml` y registros de SUMO.
- `tripinfo.xml`, `summary.xml`, `statistics.xml`, `collisions.xml` y `edge_data.xml`.
- `vehroute.xml` con rutas reemplazadas, motivo, instante y tiempos de paso de
  la ruta final; los antecedentes reemplazados no se cuentan como trayectos ejecutados.
- `permission_monitor.csv`, dos muestras por paso durante los 1800 pasos;
  `permission_snapshots.json` comprueba todos los carriles al inicio, tras el
  primer paso y al final.
- Rutas ejecutadas, eventos de reruteo, métricas y series temporales derivadas.

La instrumentación añade el token `vehroute_<id>` al atributo `devices` de
`tripinfo`. Para la regresión con la 003 solo se retira ese token; todos los
demás atributos, agregados por enlace y pasos temporales deben coincidir.
Entre las dos corridas del cierre se comparan todos los atributos completos,
rutas, tiempos de paso, eventos, muestras de permisos y configuraciones.

`paired_vehicle_impacts.csv` conserva una fila por solicitud, incluso si un
vehículo no completa el recorrido; en ese caso su impacto de duración queda
sin valor. `comparison.json` declara denominadores y percentiles descriptivos;
`edge_interval_comparison.csv` y `edge_totals_comparison.csv` separan cantidades
vehiculares, tasas en veh/h y promedios temporales. Se generan seis figuras
PNG/SVG con manifiesto de fuentes.

Es un contrafactual sintético condicionado a esta carga, regla de información,
red, conductor y semilla. No calibra tráfico real ni implementa CTM/LTM.
Ver el [informe](../../docs/closure_experiment_report.md).
