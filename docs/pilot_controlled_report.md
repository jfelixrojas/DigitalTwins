# Intervención 003 — red inspeccionada y escenario base controlado

El corredor de Alameda Franklin Delano Roosevelt queda preparado como base
técnica para una comparación posterior: **150 solicitudes explícitas, 150 rutas
válidas y 150 viajes completados**, reproducidos en dos corridas. Se conserva
exactamente la red de la intervención 002. No se ejecutó ningún cierre.
La demanda, la conducción y los programas semafóricos son sintéticos o supuestos;
el escenario no representa todavía tráfico calibrado de San Salvador.

El resultado canónico está en
[`outputs/pilot_controlled_verified/`](../outputs/pilot_controlled_verified/summary.json).
El [manifiesto](../outputs/pilot_controlled_verified/manifest.json) fija entradas,
herramientas, código, configuración, semilla y hashes. La
[validación final](../outputs/intervention003/final_validation.json) reúne pruebas,
integridad, regresión y comprobaciones de resultados.

## Inspección visual y conservación de la red

Se probaron los ejecutables instalados `sumo-gui` y `netedit`, abriendo la red
protegida sin modificarla. Ambos terminaron con código 1 y
`FXApp::openDisplay: unable to open display :0.0`. `DISPLAY` está ausente y no
hay XQuartz. Se conservan [los comandos y resultados](../outputs/intervention003/gui_probe/result.json)
y sus registros; no se hicieron instalaciones.

La inspección continuó mediante XML de SUMO y seis figuras estáticas PNG/SVG,
generadas con Matplotlib y PyProj locales. Son evidencias de geometría y estados
sintéticos; no son capturas de una GUI ni observaciones de tránsito. No se
descargaron mapas ni se consultaron controladores reales.

![Componentes y ventana original](../outputs/pilot_controlled_verified/visual/network_components.png)

Se mantuvo la ventana CRS84 `[-89.216, 13.699, -89.207, 13.705]`. El método de
extracción conserva vías completas; por eso la geometría se extiende fuera de
ese rectángulo. No se amplió el recorte ni se conectaron componentes
artificialmente. `controlled.net.xml` es una copia de la red protegida, con
SHA-256 `5ffebc98d865aa238703cc39463d4a34128e83390e6a4b24611a9e280b6fe4d5`.
Los cambios de geometría, carriles, velocidades, conexiones y fases aplicados
en esta intervención son **cero**.

## Conectividad passenger y componentes menores

El diagnóstico usa permisos de carril, conexión y carril interno `via`. No hay
restricciones explícitas de cambio de carril en este insumo. El grafo contiene
350 enlaces externos, 810 conexiones entre carriles passenger y tres componentes
débilmente conexas:

| Componente | Enlaces | Diagnóstico |
|---|---:|---|
| 0 | 321 | Red principal; contiene los seis OD controlados. |
| 1 | 21 | Sector Héroes/49 Avenida; once vías OSM, con puentes y rampas. Hay evidencia de continuidad omitida por el recorte. |
| 2 | 8 | Vía residencial sin nombre `36967463`, bidireccional; conexiones vecinas quedan fuera del criterio de extracción. |

Se compararon las incidencias de nodos con el índice nacional de **octubre de
2026**, abierto con SQLite `mode=ro&immutable=1` y `query_only=ON`. No se
mezclaron fuentes de agosto. Para la componente 1 hay 14 incidencias vía-nodo
omitidas; para la 2 hay siete. Ninguna de esas vías vecinas tiene un nodo dentro
del rectángulo solicitado. Ejemplos verificables:

- Componente 1: vía `141448609` (49 Avenida Norte), nodo `631378180`, longitud
  `-89.2160965`, inmediatamente al oeste del borde; vía `179733669` (Héroes),
  nodo `1977373285`, latitud `13.7052897`, al norte. Dos vías conservadas
  (`179733828`, `627437184`) declaran `bridge=yes`, `layer=1`.
- Componente 2: vías residenciales `647608220` y `1124578632` inciden en
  `429848073`, longitud `-89.2068318`, al este; Calle El Ciro `874888864`
  incide en `8143909802`, también al este. La vía `36967463` declara
  `highway=residential`, `noname=yes`, sin etiquetas de acceso privado.

La evidencia favorece un efecto de frontera del recorte. La separación a
distinto nivel es una condición cartográfica legítima que debe respetarse;
la proximidad geométrica no autoriza una conexión. No se encontró evidencia
de acceso privado que explique estas dos componentes. El índice nacional
describe pertenencia a vías y etiquetas: no demuestra por sí solo una ruta
nacional válida con todas sus restricciones de giro.

Hay 85 componentes fuertemente conexas: una de 259 enlaces, una de ocho y 83
unitarias. Se identificaron **83 065 pares ordenados alcanzables de 122 500**,
incluyendo la diagonal (permanecer en el mismo enlace). La
[matriz completa 350 × 350](../outputs/pilot_controlled_verified/passenger_reachability.csv)
identifica cada par, y [connectivity.json](../outputs/pilot_controlled_verified/connectivity.json)
conserva componentes, incidencias y conteos por origen. Estar en una misma
componente débil no implica poder recorrer ambos sentidos.

## Atributos incompletos, geometría y semáforos

Hay 138 enlaces con carriles predeterminados y 137 con velocidad predeterminada;
162 tienen al menos uno de esos campos. De ellos, 118 aparecían en las rutas
aleatorias anteriores y ocho aparecen en la demanda controlada. El
[inventario completo](../outputs/pilot_controlled_verified/edge_attribute_audit.csv)
incluye los 350 enlaces, valores OSM, valores SUMO y usos por rutas.

La prioridad inmediata sobre las rutas nuevas es:

| Enlace | Calle/clase | Campos predeterminados | Carriles SUMO | Velocidad SUMO | Viajes que lo usan |
|---|---|---|---:|---:|---:|
| `-1535710422` | rampa `primary_link` sin nombre | carriles, velocidad | 1 | 22,22 m/s ≈ 80 km/h | 15 |
| `141594579#0` | rampa `primary_link` sin nombre | carriles, velocidad | 1 | 22,22 m/s ≈ 80 km/h | 15 |
| `141594579#1` | rampa `primary_link` sin nombre | carriles, velocidad | 1 | 22,22 m/s ≈ 80 km/h | 15 |
| `198404004#0` | 45 Avenida Sur | velocidad | 2 | 13,89 m/s ≈ 50 km/h | 15 |
| `198404004#1` | 45 Avenida Sur | velocidad | 2 | 13,89 m/s ≈ 50 km/h | 15 |
| `37785370` | Calle el Progreso | carriles, velocidad | 1 | 22,22 m/s ≈ 80 km/h | 15 |
| `565967882#0` | 33 Avenida Sur | velocidad | 2 | 22,22 m/s ≈ 80 km/h | 30 |
| `565967882#1` | 33 Avenida Sur | velocidad | 2 | 22,22 m/s ≈ 80 km/h | 30 |

Los seis valores cercanos a 80 km/h merecen revisión antes de calibrar un
corredor urbano. Son decisiones predeterminadas del convertidor ante etiquetas
ausentes; no son velocidades medidas ni límites legales verificados. Tampoco
la existencia de una etiqueta OSM convierte un valor en una medición validada.
Sin evidencia adicional no se sustituyeron por velocidades elegidas a mano.

Se conservaron y clasificaron las 25 líneas del registro de advertencias
heredado, incluido el resumen de 18 reducciones de velocidad por curvatura:

| Hallazgo | Evaluación y decisión |
|---|---|
| Tipo `bus`, cauce y paradas/líneas de transporte público incompletas | Consistentes con filtrado modal y recorte. No se implementa aquí un escenario de transporte público. |
| Radio de 8,96 m en `198404927` | Geometría que requiere inspección independiente; el aviso no prueba un error físico. |
| Desplazamientos de forma de 38,55 m y 26,32 m en `1538961972` y `1901675110` | Señalados en la figura de prioridades; no se corrigieron sin geometría de referencia. |
| Tres semáforos sin movimientos retenidos: `191997676`, `192024481`, `4337995469` | Netconvert no construye sus programas; se conserva la evidencia, sin crear movimientos ficticios. |
| Verde menor `37785370` → `1225540290#0`, velocidad superior a 19,44 m/s | Posible falta de carril de giro o velocidad inferida inadecuada; pendiente de verificación. |
| Reducciones de velocidad por radio de giro | Decisiones del convertidor para las conexiones, conservadas. |
| 57 enlaces externos de menos de 1 m | Sensibilidad de indicadores y segmentación; no se fusionaron ni borraron por su longitud. |

No se comprobó un error físico que justifique modificar la red. El
[diagnóstico de advertencias](../outputs/pilot_controlled_verified/inherited_warning_review.json)
mantiene el texto original y las referencias. Las cuatro bitácoras nuevas de
ruteo, validación de alternativas y simulación tienen cero advertencias y
errores; esto no elimina los problemas heredados. No se usaron opciones de
ignorar errores, reparar rutas ni desactivar advertencias.

Se inspeccionaron los 18 programas estáticos generados: ciclos de **90 s**, con
tres a seis fases. [signals.json](../outputs/pilot_controlled_verified/signals.json)
conserva estados, duraciones e índices de conexiones controladas. Son programas
virtuales, no ciclos reales. Cuatro nodos OSM con etiqueta semafórica no tienen
programa del mismo identificador: los tres avisados y `3990780933`, situado
fuera de la ventana y sin enlaces retenidos incidentes a ese nodo.

## Demanda sintética y movimientos explícitos

La [especificación](../scenarios/pilot_controlled/demand.json) define seis
movimientos. Los identificadores de origen y destino son enlaces SUMO
dirigidos; norte/sur/este/oeste describen entradas y salidas del experimento.

| Movimiento | Trayecto | Origen | Destino | Tasa (veh/h) | Primera salida (s) | Solicitudes |
|---|---|---|---|---:|---:|---:|
| W_E | Roosevelt oeste → este | `198404000` | `1225540290#2` | 180 | 0 | 45 |
| E_W | Roosevelt este → oeste | `1255704511#0` | `54144834` | 180 | 10 | 45 |
| N_W | 33 Avenida norte → Roosevelt oeste | `24556748#0` | `54144834` | 60 | 5 | 15 |
| E_N | Roosevelt este → Héroes norte | `1255704511#0` | `179733827#1` | 60 | 15 | 15 |
| N_E | Juan Pablo II desde el este → Roosevelt este | `141164180#0` | `1225540290#2` | 60 | 20 | 15 |
| W_S | Roosevelt oeste → 45 Avenida Sur | `198404000` | `198404004#1` | 60 | 25 | 15 |

Se generan llegadas periódicas `inicio + k × 3600/tasa`, estrictamente antes
de 900 s, sin remuestreo ni sustitución de solicitudes. Suman 600 veh/h durante
15 minutos: 150 solicitudes. Los flujos de 180 veh/h tienen intervalo de 20 s;
los de 60 veh/h, de 60 s. La semilla 42 fija la aleatoriedad del simulador;
las horas de llegada se construyen de forma determinista.

Se usa `passenger`, `speedFactor=1.0`, `speedDev=0`, `departLane=best` y
`departSpeed=0`. Son supuestos uniformes de conducción; los demás parámetros
se heredan de SUMO 1.28.0. El paso es 1 s, horizonte 1800 s y agregación 60 s.
`duarouter` usa un hilo, ruteo estricto y OD fijos. Todas las solicitudes
preservan identificador, origen, destino y hora; cada secuencia tiene movimientos
permitidos. No hubo rechazos que justificar individualmente.

Las secuencias completas y las conexiones por carril están en
[controlled_movements.json](../outputs/pilot_controlled_verified/controlled_movements.json),
y las 150 horas en [arrival_schedule.json](../outputs/pilot_controlled_verified/arrival_schedule.json).

## Resultados, indicadores y repetición

| Indicador | Base | Repetición |
|---|---:|---:|
| Solicitados / aceptados / insertados / completados | 150 / 150 / 150 / 150 | 150 / 150 / 150 / 150 |
| Rechazados / pendientes / eliminados | 0 / 0 / 0 | 0 / 0 / 0 |
| Duración media del viaje | 132,90 s | 132,90 s |
| `timeLoss` medio | 51,01 s | 51,01 s |
| Tiempo detenido medio (`waitingTime`) | 32,39 s | 32,39 s |
| Demora media de salida | 0,00 s | 0,00 s |
| Longitud media recorrida | 1333,84 m | 1333,84 m |
| Teletransportes / colisiones | 0 / 0 | 0 / 0 |
| Frenadas / paradas de emergencia | 0 / 0 | 0 / 0 |
| Máximo simultáneo en red / detenido | 25 / 13 veh | 25 / 13 veh |

El último viaje llega en el segundo 1035. Se conserva la ventana completa
hasta 1800 s, incluyendo el vaciado. En cada paso se comprobó el balance entre
vehículos insertados, presentes y terminados. El
[resumen](../outputs/pilot_controlled_verified/summary.json) incluye estadísticas
por movimiento; N_W y N_E muestran medias de `timeLoss` de 111,51 s y 104,67 s,
respectivamente. Son resultados de esta configuración sintética, no una
estimación del retraso real.

![Series temporales y resultados por movimiento](../outputs/pilot_controlled_verified/visual/traffic_indicators.png)

Hay **10 500 registros enlace-intervalo**: 350 enlaces externos por 30 períodos
de 60 s, incluyendo vacíos, sin enlaces internos y con agregación temporal
`trackVehicles=false`. Se conservan XML y
[CSV de indicadores](../outputs/pilot_controlled_verified/base/edge_indicators.csv):

| Campo | Unidad e interpretación |
|---|---|
| `entered`, `left` | Vehículos que cruzan las fronteras del enlace durante el intervalo. |
| `flow_in_veh_h`, `flow_out_veh_h` | `3600 × conteo / duración_del_intervalo`; tasas en veh/h. |
| `departed`, `arrived` | Inicios/finales de viajes dentro del enlace, separados de los cruces de frontera. |
| `mean_vehicles` | `sampledSeconds / duración_del_intervalo`, promedio temporal de vehículos presentes, en veh. |
| `occupancy_pct` | Ocupación porcentual nativa de SUMO, agregada sobre el enlace. |
| `density_veh_km`, `speed_m_s` | Densidad y velocidad reportadas por SUMO. Velocidad ausente queda vacía, no se inventa cero. |
| `waiting_time_vehicle_s`, `time_loss_vehicle_s` | Tiempos acumulados de vehículos en el enlace e intervalo, en veh·s. |

Las definiciones nativas se contrastaron con la
[documentación de salidas por enlace de SUMO](https://sumo.dlr.de/docs/Simulation/Output/Lane-_or_Edge-based_Traffic_Measures.html).
En [TripInfo](https://sumo.dlr.de/docs/Simulation/Output/TripInfo.html),
`waitingTime` mide tiempo a velocidad menor o igual al umbral de detención de
SUMO (por defecto 0,1 m/s), sin paradas programadas. `timeLoss` expresa pérdida
frente a la velocidad ideal del vehículo. Esas dos medidas se solapan y no
deben sumarse como causas independientes de duración.

El máximo de `mean_vehicles` por enlace-intervalo es 2,4692 veh; la ocupación
nativa máxima es 96,67 %. Los enlaces muy cortos hacen especialmente sensible
la interpretación de ese porcentaje. Se conserva y visualiza el valor completo,
sin recortarlo para mejorar su apariencia. La
[figura de ocupación](../outputs/pilot_controlled_verified/visual/edge_occupancy.png)
usa escala logarítmica y muestra el máximo de cada enlace entre los intervalos.

De acuerdo con **GDM-MATH-001 v1.0**, el número de vehículos detenidos de toda
la red no es una cola física única `Q_t`; el promedio temporal por enlace
tampoco constituye el estado de celda `n_{i,t}` de un CTM. Para acumulación
total se usa `running` de la serie de red, que incluye vehículos en conexiones
internas. No se suman ocupaciones porcentuales de enlaces ni se equiparan
estados simulados con observaciones o estimaciones CTM/LTM.

La [comparación de repetición](../outputs/pilot_controlled_verified/reproducibility.json)
confirma igualdad de métricas, **todos los atributos por vehículo** de
`tripinfo`, atributos de todos los intervalos de enlaces, configuraciones y
todos los pasos de `summary`, excluyendo únicamente su tiempo de CPU.
Fechas y rutas de archivos en comentarios XML no son indicadores de tráfico.

## Dos candidatos para un cierre posterior

![Alternativas topológicas, sin ejecutar cierres](../outputs/pilot_controlled_verified/visual/closure_candidates.png)

| Prioridad | Enlace dirigido | Longitud | Exposición en esta base | Alternativa ilustrada |
|---|---|---:|---|---|
| 1 | `1257993561#5`, Roosevelt hacia el este | 67,81 m | W_E: 45 viajes | 35 Avenida Sur (`-175606174`) → Calle el Progreso (`-198404021`), retorno a `1225540290#0`. |
| 2 | `54144826#5`, Roosevelt hacia el oeste | 84,48 m | E_W, N_W y E_N: 75 viajes | Baden Powell (`175606172#1`, `#2`) → 1a Calle Poniente (`24562307#2`) → 41 Avenida Norte (`-262426697#0`), retorno a `54144826#7`. |

Ambos tienen etiquetas OSM de dos carriles, `maxspeed=60` y sentido único.
Son segmentos dirigidos de SUMO, no toda una vía OSM ni ambas calzadas.
Para cada candidato se consultó el grafo excluyendo ese enlace: **los seis OD
conservan una alternativa**. Las doce secuencias se comprobaron además con
`duarouter --skip-new-routes true` en la red abierta, sin reparación ni
reoptimización, preservando todas las secuencias propuestas. Ver
[closure_candidates.json](../outputs/pilot_controlled_verified/closure_candidates.json)
y [alternative_validation.json](../outputs/pilot_controlled_verified/alternative_validation.json).

El costo usado para buscar alternativas es suma de longitud/velocidad de
enlaces externos; omite tiempos internos, fases y congestión. **No predice
demoras de desvío** ni demuestra capacidad suficiente. La figura muestra W_E
y E_W como ejemplos; las otras alternativas están en el JSON. Ningún enlace
se deshabilitó en la red y no se ejecutaron esas alternativas en SUMO.

Se recomienda empezar por `1257993561#5`, por afectar una sola corriente y
facilitar la interpretación. Antes de ejecutar ese experimento habrá que
declarar la reasignación de rutas y conservar OD, identificadores, vehículos,
salidas, semilla, paso, horizonte, atributos, señales y fronteras. Se deben
comparar también rechazos y pendientes, sin reducir la demanda cuando se
interrumpa una ruta. La demanda controlada tiene otros OD y supuestos de
conducción que la aleatoria; sus medias no prueban una mejora frente a la 002.

## Reproducibilidad, regresión e integridad

Comando único desde la raíz de `DigitalTwins`, usando un directorio nuevo:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.controlled --output outputs/pilot_controlled_reproduction
```

Requiere Python 3.11+, SUMO 1.28.0 y los paquetes de visualización ya presentes
(Matplotlib 3.10.3, PyProj 3.7.2, NumPy 1.26.4). No instala dependencias ni
descarga datos. Reutiliza la base PROJ fijada y desactiva red PROJ. Cada
ejecución nueva verifica las referencias protegidas y el índice nacional,
genera diagnóstico y demanda, ejecuta ambas corridas y dibuja las seis figuras.

Se volvió a ejecutar íntegramente el piloto aleatorio anterior —recorte,
conversión, restricciones, ruteo y dos simulaciones— en
`outputs/intervention003/regression002/`. Reprodujo **109 rutas y viajes
completados de 150 solicitudes**, los 41 rechazos esperados, los atributos de
todos los vehículos y el contenido semántico de la red. La
[comparación](../outputs/intervention003/regression_comparison.json) registra
igualdad con las evidencias protegidas y entre sus dos corridas. El código
`pilot.py` y la configuración anterior se conservan sin cambios.

Las 15 pruebas focales cubren restricciones, rechazos, direcciones, permisos,
tasas y unidades, determinismo, consultas de alternativas y balances de
vehículos. Comando y [registro](../outputs/intervention003/tests.log):

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

El inventario de protección compara SHA-256 y tamaño de los **2374 archivos
preexistentes protegidos**, incluidos resultados anteriores, auditorías,
documentos conceptuales y contrato matemático. Las fuentes OSM se verifican
por separado contra su manifiesto. El control de repositorios vecinos compara
rutas/tamaños/fechas de sus árboles de trabajo excluyendo entornos, cachés y
dependencias; además compara el estado Git disponible. Estos controles y
su alcance se detallan en la
[validación final](../outputs/intervention003/final_validation.json). No se
modificaron fuentes originales ni evidencias verificadas.

## Archivos y cambios de comportamiento

| Tipo | Archivos | Propósito |
|---|---|---|
| Nuevos | `src/digitaltwins/controlled.py`, `diagnostics.py`, `plots.py` | Demanda, ejecución doble, grafos passenger, auditoría, métricas y figuras. |
| Nuevos | `scenarios/pilot_controlled/demand.json`, `README.md` | Tasas, OD, supuestos y receta. |
| Nuevos | `tests/test_controlled.py`, este informe | Ocho pruebas adicionales y evidencia interpretada. |
| Modificados | `README.md`, `tests/README.md`, `pyproject.toml` | Instrucciones actuales y declaración opcional de Matplotlib/PyProj; sin instalación. |
| Generados | `outputs/pilot_controlled_verified/`, `outputs/intervention003/` | Resultados canónicos, figuras, regresión, registros y comprobaciones. |
| Generados y conservados | `outputs/pilot_controlled/`, `outputs/pilot_controlled_v1/` | Ensayo preliminar y tentativa fallida, separados del resultado canónico. |
| Eliminados | Ningún archivo de código, dato original o evidencia previa | Solo se limpiaron temporales propios de pruebas. |

La primera tentativa de validación de alternativas permitió que `duarouter`
recalculase rutas dadas. La comprobación detectó secuencias distintas y detuvo
esa ejecución antes de simular. Se corrigió invocando `--skip-new-routes true`
para validar exactamente las propuestas; no se relajó la validación. Se
conserva el registro fallido en `pilot_controlled_v1`. También se corrigió una
anotación de figura y se aseguró la creación del directorio temporal de pruebas
en una copia limpia. El [inventario de cambios](../outputs/intervention003/changes.json)
enumera los archivos entregados.

El comportamiento nuevo procede de los seis OD y llegadas periódicas, del tipo
de conductor declarado y del registro agregado adicional. No sustituye la
demanda aleatoria anterior ni altera su código, red o resultados. No hay
instalaciones globales, servicios, accesos reales, operaciones Git de publicación
ni infraestructura adicional.

## Limitaciones pendientes

La GUI sigue indisponible. Geometría fina, radios, enlaces diminutos, carriles
de giro, velocidades incompletas y capacidad de desvíos requieren evidencia
independiente antes de cualquier validación física. Las componentes menores
permanecen aisladas en este recorte; todos los OD experimentales están en la
principal. El vaciado sin pendientes solo demuestra viabilidad de esta carga
de 150 vehículos.

No hay conteos, Waze ni registros semafóricos reales, ni calibración de fases,
conductores o capacidad. No se implementaron CTM, LTM, GNN, estimación ni
dashboard. Los CSV son agregados sintéticos útiles para futuros estudios; la
equivalencia de entradas, salidas y supuestos macro/microscópicos aún deberá
definirse. La conservación y repetición verificadas permiten una comparación
posterior dentro de estos supuestos, con las limitaciones explícitas.

Datos derivados: **© OpenStreetMap contributors**, procesados por Geofabrik,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Se conserva
`ATTRIBUTION.txt` con los resultados.
