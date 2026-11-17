# Flujo real OSM–SUMO de DigitalTwins

Este laboratorio representa el corredor de Alameda Franklin Delano Roosevelt,
San Salvador, con cartografía local y viajes sintéticos. El
[visor](../outputs/visualization/index.html) reproduce resultados guardados;
no ejecuta SUMO al abrirse. Las [fichas SIM-002 a SIM-005](simulations/README.md)
explican las preguntas y configuraciones de cada experimento.

~~~mermaid
flowchart LR
  A["PBF OSM / Geofabrik<br/>corte 14 oct 2026"] --> B["Osmium<br/>extracto y restricciones"]
  B --> C["netconvert<br/>red dirigida y señales virtuales"]
  C --> D["Demanda sintética + duarouter<br/>OD, rutas y salidas"]
  D --> E["SUMO 1.28.0<br/>base / cierre aislado"]
  E --> F["tripinfo · summary<br/>edgeData · rutas · FCD · TLS"]
  F --> G["Validación y manifiestos<br/>comparación de pares"]
  G --> H["Visor HTML y fichas"]
~~~

El diagrama no implica que todos los experimentos tengan todas las salidas:
solo SIM-005 conserva FCD y señales por segundo. Las demás fichas usan sus
rutas, indicadores y figuras originales.

## Procedencia de la cartografía

La entrada efectiva es **el-salvador-261014.osm.pbf**, corte
2026-10-14T20:21:12Z, procesado por Geofabrik y adquirido previamente el
15 de octubre. Su procedencia, licencia, tamaño, ruta y recibo están en
[data/osm/sources.json](../data/osm/sources.json). Su ruta de solo lectura,
relativa a DC_X, es:

    savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/el-salvador-261014.osm.pbf
    SHA-256: 73369769b9a7f45dd9f0b3a44511da0c29101c7268805b9c9f415114a6c27672

La fuente declarada es Geofabrik para El Salvador; atribución
**© OpenStreetMap contributors**, licencia ODbL 1.0. No se descargó cartografía
durante la intervención 006. El SQLite de octubre es diagnóstico; el GeoPackage
de agosto es referencia cartográfica. No se mezclan sus IDs para construir la
red, ni se usa el SQLite como sustituto del PBF para las restricciones de giro.

## Extracción y conversión ejecutadas

[commands.json de SIM-002](../outputs/pilot_verified/commands.json) registra
los argumentos, versiones, códigos de retorno y logs originales. Estos son
sus pasos principales con nombres de salida abreviados; son explicativos,
no deben ejecutarse sobre los resultados verificados:

~~~sh
osmium extract --bbox=-89.216,13.699,-89.207,13.705 \
  --strategy=smart -S types=restriction \
  el-salvador-261014.osm.pbf -o pilot.osm.pbf
osmium cat pilot.osm.pbf -o pilot.osm.xml
osmium check-refs pilot.osm.pbf
netconvert --osm-files pilot.osm.xml \
  --keep-edges.by-vclass passenger \
  --osm.turn-lanes true --osm.annotate-defaults true \
  --output.original-names true --output-file pilot.net.xml \
  --error-log netconvert.errors.log
~~~

Se usó Osmium 1.19.1 y SUMO/netconvert 1.28.0. La estrategia smart conserva vías
completas y las relaciones de restricción solicitadas; por ello la red puede
rebasar el rectángulo de selección. La auditoría de giros original revisa once
restricciones, separa desconexión de falta de camino dirigido y no confunde
una conversión exitosa con geometría físicamente validada.

La red tiene **350 enlaces y 604 carriles externos**, además de conexiones
internas; contiene tres componentes débiles de 321, 21 y 8 enlaces. SIM-003
diagnosticó sus limitaciones y conservó los mismos bytes para no introducir
correcciones geométricas sin evidencia. SIM-004 y SIM-005 usan esa misma red:

    SHA-256: 5ffebc98d865aa238703cc39463d4a34128e83390e6a4b24611a9e280b6fe4d5

La geometría del visor procede de
[controlled.net.xml](../outputs/closure_sensitivity/common/controlled.net.xml).
Los nombres y marcas de atributos predeterminados proceden de
[edge_attribute_audit.json](../outputs/pilot_controlled_verified/edge_attribute_audit.json).
Hay 138 enlaces con carriles predeterminados y 137 con velocidad
predeterminada. No son conteos de carriles o mediciones de velocidad reales.

## Representación de la red

| Elemento | Ejemplo y uso |
|---|---|
| edge externo | Enlace dirigido 1257993561#5, Roosevelt hacia el este. Un ID OSM puede dividirse en varios enlaces SUMO. El signo y sufijo forman parte del ID. |
| lane | Carril con longitud, velocidad, permisos y polilínea. FCD y geometría comparten el mismo sistema métrico local. |
| junction | Nodo de unión, prioridad o intersección; no identifica por sí solo una maniobra semaforizada. |
| connection | Maniobra permitida entre carriles; via identifica su carril interno. |
| tlLogic | Programa virtual con fases y estados. Cada carácter controla el linkIndex de una conexión con el mismo tl. |

La red emplea UTM zona 16 y desplazamiento
netOffset="-260204.62,-1515196.25". El visor no aplica una proyección nueva ni
consulta mapas: conserva los x/y locales y solo invierte Y para el eje
vertical de SVG, manteniendo el norte arriba. No se geocodifican vehículos
a partir de velocidades medias.

## Demanda, rutas y horarios

En SIM-002, randomTrips.py produjo 150 solicitudes entre 0 y 900 s, período
6 s, clase passenger, semilla 42. La validación aceptó 109 y rechazó 41;
los rechazos no se reemplazaron. Las 109 rutas válidas se completaron.
Esta selección aleatoria demuestra funcionamiento técnico y expone las
limitaciones del ruteo en el extracto.

SIM-003 introdujo
[demand.json](../scenarios/pilot_controlled/demand.json):
45 viajes W_E, 45 E_W y 15 para cada uno de N_W, E_N, N_E y W_S.
Las tasas nominales suman 600 veh/h durante 900 s. Las salidas son periódicas,
con distintos inicios por movimiento. duarouter valida OD fijos, con un hilo,
sin reparar silenciosamente una alternativa ni sustituir solicitudes.
El vehículo controlled_passenger fija speedFactor=1.0 y speedDev=0;
los demás parámetros de conducción mantienen los supuestos declarados de SUMO.
No hay calibración de conductores ni demanda medida.

SIM-004 conserva los mismos IDs, horarios, OD, tipos y rutas iniciales. En el
escenario intervenido, closingReroute añade la prohibición passenger al enlace
**1257993561#5 durante [0,1800) s**, preservando las clases ya prohibidas.
El rerouter se activa desde 198404000, antes de las bifurcaciones; el modo de
ruteo 8 se aplica solo al cierre. Se verifican permisos efectivos durante la
corrida. La geometría no se modifica.

Los 45 W_E ejecutan el desvío por **35 Avenida Sur (-175606174) → Calle el
Progreso (-198404021) → 1225540290#0**. Las rutas ejecutadas, separadas de
propuestas reemplazadas, confirman que evitan el enlace cerrado. Evitar
también sus enlaces vecinos no significa que estos se hayan cerrado.
El desvío añade 105,55 m a cada W_E.

SIM-005 conserva esos pares y perturba solo condiciones temporales: calendario
original y cuatro calendarios de jitter entero ±15 s con semillas 101–104,
respetando orden por movimiento, IDs y ventana de salida anterior a 900 s.
Cada uno se combina con desfases adicionales de 0, 30 y 60 s: 15 pares.
Se conserva semilla SUMO 42 y se repite J101/30. Las perturbaciones no son
observaciones de variabilidad poblacional ni réplicas estadísticas independientes.

## Semáforos virtuales y estados efectivos

La importación genera **18 programas estáticos, ciclos de 90 s**. Las
etiquetas OSM ayudan a definir la red, pero no aportan tiempos reales de
controladores. Las fases y prioridades son supuestos virtuales.
La auditoría de SIM-003 advierte casos que necesitan validación física.

En SIM-005 se carga un tlLogic adicional con el mismo ID y programID,
sin redefinir fases, cambiando el offset original módulo 90. El registro
nativo por segundo comprueba que el desfase se aplicó realmente; no basta con
leer un atributo de configuración.

El visor usa las 84 conexiones con tl y linkIndex, y dibuja su geometría via.
Busca la fase registrada en ese segundo y toma el carácter correcto de su
vector: G/g verde (prioridad distinta), y amarillo, r rojo.
El tooltip conserva ID, índice y estado. Los registros iguales para un mismo
offset se deduplican; los cambios de fase se comprimen sin pérdida. No se
deduce el color a partir de la posición de un vehículo ni del ID de un nodo.
Estos colores son **estados simulados**, no estados de semáforos reales.

## Ejecución y salidas

Cada experimento usa horizonte 0–1800 s, paso 1 s y entradas registradas en su
manifiesto; las salidas se escriben en un directorio nuevo. SUMO trabaja de
forma local y aislada. TraCI, cuando se usa para auditar permisos, opera sobre
el proceso SUMO mediante un socket local temporal.

| Salida | Qué se consulta y qué unidad tiene |
|---|---|
| tripinfo.xml | Viajes completos, duración y demora de salida (s), waitingTime (s), timeLoss (s), longitud (m). Pendientes contabilizados aparte. |
| summary.xml | Vehículos activos, insertados, finalizados y pendientes por paso. running incluye vehículos en conexiones internas. |
| fcd.xml.gz | Posición nativa x/y (m locales), carril y velocidad (m/s) por vehículo y segundo. Solo SIM-005 la conserva. |
| tls_states.xml.gz | Tiempo, ID, programa, fase y vector de estados nativos por segundo. Solo SIM-005. |
| edgeData / CSV | Intervalos de 60 s, sin enlaces internos, incluyendo vacíos; conteos de entrada/salida, ocupación y presencia. |
| Historiales de rutas | Rutas efectivamente ejecutadas y tiempos de salida de enlaces, separados de eventos de cambio de ruta. |

waitingTime mide tiempo detenido según el umbral de SUMO; timeLoss mide
pérdida frente a la velocidad ideal del vehículo. Se solapan y **no se suman**
como causas independientes. Una mayor longitud puede aumentar duración
mientras disminuye tiempo detenido. El visor muestra ambos indicadores
separados y la diferencia **cierre − base**.

El flujo se convierte con 3600 × entered / duración_del_intervalo, en
**veh/h**. En un intervalo de 60 s, dos entradas son 120 veh/h. Ese número es
una tasa equivalente del intervalo, no 120 vehículos observados.
mean_vehicles = sampledSeconds / duración_del_intervalo está en **veh**;
la ocupación nativa es un **porcentaje de espacio**. No se convierte porcentaje
en conteo. El máximo presentado es el máximo de las ocupaciones de intervalo,
no una ocupación instantánea. entered no incluye departed: un vehículo
puede iniciar dentro de un enlace. La suma de entradas de muchos enlaces
cuenta pasos y no equivale a viajes únicos.

No se equiparan vehículos presentes, vehículos detenidos, cola Q_t y estado
de celda n_i,t. Este trabajo no implementa CTM/LTM ni redefine
[GDM-MATH-001](GDM-MATH-001_v1.0.md).

## Naturaleza de la evidencia

| Clase | Evidencia actual | Límite |
|---|---|---|
| Cartografía de origen | Geometría, nombres y etiquetas OSM/Geofabrik de octubre. | No demuestra capacidad, demanda ni operación física actual. |
| Atributos inferidos | Carriles/velocidades predeterminados, conexiones, prioridades y geometría derivada por netconvert. | Marcas visibles por enlace; necesitan contraste de campo. |
| Parámetros y estados sintéticos | OD, horarios, tipos, cierre, offsets; posiciones, flujos y señales simulados. | Permiten contrafactuales condicionados a esos supuestos. |
| Observaciones reales | No hay conteos vehiculares, Waze ni registros reales de controladores integrados. | No hay calibración o validación operacional. |
| Estimaciones | No hay estimador de estados integrado. | La simulación no se presenta como reconstrucción del estado real. |

## Regeneración y comprobaciones

Con los resultados locales disponibles, desde la raíz del repositorio:

~~~sh
PYTHONPATH=src python3 -B -m digitaltwins.visualization
~~~

El comando usa solo la biblioteca estándar Python, comprueba los hashes de
los cuatro manifiestos, contrasta métricas con tripinfo, verifica cobertura
temporal y mapeos de señales, genera fichas y empaqueta el HTML. Se puede
repetir sobre su propio directorio outputs/visualization/; rechaza carpetas
existentes que no sean un paquete propio. No vuelve a simular.

Abrir outputs/visualization/index.html con doble clic. No se requiere servidor,
conexión, CDN ni mapas externos. El HTML contiene solo cuatro FCD seleccionados
(Original/0 y J103/0, base y cierre) a resolución completa de 1 s. Los otros
13 pares aportan agregados y señales, con ausencia de posiciones explícita.
Los 32 FCD y 32 logs de señales originales permanecen intactos.

Las recetas completas están en cada [ficha](simulations/README.md);
requieren herramientas e insumos originales y escriben en salidas nuevas.
Las comprobaciones de la 006 reutilizan las repeticiones verificadas
anteriores, sus hashes, entradas, código y pruebas; no ejecutan una nueva
repetición SUMO.

Las pruebas técnicas y balances comprueban coherencia y repetibilidad, no
verdad física. Persisten componentes desconectados, velocidades/carriles
inferidos, formas dudosas y programas virtuales pendientes de contraste.
Los 15 diseños muestran sensibilidad temporal del experimento; no justifican
una política de cierre real, una afirmación de saturación ni un efecto causal
medido en San Salvador.
