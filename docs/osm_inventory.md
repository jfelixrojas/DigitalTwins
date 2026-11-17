# Inventario OSM y preparación mínima de DigitalTwins

Intervención 001 · fecha de referencia: **2026-11-16, America/Bogota**.
Raíz inspeccionada: `/Users/josefelix/Desktop/DC_X`.

**Hay datos locales suficientes para preparar un primer escenario SUMO de El
Salvador sin descargar otra red.** La entrada recomendada es el PBF Geofabrik
del 14 de octubre de 2026, acompañado de recibo, hash y metadatos. El bloqueo
actual es la ausencia de SUMO y de una herramienta de conversión PBF a XML.
La suficiencia es para una prueba técnica con supuestos; no acredita fidelidad
del tráfico ni disponibilidad de demanda y programación semafórica observadas.

## Alcance y método

Se recorrieron `savia-x-b1`, `savia-x-lab`, `x_red_social` y `DigitalTwins`,
incluidos datos ignorados por Git. Se excluyeron dependencias, entornos
virtuales, `.git`, cachés, `site-packages`, `Python.framework`, compilación y
distribuciones. Se buscaron formatos geográficos, bases SQLite, archivos
comprimidos y referencias en Python, shell, SQL, JSON y documentación.
Los entornos históricos solo se revisaron por metadatos de paquetes.

Las bases se abrieron con `mode=ro&immutable=1`, `query_only=ON` y sin cargar
extensiones. Se consultaron esquemas, conteos, extensiones y etiquetas; no se
volcaron geometrías completas. Los Parquet se inspeccionaron con PyArrow y,
cuando fue necesario, WKB con Shapely. Los GeoJSON se resumieron por tipos,
conteos, propiedades y límites. El PBF se leyó por bloques mediante las
funciones de lectura del parser local de B1, con Python `-B`; no se llamó a
su constructor de índices ni a su CLI. El paquete nuevo no depende de B1.

Se verificaron SHA-256 de los cuatro recursos principales y del miembro GPKG
del ZIP sin extraerlo. Los metadatos medidos de los recursos están en
`outputs/intervention001/local_resource_audit.json`; los cuatro originales
fijados, en `data/osm/sources.json`. Los límites son `[oeste,sur,este,norte]`,
longitud/latitud; no son certificaciones de frontera ni de completitud nacional.

Se leyeron `docs/concept.md` y los dos documentos Word existentes. Estos
establecen observación de solo lectura, laboratorio aislado, separación entre
datos observados e inferidos, CTM inicial, comparación LTM y contrato
GDM-MATH-001 v1.0. No se encontró un archivo independiente con el contrato
matemático completo; los Word contienen sus invariantes. No se alteraron.

## A. Datos originales y derivados prioritarios

Tamaños en MB decimales. Cada ruta corresponde al original, conservado en su
ubicación. Los archivos de DigitalTwins solo los referencian.

| Recurso y ruta absoluta | Tipo y tamaño | Cobertura y fecha comprobadas | Utilidad, SUMO y trabajo pendiente |
| --- | --- | --- | --- |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/el-salvador-261014.osm.pbf` | OSM original binario, 35,17 MB | Extracto Geofabrik SV; cabecera y recibo; datos a 2026-10-14 20:21:12 UTC | **Entrada preferida**. Conserva nodos, vías, etiquetas y relaciones; recortar localmente y convertir a XML antes de `netconvert`. Revisar atributos y restricciones del corredor. ODbL 1.0. |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/topology-osm-v1.sqlite` | Índice derivado SQLite, 127,84 MB; `G_OSM_PBF_TOPOLOGY_V1` | Deriva solo del PBF de octubre; 109.633 vías y 1.155.786 nodos seleccionados | Consulta de nombres, nodos ordenados, geometría y etiquetas. No es una red SUMO; no almacena las relaciones de giro ni etiquetas de nodos. No usar sus componentes como prueba de rutas legales. ODbL 1.0. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/source/el-salvador.gpkg` | Derivado Geofabrik GeoPackage, 196,19 MB; 20 capas | README del ZIP: datos a 2026-08-23 20:21:36 UTC; CRS84, `srs_id=100000`; 119.975 objetos en `gis_osm_roads_free` | Referencia cartográfica, nombres, tipos, sentidos y velocidades parciales. Carece de IDs de nodos y relaciones; no hay campo de carriles. Requiere exportación y reconstrucción topológica para SUMO: mayor pérdida y esfuerzo que el PBF. ODbL 1.0. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/source/el-salvador-260823-free.gpkg.zip` | Distribución original ZIP, 89,48 MB; README y GPKG | Mismo corte de agosto; el GPKG interno tiene el mismo SHA-256 que el extraído | Evidencia de procedencia y licencia, no otra red. No volver a extraer ni duplicar. ODbL 1.0. |

La cabecera PBF declara `[-90.500910,12.035980,-87.584382,14.457621]` y URL de
replicación `central-america/el-salvador-updates`, secuencia 2074, escritor
`osmium/1.16.0`. Los nodos viales efectivamente indexados alcanzan
`[-90.1963443,13.1567127,-87.5611159,14.4653944]`. La extensión declarada no es
una envolvente estricta de todos los miembros de vías: no se deben descartar
nodos solo por excederla. La capa vial GPKG tiene esa misma envolvente numérica,
lo que **no demuestra igualdad entre cortes**. La selección de país está
respaldada por metadatos y por vías identificadas en San Salvador, no solo por
los nombres de archivo.

### Integridad, procedencia y duplicaciones

| Recurso | SHA-256 verificado en esta intervención |
| --- | --- |
| PBF octubre | `73369769b9a7f45dd9f0b3a44511da0c29101c7268805b9c9f415114a6c27672` |
| Índice topológico | `eb543319cc6d44e8eb84ba44b63c92eeb0fa715f1653daab3cba3e72e03a2aed` |
| GPKG agosto, tanto suelto como dentro del ZIP | `6ad7bcc0d2b8801e9f00871108d3953feff8fabcce71288b8c0e10ea25fe45f8` |
| ZIP agosto | `dbe3f2a8dc6a895dedd7d61b6f5bee6a3a6a1c42377d56c3b0ff22b7feb47ea9` |

El recibo local registra adquisición del PBF el 15 de octubre, MD5 oficial
`1adad8bfa40ade9defdd150c6659af54` y origen Geofabrik. Su estado inicial
`HEADER_PARSE_PENDING` queda completado por los metadatos posteriores; no es
un fallo vigente. Los documentos históricos distinguen explícitamente agosto
y octubre. No se hizo una comparación objeto por objeto de ambos cortes ni
una unión por `osm_id`. Las diferencias de conteo también reflejan filtros de
clase y segmentación del exportador; no se interpretan como altas/bajas viales.

No se encontraron otras versiones completas del PBF ni redes `.net.xml`.
Las copias de código y manifiestos en directorios históricos de laboratorio
son evidencia de versiones, no nuevas adquisiciones de datos.

### Atributos que realmente están disponibles

Conteos actuales sobre las **109.633 vías seleccionadas** del SQLite, con
clases de circulación motorizada incluyendo `service`, `track` y
`living_street`; no equivalen a todas las vías del PBF ni a aristas SUMO:

| Propiedad | Evidencia medida | Consecuencia para el piloto |
| --- | --- | --- |
| Topología | 1.311.688 membresías ordenadas; 1.155.786 nodos; cero referencias ausentes en las vías seleccionadas según el índice y su informe | Base sólida de conectividad por ID. El PBF conserva además objetos no incluidos en ese filtro. Validar conectividad del recorte y sus bordes. |
| Intersecciones | 134.292 nodos compartidos y 175.530 pares compatibles según metadatos; 3.434 pares excluidos por nivel y 2.264 componentes no dirigidos | Son resultados del criterio conservador del índice, no movimientos permitidos ni componentes dirigidos de una red de tráfico. La auditoría confirmó tablas y conteos de vías/nodos, sin recalcular todos esos pares. |
| Tipos de vía | `highway` en 109.633: 65.562 `residential`, 13.448 `service`, 10.412 `unclassified`, 5.370 `tertiary`, 5.048 `track`, entre otros | Seleccionar modos y accesos; no convertir automáticamente toda línea en calle utilizable por automóviles. |
| Sentidos | `oneway` en 12.237 (11,16 %): 9.168 `yes`, 3.054 `no`, 15 `reversible`; `junction` en 399 | La ausencia no acredita doble sentido. Revisar rotondas, excepciones de acceso y reversibilidad; defaults explícitos. |
| Carriles | `lanes` en 9.815 (8,95 %); `lanes:forward` y `lanes:backward` en una vía cada uno | Cobertura escasa. Hay un `lanes=0`; validar valores y reparto por sentido antes de usarlos. |
| Velocidades | `maxspeed` en 5.019 (4,58 %); sin `maxspeed:forward/backward` en este índice | No presuponer velocidades conocidas. Existen valores no escalares, por ejemplo `20, 30, 40`; depurar o registrar el default aplicado. |
| Giros | Lectura del PBF: **793 relaciones `type=restriction`**, todas con clave `restriction`; solo 6 vías con `turn:lanes` en el índice | Preservar relaciones durante el recorte. No están interpretadas ni almacenadas por el índice SQLite; no se acreditó que las 793 sean completas o válidas. |
| Accesos y niveles | `access` en 5.301, `motor_vehicle` en 437, `bridge` en 1.433, `tunnel` en 85 y `layer` en 1.644 | Revisar restricciones y separación de niveles. Un cruce geométrico no demuestra una conexión. |
| Semáforos | Lectura del PBF: **385 nodos `highway=traffic_signals`** | Presencia geográfica, sin garantía de fases, movimientos, ciclos ni tiempos reales. El índice pierde esas etiquetas de nodos. |

La lectura directa del PBF contó 777 bloques de datos, 809.396 vías y 4.223
relaciones. Se verificaron tipos de relación y etiquetas semafóricas, sin
construir una red ni certificar maniobras. El parser usado tiene SHA-256
`67171c46bb5b017d0bb89036cf2de827b7820d4dbb78bb1c4a9d1b046fe1561b`.

En el GPKG, `gis_osm_roads_free` contiene únicamente `fid`, `geom`, `osm_id`,
`code`, `fclass`, `name`, `ref`, `oneway`, `maxspeed`, `layer`, `bridge`, `tunnel`.
Sus sentidos están codificados como B/F/T (110.883/9.091/1), que requieren el
mapeo del exportador. Hay 114.996 valores `maxspeed=0`: tratarlos como falta de
velocidad informada, no imponer velocidad física cero. Carriles y restricciones
relacionales no se pueden reconstruir fielmente desde ese esquema solo.

## Otros datos geográficos y recursos descartados

El anexo al final registra todas las rutas, tamaños, conteos y extensiones
medidas de los archivos geográficos relevantes, incluidos los ignorados por Git.
Se agrupan aquí sus condiciones de reutilización.

- **Overture Transportation 2026-08-19.0**: 205.989 segmentos viales y 188.938
  conectores en Parquet. El recibo declara selección SV con margen nacional de
  250 m, CRS de intercambio longitud/latitud, preparación 2026-09-04. Los campos
  `connectors_json`, `access_restrictions_json`, `routes_json`, `sources_json`
  y WKB permiten estudiar conectividad. La materialización local no contiene
  campos de carriles o velocidades. Las entradas de procedencia incluyen OSM
  y TomTom; no son una corroboración independiente de OSM. Convertirlos a SUMO
  exige un adaptador y revisión de movimientos, por lo que no son la ruta corta.
  El manifiesto histórico declara CDLA-Permissive-2.0, en discrepancia con la
  [licencia ODbL del tema Transportation publicada por Overture](https://docs.overturemaps.org/attribution/).
  Registrar la discrepancia antes de adoptarlos; no se corrigen los originales.
- **Índices R56B/R56C**: nombres, corredores, pertenencias y cadenas
  administrativas derivados de OSM, Overture y jerarquías nominales locales.
  Son índices para geocodificación, no una red de simulación. R56C contiene
  7.502 corredores y 70.951 segmentos; `named_features` crece de 34.587 a
  34.907 respecto de R56B al incorporar 320 entidades administrativas. No son
  duplicados binarios. La tabla de conectores tiene 155.763 filas; el manifiesto
  conserva además un conteo de procedencia de 155.792, que no se sustituyó por
  el medido. Reconciliar licencia Overture y fuentes nominales sin licencia
  identificada antes de reutilizar o redistribuir el conjunto.
- **Overture Divisions 2026-09-23.1**: 287 puntos `division` y 288 áreas
  `division_area`, todos con `country=SV`, fuentes y metadatos GeoParquet.
  Sirven de contexto administrativo, no aportan aristas ni giros. El manifiesto
  registra ODbL y atribución a OSM, Overture y geoBoundaries CC BY 4.0; conserva
  una discrepancia Esri CC0/CC BY 4.0 que debe resolverse antes de republicar.
- **Overture Places 2026-09-23.1**: 61.099 puntos filtrados por bbox y país SV
  de la primera dirección. Captura 2026-10-04; puede omitir puntos sin país o
  con dirección errónea y no acredita completitud territorial. Complemento de
  lugares, no red vial. Mantener licencias por proveedor: CDLA-Permissive-2.0,
  Apache-2.0 y CC0-1.0, con NOTICE de Foursquare cuando corresponda. No es un
  dataset OSM puro ni contemporáneo del PBF o de Transportation.
- **GeoJSON R72/R73 e incidentes R56E**: geometrías asociadas a hipótesis de
  geocodificación y eventos; versiones declaradas 0.1.0/0.2.0. Se comprobó que
  las extensiones están en El Salvador, pero representan selecciones parciales,
  no una red nacional ni verdad de incidentes. No contienen topología nodal ni
  atributos suficientes para `netconvert`. Su uso ulterior requiere separar
  geometría OSM y contenido de eventos, verificar la procedencia y licencia
  de ambos y evitar tratar inferencias como observaciones.
- **Archivo nominal de 0 bytes**: `geography/el-salvador.gpkg` es un placeholder;
  el válido está en `geography/source/`. No usar el primero como entrada.
- **GPKG de 32 bytes** en `SYNTHETIC_INVALID_RESOURCE`: fixture deliberadamente
  inválida. Sin cobertura comprobable ni utilidad para una red real.

Duplicados GeoJSON verificados por SHA-256: los dos archivos R72OP_5 son
idénticos; R72OP_6, R72OP_6C y la copia R72OP_7/current de v0.1.0 son idénticos;
R72OP_6B y R72OP_7/current de UI v0.2.0 son idénticos. La UI añade presentación
manteniendo las geometrías de R72OP_6; no es una nueva fuente vial. R73ACQ_3 y
R73ACQ_5 tienen otros conteos y extensiones, sin equivalencia afirmada.

No se hallaron OSM XML, Shapefiles, GraphML ni redes SUMO existentes en el
alcance. No apareció una integración implementada con Overpass, OSMnx,
Pyrosm o SUMO en el código inspeccionado. Las referencias OSM operativas se
basan principalmente en extractos congelados y SQLite/Parquet.

## B. Código y procesos que se pueden aprovechar

Reutilización conceptual o adaptación posterior a DigitalTwins, con salidas
locales y revisión de licencia del código; no se copió código de SAVIA-X ni se
conectó su runtime. No se identificó una licencia general del código en las
raíces inspeccionadas. Una licencia de datos no concede por sí sola licencia
sobre los programas que los procesan.

| Ruta absoluta | Función existente | Uso potencial y límite |
| --- | --- | --- |
| `/Users/josefelix/Desktop/DC_X/savia-x-b1/extensions/g_topo_x68_v1/topology_pbf.py` | Parser PBF stdlib, índice de nodos/membresías/etiquetas y apertura inmutable | Se usaron únicamente lectores para auditar el PBF. Útil para comprobar nodos, grados y membresías; sus relaciones solo se cuentan. Su CLI crea SQLite: no ejecutarlo contra fuentes existentes. |
| `/Users/josefelix/Desktop/DC_X/savia-x-b1/extensions/g_topo_x68_v2/topology_provider.py` | Proveedor sobre el índice de octubre, agrupación y geometrías | Patrón de consulta por vía/nombre y preservación de alternativas. Depende de contratos B1 y rutas fijadas; no es un router SUMO. |
| `/Users/josefelix/Desktop/DC_X/savia-x-b1/src/savia_x_b1/blocks/geographic/reader.py` | Lectura estrecha de candidatos GPKG en modo inmutable | Patrón para extraer geometrías, CRS y atributos sin tocar el original. Depende de planes y contratos B1. |
| `/Users/josefelix/Desktop/DC_X/savia-x-b1/src/savia_x_b1/blocks/geographic/resources.py` | Fijación de hashes, recibos, licencia y exclusiones de recursos | Referencia para trazabilidad; ya detecta la discrepancia Overture y las limitaciones de fuentes nominales. |
| `/Users/josefelix/Desktop/DC_X/savia-x-b1/src/savia_x_b1/blocks/geographic/integral/roads.py` | Organización de candidatos por identidad vial, nivel y continuidad geométrica | Apoya selección de corredor; no acredita IDs de nodos, giros ni intersecciones en GPKG. |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-001/20261015-offline01/inspect_topology_readonly.py` | Inspección histórica de topología y limitaciones GPKG | Guía de auditoría; revisar sus rutas de salida antes de ejecutar. |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-referencias-osm-001/20261016-offline01/osm/osm_study_reader.py` | Diagnóstico de ambos cortes y geometrías de referencia | Consultas comparables manteniendo cada corte separado; no ejecutar reportes que escriban en el laboratorio. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/src/savia_x/operational/territorial_geocode_r56_sources.py` | Decodificación GPKG, límite nacional, consulta S3 y congelación Overture | Ideas de WKB/CRS y procedencia. Tiene `INSTALL httpfs/spatial`, acceso de red y escrituras: no se ejecutó y no se incorpora al flujo actual. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/src/savia_x/operational/territorial_geocode_r56c_sources.py` | Índices offline de corredores y conectores | Adaptable a selección por nombres; genera archivos y mezcla linajes, sin exportador SUMO. |

Documentación y configuraciones principales, con rutas originales:

- `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/ACQUISITION_RECEIPT.json`: origen, adquisición, tamaño, SHA-256, MD5 y atribución del PBF.
- `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/RESOURCE_SNAPSHOT_PBF.json`: cabecera, cobertura, fecha y límites de equivalencia.
- `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/RESOURCE_TOPOLOGY_INDEX.json`: versión, filtros y conteos del índice.
- `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/RESOURCE_BUNDLE_PBF.json`: vinculación del PBF, índice y transformador.
- `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/men-geographic-integral/20261015-offline01/RESOURCE_INVENTORY_C0.json`: auditoría de capas y limitaciones del GPKG.
- `/Users/josefelix/Desktop/DC_X/x_red_social/config/savia_x/operational/geography/source_manifest_v1.0.0.json`: fuente Geofabrik y corte de agosto.
- `/Users/josefelix/Desktop/DC_X/x_red_social/config/savia_x/operational/geography/territorial_geocode_source_manifest_v1.1.0.json`: fuentes combinadas R56 y discrepancia de licencia Transportation.
- `/Users/josefelix/Desktop/DC_X/x_red_social/config/savia_x/operational/geography/territorial_geocode_r56c_source_manifest_v1.0.0.json`: fecha, hashes y conteos declarados de los índices.
- `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/overture/2026-08-19.0/download_receipt.json`: S3, filtros, margen y hashes de Transportation.
- `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/b1_pilot_corpus/b1_public_only_geographic_resource_freeze_v0.1.0/resources/overture_divisions/overture_divisions_sv_resource_manifest_v0.1.0.json`: país SV, fuentes por propiedad, licencia y discrepancias.
- `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/b1_pilot_corpus/b1_public_only_geographic_resource_freeze_v0.1.0/resources/overture_places/overture_places_freeze_manifest_2026-09-23.1.json`: filtro de lugares, fecha, hash y licencias por proveedor.
- `/Users/josefelix/Desktop/DC_X/x_red_social/docs/F9_R56_TERR_GEOCODE_IMPLEMENTATION.md` y `/Users/josefelix/Desktop/DC_X/x_red_social/docs/F9_R56C_TERR_GEOCODE_RESOLVER.md`: uso anterior de las fuentes para geocodificación; no diseño de simulación.

## Atribución y condiciones de reutilización

Para el PBF, GPKG y sus derivados conservar **© OpenStreetMap contributors**,
procedencia **Geofabrik GmbH**, fecha y enlace a
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
La [página oficial de OSM](https://www.openstreetmap.org/copyright) describe
atribución y aviso de licencia. Al distribuir bases derivadas, conservar los
avisos y aplicar las condiciones ODbL de compartir y ofrecer acceso según el
tipo de publicación. Esta intervención prepara referencias locales, sin
redistribuir bases ni aplicar una licencia nueva al código del proyecto.

La evidencia local de agosto es el miembro `README` del ZIP; la de octubre
es la página Geofabrik retenida en
`/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/official/el-salvador.html`.
Para Overture conservar `sources`/`sources_json` y avisos por proveedor. No
extender CDLA, ODbL o una autorización de investigación a todo un recurso mixto
sin revisar sus componentes. Los eventos sociales y fixtures no se incorporan
como red ni como observaciones validadas.

## C. Diagnóstico del Mac

| Elemento | Resultado de la inspección |
| --- | --- |
| Sistema | macOS 26.7, arm64 |
| Git | `git version 2.54.0 (Apple Git-157)` |
| DigitalTwins al comenzar | Directorio con documentos, sin `.git`, código ni dependencias declaradas |
| DigitalTwins al terminar | Repositorio Git local inicializado en `main`, sin commits ni remoto; archivos nuevos pendientes de revisión |
| Fuentes vecinas | B1: `main` sin commits, archivos sin seguimiento; `x_red_social`: `main...origin/main` con cambios previos y archivos sin seguimiento; laboratorio sin `.git`. Se preservó su estado. |
| Python seleccionado | `/usr/local/bin/python3`, 3.11.5; `python` no está en PATH |
| Python del sistema | `/usr/bin/python3`, 3.9.6; no satisface `requires-python >=3.11` |
| SUMO | `sumo`, `sumo-gui`, `netconvert`, `netedit`, `duarouter`: no encontrados en PATH. Sin SUMO_HOME; tampoco SUMO en ubicaciones Homebrew y app estándar revisadas. No es una búsqueda exhaustiva de todo el disco. |
| Conversión GIS CLI | `osmium`, `ogrinfo`, `gdalinfo` y `proj`: no encontrados en PATH |
| Paquetes disponibles en Python 3.11 | Shapely 2.1.2, PyProj 3.7.2, NumPy 1.26.4, Pandas 2.2.3, PyArrow 23.0.0, DuckDB 1.5.5 |
| Paquetes no encontrados en ese intérprete | OSMnx, GeoPandas, Pyrosm, osmium, sumolib, traci, libsumo, eclipse-sumo, Fiona, Pyogrio, GDAL, NetworkX y pytest |
| Empaquetado disponible | pip 26.1.1, setuptools 70.0.0, wheel 0.45.1; Homebrew y uv presentes, sin usarlos para instalar |
| Entornos históricos | Se detectaron entornos de B1 y runtimes de evidencia; uno conserva Shapely 2.1.2. No se activaron ni se alteraron. |

La consulta de paquetes usa metadatos de distribución; no acredita toda su
funcionalidad. Shapely y PyArrow sí se usaron para la inspección. PyArrow
emitió avisos de `sysctlbyname` por restricciones del entorno, pero pudo leer
los Parquet. PyProj no se utilizó para reproyectar. No se descargaron extensiones
DuckDB, dependencias, mapas ni nuevas observaciones. La consulta externa se
limitó a documentación pública de SUMO, osmium y licencias, sin servicios de pago.

## D. Cambios dentro de DigitalTwins

- `AGENTS.md`: ámbito de escritura, observación de solo lectura, El Salvador,
  notación y modelos, aislamiento y reproducibilidad.
- `README.md`, `pyproject.toml`, `.gitignore`: propósito, instrucciones locales,
  Python mínimo y cero dependencias de ejecución; exclusión de datos grandes.
- `docs/osm_inventory.md`: este inventario; documentos anteriores conservados.
- `data/osm/README.md` y `data/osm/sources.json`: referencias y hashes de cuatro
  fuentes en su ubicación original, sin copias ni enlaces simbólicos.
- `src/digitaltwins/__init__.py` y `src/digitaltwins/doctor.py`: versión y
  diagnóstico stdlib de solo lectura, ejecutable sin instalar el paquete.
- `scenarios/pilot/README.md` y `scenarios/pilot/pilot.sumocfg`: receta futura y
  configuración con semilla 42; las entradas aún no se han generado.
- `tests/README.md`: alcance de pruebas futuras; sin modelos vacíos.
- `outputs/.gitkeep` y `outputs/intervention001/`: evidencias locales de esta
  inspección y verificaciones, excluidas de Git.
- `.git/`: inicialización local, sin commits, remotos ni cambios de configuración global.

## E. Camino más corto al primer experimento

Usar el PBF de octubre en lectura, recortar la ventana propuesta de Alameda
Roosevelt, preservar restricciones, convertir a XML y después a `.net.xml`.
La [documentación de SUMO](https://sumo.dlr.de/docs/Networks/Import/OpenStreetMap.html)
exige el paso PBF a XML e indica que las conexiones entre carriles incluyen
inferencias. No convertir directamente el SQLite ni reconstruir desde GPKG
cuando ya existe el original con relaciones.

La receta completa y sus comandos están en `scenarios/pilot/README.md`.
La demanda inicial es sintética, con semilla fija, y solo comprueba el flujo
técnico. Guardar versiones, hashes, typemap, advertencias y resultados. Revisar
conectividad, sentidos, carriles y giros antes de usar métricas de desempeño;
los tiempos semafóricos generados no son registros reales. Posteriormente,
incorporar conteos, registros semafóricos y Waze para calibración y validación.

## F. Dependencias y bloqueos

1. **Herramientas**: instalar SUMO con `netconvert`, `duarouter`, herramientas
   Python y, para inspección visual, `sumo-gui`; además `osmium-tool` u otro
   conversor PBF/XML. Requiere un incremento que autorice instalaciones;
   esta intervención las excluye. GeoPandas, OSMnx y Pyrosm no son requisitos
   del camino propuesto. Configurar PATH y SUMO_HOME y fijar versiones.
2. **Calidad del corredor**: comprobar restricciones completas y valores
   inválidos o ausentes. Definir supuestos de carriles, velocidades, accesos y
   programas semafóricos. La suficiencia nacional no garantiza la local.
3. **Tráfico real**: seleccionar corredor y sensores; obtener conteos, ubicación,
   intervalos, relojes, registros fase–movimiento y acceso autorizado a Waze.
   No se caracterizó ni se descargó ese material en esta intervención.
4. **Fuentes alternativas**: reconciliar licencias y linajes de Overture,
   índices mixtos y crosswalks antes de incorporarlos. No bloquea el PBF OSM.
5. **Reproducibilidad**: el manifiesto necesita conservar la estructura de los
   repositorios vecinos o actualizar las rutas de manera explícita. Sus hashes
   permiten detectar cambios. Aún no hay red generada ni corrida SUMO validada.

No falta una nueva descarga OSM para la primera prueba. No se requieren
servicios web, Docker, CI/CD ni modelos de IA para alcanzar ese hito.

### Verificación de la intervención

El diagnóstico pasó con coincidencia de tamaño y SHA-256 de las cuatro
fuentes. Detectó correctamente una fuente ausente y un cambio de contenido de
igual tamaño en fixtures sintéticas temporales. La exigencia de herramientas
SUMO devolvió código 1, coherente con su ausencia. Se comprobaron sintaxis de
Python, TOML, JSON y XML y que las rutas del escenario quedan dentro de
`outputs/pilot/`. La validación de esquema SUMO y la simulación siguen pendientes.

Se compararon huellas de rutas, tamaños y fechas de modificación de 95.157
archivos en los tres árboles fuente, con las exclusiones documentadas, y
huellas del estado Git de B1 y `x_red_social`: permanecieron iguales. Los
documentos preexistentes conservaron sus SHA-256. Estas huellas de árbol son
controles de metadatos; los cuatro activos principales y los documentos sí se
verificaron por contenido. Evidencias en `outputs/intervention001/`:
`source_guard_before.json`, `source_guard_after.json`, `environment.json`,
`raw_pbf_audit.json`, `local_resource_audit.json` y `validation.json`.

## Anexo de archivos geográficos medidos

Las siguientes tablas se generan a partir de los archivos locales. Las fechas
indicadas son cortes o versiones de procedencia; la fecha de modificación del
archivo se conserva aparte en la evidencia JSON y no se usa como fecha de datos.
`n/d` indica que el formato o la evidencia no permite atribuir un conteo o
cobertura válidos. Las extensiones parciales de GeoJSON no demuestran cobertura
de una red. El linaje determina la licencia según las secciones anteriores.

### Archivos OSM y bases derivadas

| Ruta absoluta | Formato; MB; registros | Corte o versión; linaje | Cobertura comprobada y posible uso |
| --- | --- | --- | --- |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/el-salvador-261014.osm.pbf` | OSM PBF; 35.169 MB; 809.396 | 2026-10-14; OSM/Geofabrik; ODbL-1.0 | SV, extracto Geofabrik; cabecera y recibo; bbox -90.500910,12.035980,-87.584382,14.457621. Entrada SUMO preferida; recorte y XML. |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/g-topo-x68-002/20261015-offline01/resource/topology-osm-v1.sqlite` | SQLite; 127.836 MB; 109.633 | 2026-10-14 / TOPOLOGY_V1; OSM/Geofabrik; ODbL-1.0 | SV, selección de clases viales; bbox -90.196344,13.156713,-87.561116,14.465394. Diagnóstico; no almacena giros relacionales ni etiquetas nodales. |
| `/Users/josefelix/Desktop/DC_X/savia-x-lab/integration/men-geographic-g001/20261014-offline01/evidence-final/SYNTHETIC_INVALID_RESOURCE/data/savia_x/reference/operational/geography/source/el-salvador.gpkg` | GPKG inválido/vacío; 0.000 MB; n/d | fixture; SYNTHETIC_INVALID_RESOURCE | No comprobable. Excluir de entradas reales. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/el-salvador.gpkg` | GPKG inválido/vacío; 0.000 MB; n/d | sin datos; placeholder | No comprobable. Excluir de entradas reales. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/source/el-salvador-260823-free.gpkg.zip` | ZIP GPKG; 89.476 MB; n/d | 2026-08-23; OSM/Geofabrik; ODbL-1.0 | SV, mismo GPKG del corte agosto. Procedencia/licencia; duplicado exacto del miembro GPKG. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/source/el-salvador.gpkg` | GeoPackage; 196.194 MB; 119.975 | 2026-08-23; OSM/Geofabrik; ODbL-1.0 | SV, 20 capas Geofabrik; bbox -90.196344,13.156713,-87.561116,14.465394. Cartografía; reconstrucción de topología necesaria para SUMO. |

### Parquet e índices nominales

| Ruta absoluta | Formato; MB; registros | Corte o versión; linaje | Cobertura comprobada y posible uso |
| --- | --- | --- | --- |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/b1_pilot_corpus/b1_public_only_geographic_resource_freeze_v0.1.0/resources/overture_divisions/division_area_sv_admin_2026-09-23.1.parquet` | GeoParquet; 0.686 MB; 288 | Overture 2026-09-23.1; Overture Divisions; ODbL y avisos por fuente, discrepancia Esri | country=SV verificado; bbox -90.220904,12.951802,-87.597147,14.451049. Contexto administrativo; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/b1_pilot_corpus/b1_public_only_geographic_resource_freeze_v0.1.0/resources/overture_divisions/division_sv_admin_2026-09-23.1.parquet` | GeoParquet; 0.046 MB; 287 | Overture 2026-09-23.1; Overture Divisions; ODbL y avisos por fuente, discrepancia Esri | country=SV verificado; bbox -90.038135,13.195090,-87.695684,14.378692. Contexto administrativo; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/b1_pilot_corpus/b1_public_only_geographic_resource_freeze_v0.1.0/resources/overture_places/overture_places_sv_bbox_2026-09-23.1.parquet` | GeoParquet; 7.144 MB; 61.099 | Overture 2026-09-23.1; Overture Places; CDLA/Apache/CC0 según proveedor | Bbox + primera dirección país SV; bbox -90.113602,13.155711,-87.696736,14.416662. Lugares auxiliares; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/config/savia_x/operational/geography/administrative_hierarchy_v1.0.0.json` | JSON nominal; 0.140 MB; 320 | 1.0.0; Sin licencia de reutilización identificada | SV, nombres/correspondencias; no geometría vial. Consulta nominal; no usar como fuente vial o autoridad geográfica. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/config/savia_x/operational/geography/territorial_name_crosswalk_v1.0.0.json` | JSON nominal; 1.165 MB; n/d | 1.0.0; Sin licencia de reutilización identificada | SV, nombres/correspondencias; no geometría vial. Consulta nominal; no usar como fuente vial o autoridad geográfica. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/overture/2026-08-19.0/el_salvador_transportation_connectors.parquet` | Parquet + WKB; 11.563 MB; 188.938 | Overture 2026-08-19.0; Overture Transportation, OSM/TomTom; ODbL frente a CDLA histórico | Selección SV + margen 250m; bbox -90.130295,13.157608,-87.694382,14.450503. Conectividad alternativa; adaptador SUMO y licencia por reconciliar. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/overture/2026-08-19.0/el_salvador_transportation_segments.parquet` | Parquet + WKB; 41.260 MB; 205.989 | Overture 2026-08-19.0; Overture Transportation, OSM/TomTom; ODbL frente a CDLA histórico | Selección SV + margen 250m; bbox -90.132805,13.156713,-87.694305,14.460768. Conectividad alternativa; adaptador SUMO y licencia por reconciliar. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56b/territorial_named_features.parquet` | Parquet + WKB; 3.704 MB; 34.587 | R56B 1.0.0 / septiembre 2026; OSM y enlaces nominales; revisar componentes sin licencia | SV, selección de nombres OSM; bbox -90.183335,13.078451,-87.675977,14.443563. Índice de lugares; no topología SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/administrative_chains.parquet` | Parquet + WKB; 0.022 MB; 320 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales. Consulta de nombres/corredores; no entrada SUMO directa. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/connector_road_membership.parquet` | Parquet + WKB; 5.980 MB; 155.763 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales; bbox -90.118312,13.166830,-87.694382,14.446094. Consulta de nombres/corredores; no entrada SUMO directa. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/named_features.parquet` | Parquet + WKB; 5.640 MB; 34.907 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales; bbox -90.183335,13.078451,-87.675977,14.451049. Consulta de nombres/corredores; no entrada SUMO directa. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/road_corridors.parquet` | Parquet + WKB; 1.266 MB; 7.502 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales; bbox -90.118324,13.166295,-87.694305,14.447883. Consulta de nombres/corredores; no entrada SUMO directa. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/road_segment_membership.parquet` | Parquet + WKB; 10.159 MB; 70.951 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales; bbox -90.118324,13.166295,-87.694305,14.447883. Consulta de nombres/corredores; no entrada SUMO directa. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/data/savia_x/reference/operational/geography/r56c/territorial_names.parquet` | Parquet + WKB; 0.828 MB; 48.787 | R56C 1.0.0 / 2026-09-04; Mixto OSM/Overture/nominal; licencia por reconciliar | SV, índices parciales. Consulta de nombres/corredores; no entrada SUMO directa. |

### GeoJSON de eventos y visualización

| Ruta absoluta | Formato; MB; registros | Corte o versión; linaje | Cobertura comprobada y posible uso |
| --- | --- | --- | --- |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/map_layer_v0.1.0.geojson` | GeoJSON; 0.000 MB; 0 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | Sin geometrías. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_5/geocoded_events_shadow_provider_v0.1.0.geojson` | GeoJSON; 0.011 MB; 11 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.509861,-87.986961,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_5/geocoded_events_shadow_v0.1.0.geojson` | GeoJSON; 0.011 MB; 11 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.509861,-87.986961,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_5d/local_resolver_v2_geojson_v0.2.0.geojson` | GeoJSON; 0.033 MB; 30 | 0.2.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_6/savia_x_map_features_v0.1.0.geojson` | GeoJSON; 0.048 MB; 30 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_6b/savia_x_map_features_ui_v0.2.0.geojson` | GeoJSON; 0.062 MB; 30 | 0.2.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_6c/savia_x_google_map_features_v0.1.0.geojson` | GeoJSON; 0.048 MB; 30 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_7/current/savia_x_map_features_ui_v0.2.0.geojson` | GeoJSON; 0.062 MB; 30 | 0.2.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r72op_7/current/savia_x_map_features_v0.1.0.geojson` | GeoJSON; 0.048 MB; 30 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.846000,13.486292,-87.832448,14.016675. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r73acq_3/pipeline/05_geocoding/local_resolver_v2_geojson_v0.2.0.geojson` | GeoJSON; 0.002 MB; 1 | 0.2.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.205671,13.778235,-89.204570,13.779100. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r73acq_3/pipeline/06_map/savia_x_map_features_v0.1.0.geojson` | GeoJSON; 0.003 MB; 1 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.205671,13.778235,-89.204570,13.779100. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r73acq_5/downstream/execution/batch/pipeline/05_geocoding/local_resolver_v2_geojson_v0.2.0.geojson` | GeoJSON; 0.083 MB; 34 | 0.2.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.434838,13.488447,-88.164039,14.206247. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/Entregable/outputs/r73acq_5/downstream/execution/batch/pipeline/06_map/savia_x_map_features_v0.1.0.geojson` | GeoJSON; 0.091 MB; 34 | 0.1.0; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.434838,13.488447,-88.164039,14.206247. Visualización de hipótesis; no red SUMO. |
| `/Users/josefelix/Desktop/DC_X/x_red_social/outputs/savia_x/visualization/territorial_cartographic_r56e/incidents.geojson` | GeoJSON; 0.082 MB; 4 | R56E; Geometría/eventos de linaje mixto; licencia por verificar | SV parcial, bbox medido; hipótesis no validadas; bbox -89.220866,13.344241,-88.437984,13.748541. Visualización de hipótesis; no red SUMO. |
