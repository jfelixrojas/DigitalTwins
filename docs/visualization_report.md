# Intervención 006 — Visor local y documentación OSM–SUMO

**Fecha:** 17 de noviembre de 2026, America/Bogota. **Versión:** 1.0.0.

El [visor HTML](../outputs/visualization/index.html) permite explorar las
15 comparaciones temporales, alternar base/cierre, consultar métricas y
reproducir cuatro corridas FCD. Funciona con file://, sin servidor, conexión,
CDN ni mapas externos. Esta intervención ejecutó **cero simulaciones SUMO**.

## Uso y regeneración

Abrir el HTML con doble clic. Seleccionar combinación y escenario; mover la
línea temporal o pulsar Reproducir/Pausar. Los botones ±1 s permiten inspección
paso a paso. El mapa admite zoom, arrastre, selección de enlaces y retorno al
encuadre original. La tabla de sensibilidad abre cada combinación. Experimentos
ofrece las cuatro fichas dentro del propio visor.

Desde la raíz del proyecto:

~~~sh
PYTHONPATH=src python3 -B -m digitaltwins.visualization
~~~

El generador usa solo la biblioteca estándar Python. Comprueba las evidencias
canónicas y sustituye únicamente su propio paquete. Para consultar animación,
tablas y fichas basta copiar index.html; sus enlaces a documentación, figuras
y evidencias requieren conservar la estructura del proyecto.

## Inventario y selección de evidencia

| Experimento | FCD originales | Logs nativos TLS | Evidencia reutilizada |
|---|---:|---:|---|
| SIM-002 | 0 | 0 | Red, solicitudes, ruteo, tripinfo, summary y repetición. |
| SIM-003 | 0 | 0 | Red y auditoría de atributos, rutas, métricas, series por enlace y figuras. |
| SIM-004 | 0 | 0 | Comparación, rutas ejecutadas, permisos, métricas, edgeData y figuras. |
| SIM-005 | 32 | 32 | 30 corridas de matriz y dos de repetición, con trayectorias, señales y agregados. |

Las dos corridas adicionales de auditoría inicial de SIM-005 no tienen FCD;
no se cuentan como combinaciones nuevas. El
[catálogo de fuentes](../outputs/visualization/source_catalog.json) registra
272 archivos con roles, tamaños y SHA-256, incluida la evidencia inventariada.
El generador coteja **1.018 artefactos** contra los cuatro manifiestos previos.

La selección animada contiene Original/0 y J103/0, base/cierre: cuatro archivos,
7.200 fotogramas y **80.000 muestras vehículo-segundo**, conservadas a 1 s,
sin interpolación ni posiciones inferidas. Los FCD originales permanecen
intactos. Los otros trece pares muestran agregados y señales y anuncian
explícitamente que no se incluyen posiciones en el paquete.

La geometría corresponde a los 350 enlaces externos y sus 604 carriles.
Se usan también los carriles internos necesarios para asociar las
84 conexiones semaforizadas por tl, linkIndex y via. Se conservan los x/y
locales nativos; el radio de los puntos es un recurso gráfico, no el tamaño
físico de los vehículos. Los colores semafóricos son registros de simulación.
Los logs iguales por offset se deduplican y se comprimen a cambios de fase
sin pérdida de resolución temporal.

## Cifras y lectura

El panel distingue solicitados, completados, pendientes, tiempo total y medio,
waitingTime, timeLoss, longitud y espera de salida. La comparación usa
cierre − base. Incluye los seis OD con nombres, las 45 rutas W_E desviadas,
vehículos activos y los dos casos N_E investigados.

Original/0 conserva **19.935 → 20.340 s**, cambio **+405 s (+2,03 %)**.
J103/0 conserva **19.872 → 19.853 s**, cambio **−19 s**. En todos los cierres,
los 45 W_E evitan 1257993561#5 y añaden 105,55 m por viaje.
Los demás indicadores se leen de los resultados estructurados verificados;
no se duplican manualmente en el código de la interfaz.

Hay totales de los 350 enlaces y series de 60 s para cinco enlaces de interés.
El flujo se presenta en veh/h; la ocupación en porcentaje; la presencia media
en vehículos. El máximo de ocupación corresponde a intervalos, no a un instante.
La ausencia de una serie no se representa como cero ni deja visible el
gráfico de otro enlace. No se equiparan ocupación, cola y estado de celda.
waitingTime y timeLoss se muestran separados y no se suman.

Las cuatro fichas Markdown y su catálogo se generan desde metadatos y
resultados; contienen fechas con zona, configuración, semillas, preguntas,
interpretación, comandos y hashes de manifiestos. El
[flujo técnico](sumo_osm_workflow.md) documenta la cadena realmente ejecutada.
Ocho [figuras estáticas](../outputs/visualization/figures/) PNG/SVG copian
exactamente cuatro figuras verificadas de las intervenciones anteriores.

## Validación

Pasaron **44 pruebas unitarias**: las 33 existentes y once nuevas de integridad
visual. Registro: [tests.log](../outputs/intervention006/tests.log).

Chrome **157.0.8103.79** completó **59 comprobaciones** mediante file://,
con contexto sin conexión, HTTP(S) bloqueado y perfil exclusivo de prueba.
Se comprobaron los cuatro casos animados, posiciones exactas, asociación TLS,
los 15 selectores, cifras, reproducción/pausa/pasos, zoom, enlaces con y sin
serie, fichas, archivos estáticos y ausencia de desbordamiento de página a
390 y 320 px. Hubo **cero peticiones externas y cero errores JavaScript/CSP**.
Las capturas de escritorio, móvil y ficha se revisaron visualmente.
[Resultado del navegador](../outputs/intervention006/browser/validation.json).

La [auditoría final](../outputs/intervention006/final_validation.json) coteja
los 3.728 archivos previos protegidos, trata .DS_Store por separado, verifica
las cuatro fuentes OSM y conserva las huellas de los tres repositorios vecinos.
También contrasta el contenido empaquetado con FCD, señales, geometría,
métricas, series y manifiestos nativos. No modifica las evidencias anteriores.

La continuidad de SIM-002 a SIM-005 se comprueba conservando código, entradas,
versiones de herramientas, base PROJ, manifiestos y resultados de repetición
verificados, además de ejecutar las pruebas anteriores. **No se hizo una nueva
repetición de simulación en la 006**. Sus comandos permanecen en las fichas.

## Cambios y límites pendientes

Se crearon los seis archivos del módulo src/digitaltwins/visualization/,
tests/test_visualization.py, este informe, sumo_osm_workflow.md y las cinco
páginas de docs/simulations/. Se actualizaron README.md y tests/README.md.
Los productos están en outputs/visualization/ y las comprobaciones en
outputs/intervention006/. No se eliminó código ni se cambió el comportamiento
de las simulaciones. [Registro de cambios](../outputs/intervention006/changes.json).

No se instalaron dependencias, descargaron datos ni publicaron cambios remotos.
El documento Word que ya estaba presente se conserva intacto.
Las tablas anchas permiten desplazamiento horizontal en móvil. La ejecución
en otros navegadores no fue comprobada; las figuras son la alternativa estática.
Si faltan los resultados locales, clonar Git no basta para regenerar el visor.

Persisten demanda sintética, atributos inferidos, tres componentes de red y
programas virtuales sin calibración. La sensibilidad de quince diseños no es
un intervalo de confianza ni demuestra saturación o un efecto real del cierre.
No hay integración de observaciones oficiales, Waze, CTM, LTM ni GNN.
