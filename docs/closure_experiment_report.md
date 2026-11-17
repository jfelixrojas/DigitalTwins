# Intervención 004 — primer cierre virtual y comparación contrafactual

El cierre del enlace dirigido **`1257993561#5`**, Alameda Franklin Delano
Roosevelt hacia el este, fue efectivo para `passenger` durante **[0, 1800) s**.
Los 150 vehículos originales completaron tanto la base como el cierre. Los
45 W_E cambiaron de ruta; los otros 105 conservaron sus secuencias. No hubo
rechazos, pendientes, eliminaciones, teletransportes ni colisiones.

El recorrido medio aumentó **132,90 → 135,60 s: +2,70 s (+2,03 %)**. La
reducción de `timeLoss` y tiempo detenido no compensa ese aumento del indicador
principal. Es un resultado sintético condicionado a estos parámetros y semilla,
sin calibración ni atribución a las condiciones reales de San Salvador.

Resultados canónicos: `outputs/closure_experiment_verified/`.
[Resumen](../outputs/closure_experiment_verified/summary.json),
[comparación](../outputs/closure_experiment_verified/comparison.json),
[manifiesto](../outputs/closure_experiment_verified/manifest.json) y
[validación final](../outputs/intervention004/final_validation.json).

## A. Diseño y mecanismo de cierre

La base reutiliza red, identificadores, seis OD, horas de salida y tipo de
conductor de la intervención 003: semilla 42, paso 1 s, horizonte 1800 s,
llegadas hasta 900 s y agregación de enlaces cada 60 s. Se mantiene la condición
inicial vacía, los atributos viales y los 18 programas semafóricos virtuales,
estáticos, de 90 s.

Un único `closingReroute` en
[closure.add.xml](../scenarios/closure_experiment/closure.add.xml) añade
`passenger` a las clases originalmente prohibidas en ambos carriles, conservando
las otras restricciones. El punto de información está en **`198404000`**,
origen de W_E y anterior a las bifurcaciones. Probabilidad 1, sin asignación
de destinos, terminación de rutas ni dispositivo de reruteo periódico.

Se verificaron esquema y módulos TraCI instalados de SUMO 1.28.0 y la
[documentación oficial](https://sumo.dlr.de/docs/Simulation/Rerouter.html).
El cierre usa `device.rerouting.mode=8` para cargar rutas originales antes
de conocer permisos transitorios. El rerouter comunica la restricción y
calcula un recorrido que la evita; los permisos físicos impiden el paso.
No se activa `--ignore-route-errors`. El
[código oficial de la versión 1.28.0](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/src/microsim/trigger/MSTriggeredRerouter.cpp)
confirma la modificación de permisos y el tratamiento del modo 8.

Este mecanismo conserva byte a byte la misma red y demanda de entrada,
registra cambios de ruta y permite comprobar los permisos efectivos. La
variante estática cerrada se usa solo para validación independiente.

Las diferencias adicionales declaradas son instrumentales:

- Ambas condiciones añaden `vehroute-output`, tiempos de salida por enlace,
  orden de escritura y rutas no terminadas.
- TraCI avanza el simulador local y consulta estados. El observador no envía
  cambios de rutas, semáforos, velocidades o permisos.
- La salida añade `vehroute_<id>` a `tripinfo.devices`. Para la regresión con
  la 003 solo se retira ese token; los demás atributos deben ser idénticos.
- Solo el cierre incorpora su archivo adicional y el modo 8. Las diferencias
  exactas están en [configuration_differences.json](../outputs/intervention004/configuration_differences.json).

### Comprobación efectiva

Cada corrida registra **3600 muestras carril-paso**, dos carriles por 1800
pasos. En ambas corridas de cierre todas prohíben `passenger` y todas tienen
cero vehículos sobre el enlace. Se comparan los permisos de todos los carriles
antes de los eventos iniciales, tras el primer paso y al final: solo se añade
esa prohibición en los dos carriles seleccionados.

La instantánea de carga precede al planificador temporal y no contiene
vehículos insertados. El evento de tiempo cero aplica el cierre antes de
la circulación. La primera muestra posterior cubre [0, 1) s; la última,
[1799, 1800) s.

| Evidencia del enlace seleccionado | Base | Cierre y repetición |
|---|---:|---:|
| Vehículos únicos detectados | 45 | 0 |
| Rutas finales que lo recorren | 45 | 0 |
| `entered` acumulado | 45 veh | 0 veh |
| `sampledSeconds` acumulado | 223,95 veh·s | 0 veh·s |

Ver [monitor](../outputs/closure_experiment_verified/closure/closure_monitor.json),
[muestras](../outputs/closure_experiment_verified/closure/permission_monitor.csv),
[instantáneas completas](../outputs/closure_experiment_verified/closure/permission_snapshots.json)
y [rutas con tiempos](../outputs/closure_experiment_verified/closure/vehroute.xml).

## B. Conservación de demanda y validación de rutas

La red simulada, `controlled.rou.xml`, `controlled.trips.xml`, el calendario
y la especificación de demanda son copias idénticas de los insumos verificados
de la 003. No se regeneran ni sustituyen viajes. Los 150 identificadores se
conservan antes de simular y aparecen en cada condición.

Los movimientos originales se comprobaron contra permisos y conexiones de la
red abierta. Se construyeron alternativas para los 45 W_E y se conservaron las
otras 105 rutas. Las **150 propuestas** se validaron con `duarouter` estricto
sobre `validation_only_closed.net.xml`, con prohibición estática en ambos
carriles. `--skip-new-routes true` conservó cada secuencia sin reparación ni
supresión de errores. Los seis OD conservaron destinos alcanzables.

Esta validación independiente evita que el modo 8 oculte discontinuidades o
giros inválidos. Las propuestas y la variante estática son evidencias separadas;
la simulación recibe las rutas originales. Se comprueba de nuevo cada ruta
ejecutada, sus extremos y sus tiempos de salida por enlace. Los antecedentes
reemplazados no se cuentan como pasos realizados.
[Validación de demanda](../outputs/closure_experiment_verified/demand_validation.json).

Los 45 eventos `virtual_closure` ocurren en `198404000`, a la hora de salida
de cada W_E. No hay otros cambios de recorrido. Las rutas finales coinciden
con las alternativas propuestas y evitan el enlace cerrado. Ver
[rutas ejecutadas](../outputs/closure_experiment_verified/closure/executed_routes.json)
y [eventos de reruteo](../outputs/closure_experiment_verified/closure/rerouting_events.json).

## C. Comparación de red y movimientos

Las diferencias son **cierre menos base**. Los porcentajes de estas tablas
usan la media o total base correspondiente; el promedio de porcentajes
individuales se conserva por separado en JSON. Hay 150 pares completados.

| Indicador | Base | Cierre | Diferencia |
|---|---:|---:|---:|
| Solicitados / insertados / completados | 150 / 150 / 150 | 150 / 150 / 150 | 0 |
| Rechazados / pendientes / eliminados | 0 / 0 / 0 | 0 / 0 / 0 | 0 |
| Recorrido medio | 132,90 s | 135,60 s | **+2,70 s (+2,03 %)** |
| Tiempo total de recorrido | 19 935 s | 20 340 s | **+405 s (+2,03 %)** |
| Longitud media | 1333,839 m | 1365,504 m | +31,665 m (+2,37 %) |
| Longitud total | 200 075,85 m | 204 825,60 m | +4749,75 m |
| `waitingTime` medio | 32,393 s | 30,320 s | −2,073 s (−6,40 %) |
| `timeLoss` medio | 51,006 s | 50,528 s | −0,478 s (−0,94 %) |
| Demora media de inserción | 0 s | 0 s | 0 s; porcentaje indefinido sobre cero |
| Teletransportes / colisiones | 0 / 0 | 0 / 0 | 0 |
| Frenadas / paradas de emergencia | 0 / 0 | 0 / 0 | 0 |
| Máximo simultáneo en red | 25 veh | 28 veh | +3 veh |
| Máximo simultáneo detenido | 13 veh | 13 veh | 0 veh |
| Última llegada | 1035 s | 1038 s | +3 s |

Las medias se calculan desde los valores por vehículo escritos en `tripinfo`,
con su precisión de salida. Se conservan XML y cifras estructuradas sin el
redondeo de estas tablas.

![Tiempo por movimiento](../outputs/closure_experiment_verified/visual/stream_travel_times.png)

| Movimiento | Viajes | Recorrido base → cierre (s) | Cambio medio (s; %) | Δ `waitingTime` (s) | Δ `timeLoss` (s) | Δ longitud (m) |
|---|---:|---:|---:|---:|---:|---:|
| **W_E** | 45 | 115,58 → 120,36 | **+4,78; +4,13 %** | −10,22 | −5,76 | **+105,55** |
| E_W | 45 | 124,64 → 124,76 | +0,11; +0,09 % | −0,04 | +0,07 | 0 |
| N_W | 15 | 204,73 → 204,73 | 0; 0 % | −0,13 | −0,10 | 0 |
| E_N | 15 | 153,87 → 153,87 | 0; 0 % | 0 | +0,17 | 0 |
| **N_E** | 15 | 187,67 → 199,93 | **+12,27; +6,54 %** | +10,20 | +12,14 | 0 |
| W_S | 15 | 62,07 → 62,13 | +0,07; +0,11 % | 0 | +0,06 | 0 |

Los 45 W_E recorren 105,55 m adicionales cada uno (+7,96 %). La referencia de
velocidad ideal de `timeLoss` también depende de la ruta: recorrer más distancia
puede reducir detenciones y `timeLoss` y aun así aumentar duración. Esa caída
no se presenta como mejora global. `waitingTime` y `timeLoss` se solapan;
no se suman como componentes independientes.

## D. Alternativa ejecutada e impactos por vehículo

![Rutas efectivamente utilizadas](../outputs/closure_experiment_verified/visual/routes_comparison.png)

Todos los W_E salen de Roosevelt después de `1257993561#3`, toman
**`-175606174` (35 Avenida Sur)** y **`-198404021` (Calle el Progreso)**, y
vuelven en `1225540290#0`. Dejan de recorrer `1257993561#4`, `#5` y `#6`;
solo `#5` pierde permiso, los otros dos siguen abiertos. Es una única
alternativa efectivamente usada por 45 vehículos.

La [tabla emparejada](../outputs/closure_experiment_verified/paired_vehicle_impacts.csv)
conserva 150 filas: ID, movimiento, exposición original, estados de llegada,
valores base/cierre y diferencias absolutas y porcentuales de duración,
longitud, detención, `timeLoss` y demora de inserción. Un par no completado
seguiría identificado con impacto de duración vacío; aquí los 150 completan.

| Grupo | Δ duración media | Mediana | P05 | P95 | Mínimo | Máximo | Aumentan / disminuyen / iguales |
|---|---:|---:|---:|---:|---:|---:|---:|
| Red, 150 pares | +2,70 s | 0 s | −13 s | +19 s | −33 s | +90 s | 62 / 38 / 50 |
| W_E, 45 expuestos | +4,78 s | **+15 s** | −31,8 s | +19 s | −33 s | +19 s | 30 / 15 / 0 |
| Otros, 105 | +1,81 s | 0 s | −1 s | +2 s | −4 s | **+90 s** | 32 / 23 / 50 |

Los percentiles usan interpolación lineal entre rangos (método 7). Describen
estos vehículos en una realización, sin constituir intervalos de confianza.
La diferencia entre media y mediana W_E muestra heterogeneidad: quince viajes
se benefician temporalmente aun recorriendo más distancia y treinta empeoran.

![Distribución emparejada](../outputs/closure_experiment_verified/visual/paired_travel_impacts.png)

Los 405 s adicionales se reparten entre **215 s en W_E** y **190 s en los
otros movimientos**. N_E aporta 184 s de esos 190 s indirectos. Dos casos
concentran 178 s: `N_E.0007` (+88 s, +79 s detenido) y `N_E.0013` (+90 s,
+82 s detenido). Ambos conservan ruta y longitud. El primer retraso grande
en tiempos de salida aparece en `1182057747`: +60 s en cada caso, antes del
movimiento controlado por `4011718406`.
[Diagnóstico de casos](../outputs/intervention004/indirect_outliers.json).

Esto identifica dónde aparece la diferencia registrada. La relación exacta
entre interacciones microscópicas, llegadas a verde y estados semafóricos
requiere sensibilidad o más detalle temporal; no se atribuye automáticamente
el retraso a saturación del desvío. Los programas son iguales, pero puede
cambiar el instante de llegada a sus fases.

## E. Flujos, ocupación y acumulación

Cada condición conserva **10 500 registros enlace-intervalo**: 350 enlaces
externos por 30 períodos de 60 s, incluidos los vacíos. Se entregan XML,
CSV por condición, [comparación temporal](../outputs/closure_experiment_verified/edge_interval_comparison.csv)
y [totales por enlace](../outputs/closure_experiment_verified/edge_totals_comparison.csv).

| Enlace | Entradas base → cierre | Cambio | Ocupación máxima base → cierre, por intervalo de 60 s |
|---|---:|---:|---:|
| `1257993561#4` | 45 → 0 veh | −45 veh | 1,06 → 0 % |
| **`1257993561#5` cerrado** | **45 → 0 veh** | **−45 veh** | **1,11 → 0 %** |
| `1257993561#6` | 45 → 0 veh | −45 veh | 37,86 → 0 % |
| `-175606174`, 35 Avenida Sur | 0 → 45 veh | +45 veh | 0 → 3,81 % |
| `-198404021`, Calle el Progreso | 0 → 45 veh | +45 veh | 0 → 3,02 % |

El flujo de entrada por período es `3600 × entered / 60`, en veh/h; alcanza
240 veh/h en el período de mayor conteo de ambos desvíos. Las 45 entradas del
horizonte son una **cantidad**, sin etiquetarlas como 45 veh/h. Los CSV por
condición también conservan `left`, flujo de salida, inicios/finales de viaje
dentro del enlace, densidad, velocidad y tiempos agregados.

![Flujos y ocupaciones](../outputs/closure_experiment_verified/visual/affected_edge_timeseries.png)

La ocupación es el porcentaje nativo SUMO; `mean_vehicles` corresponde a
`sampledSeconds / duración_del_intervalo`, en veh. Su máximo entre enlaces
e intervalos pasa de 2,4692 a 2,4765 veh; el máximo porcentual de la red pasa
de 96,67 a 97,08 %. Los segmentos muy cortos limitan su interpretación física.
Se conservan valores completos y no se suman porcentajes para obtener la
acumulación total.

Para acumulación de red se usa `summary.running`, incluyendo conexiones
internas. Se verifica la contabilidad en cada paso. Con paso de 1 s, su suma
temporal es **19 935 veh·s en base y 20 340 veh·s en cierre**, exactamente
igual al tiempo total de viaje obtenido por otra salida.

![Indicadores del sistema](../outputs/closure_experiment_verified/visual/system_indicators.png)

Conforme a GDM-MATH-001 v1.0, son **estados simulados** y agregados
microscópicos: los detenidos de la red no son una cola única `Q_t`, y el
promedio por enlace no constituye el estado de celda CTM `n_{i,t}`. Un
aumento de distancia tampoco mide por sí mismo congestión.

## F. Repetición, pruebas e integridad

Se ejecutaron `base/`, `closure/` y `closure_repeat/`. La base reproduce todos
los atributos de `tripinfo` de la 003 tras retirar únicamente el token añadido
de instrumentación. También coinciden atributos de todos los intervalos de
enlaces y pasos de `summary`, excluyendo solo CPU.
[Regresión de base](../outputs/closure_experiment_verified/base_regression.json).

Las dos corridas de cierre coinciden en métricas, atributos completos por
vehículo, rutas finales y tiempos de salida por enlace, eventos de reruteo,
intervalos de enlaces, series temporales salvo CPU, muestras de permisos y
configuración. [Repetibilidad](../outputs/closure_experiment_verified/reproducibility.json).

Pasan **25 pruebas**: las 15 anteriores y diez nuevas sobre cierre, movimientos,
conservación, pendientes y comparación. Las cuatro bitácoras canónicas tienen
cero advertencias y errores. Los avisos heredados de la conversión siguen
documentados en la 003; no se borraron ni desactivaron. No hubo bloqueo en
las corridas canónicas.

La auditoría compara tamaños y SHA-256 de **2594 archivos protegidos
preexistentes**: evidencias anteriores, código previo, contrato y documentos
originales. **2591 coinciden íntegramente**. Tres diferencias corresponden
a metadatos Finder: `outputs/.DS_Store`, `outputs/pilot_verified/.DS_Store` y
`scenarios/.DS_Store`. No se escribieron directamente con los comandos de esta
intervención; no se determinó el proceso que los modificó. Sus hashes antes y
después quedan registrados y no se restauraron ni sobrescribieron.

Los datos y evidencias experimentales conservan su contenido. Se verifican
también las cuatro fuentes locales contra el manifiesto, los metadatos de los
árboles vecinos y estados Git disponibles, con las exclusiones registradas.
[Validación final](../outputs/intervention004/final_validation.json) e
[inventario posterior](../outputs/intervention004/protection_after.json).

El manifiesto registra herramientas y binarios 1.28.0, PROJ, Python, fuentes,
código, configuración, supuestos y hashes de los productos. El manifiesto
visual registra hashes de las fuentes usadas para dibujar; las seis figuras
se revisaron visualmente.

Los sondeos preliminares están separados en `outputs/intervention004/` y no
forman parte del resultado canónico. El primero no pudo iniciar su puerto
local; el siguiente verificó el mecanismo antes de conservar además todas las
restricciones originales de otras clases en la configuración definitiva.

## G. Reproducción y archivos entregados

Desde la raíz de `DigitalTwins`, utilizando una salida nueva:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.closure --output outputs/closure_reproduction
```

Requiere Python 3.11+, SUMO 1.28.0 y su TraCI incluido, Matplotlib y NumPy ya
instalados. El entorno debe permitir el puerto TraCI local temporal. No se
instalaron herramientas ni descargaron datos. SUMO-GUI sigue sin servidor X;
se usan figuras estáticas, sin instalar XQuartz.

| Cambio | Archivos o directorios |
|---|---|
| Nuevos módulos | `src/digitaltwins/closure.py`, `closure_analysis.py`, `closure_plots.py` |
| Escenario | `scenarios/closure_experiment/experiment.json`, `closure.add.xml`, `README.md` |
| Pruebas e informe | `tests/test_closure.py`, `docs/closure_experiment_report.md` |
| Documentación modificada | `README.md`, `tests/README.md` |
| Productos nuevos | `outputs/closure_experiment_verified/`, `outputs/intervention004/` |
| Eliminaciones | Ningún archivo previo; solo temporales propios de pruebas. |

[Inventario de cambios](../outputs/intervention004/changes.json). Se conservan
los módulos anteriores, dependencias, datos, documentos protegidos y repositorios
vecinos. No hubo publicación ni operaciones Git remotas.

## H. Limitaciones y siguiente experimento

El cierre se informa al salir del origen: **aviso anticipado perfecto**,
sin incumplimiento, búsqueda, información tardía ni elección entre varias rutas.
La conducción conserva `speedFactor=1`, `speedDev=0` y los demás valores
predeterminados de la 003.

Las llegadas periódicas pueden sincronizarse con semáforos virtuales de 90 s.
Una semilla no estima incertidumbre ni demuestra robustez de los impactos.
Conservar semilla y parámetros permite repetir el contrafactual, pero no
fija trayectorias idénticas al cambiar recorridos e interacciones.

En ambos desvíos, 13,89 m/s (≈50 km/h) es velocidad predeterminada. En
35 Avenida Sur el carril por sentido también es predeterminado; Calle el
Progreso tiene uno por sentido a partir de dos carriles totales OSM. Estos
supuestos y las advertencias geométricas y velocidades incompletas heredadas
limitan una interpretación física. Esta carga no demuestra capacidad para
otras demandas.

**Siguiente experimento recomendado:** repetir pares base/cierre para varias
semillas y desfases semafóricos virtuales comunes a ambas condiciones,
manteniendo los mismos 150 viajes dentro de cada par. Priorizar los dos casos
N_E y la mediana W_E para evaluar si los 405 s adicionales persisten ante
cambios temporales, antes de ampliar carga o interpretar efectos como política
de movilidad.

No se integraron conteos, Waze o registros reales; no se implementaron CTM,
LTM, GNN o interfaces web. Todas las operaciones pertenecen al laboratorio,
sin escritura hacia infraestructura real.

Datos derivados: **© OpenStreetMap contributors**, procesados por Geofabrik,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); atribución conservada
en `ATTRIBUTION.txt`.
