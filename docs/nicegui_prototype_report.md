# Intervención 007 — Prototipo profesional NiceGUI

**Fecha:** 17 de noviembre de 2026, America/Bogota. **Versión:** 1.0.0.

La aplicación está disponible en **http://127.0.0.1:8087** mientras se mantenga
su proceso activo. Presenta Original/0, base y cierre, con un mapa Leaflet,
reproducción FCD y gráficos ECharts. Trabaja exclusivamente con resultados
existentes. Se ejecutaron **cero simulaciones nuevas** y se conservó intacto
el visor 006.

## Iniciar y reproducir el entorno

Desde la raíz de DigitalTwins:

~~~sh
./scripts/run_nicegui.sh
~~~

El comando valida las fuentes, prepara su propio paquete y arranca un único
proceso NiceGUI, solo en 127.0.0.1. El puerto alternativo se indica con
--port; no se admite cambiar la dirección a una interfaz pública.
No hay recarga automática, túnel On Air ni servicio adicional. El servidor
necesita permanecer abierto; Ctrl+C lo detiene cuando se inicia en una terminal.

El entorno instalado es **macOS arm64 / CPython 3.11.5**:

| Componente | Versión comprobada |
|---|---|
| NiceGUI | 4.0.0 |
| PyProj | 3.7.2 |
| Leaflet, incluido en NiceGUI | 1.9.4 |
| Apache ECharts, incluido en NiceGUI | 6.1.0 |
| Chrome de revisión | 157.0.8103.79 |

Se instalaron dos dependencias directas y sus transitivas: **51 distribuciones
de ejecución**, exclusivamente en .venv-nicegui. No hubo instalaciones globales.
PyProj ya era una dependencia de visualización del proyecto y se fijó aquí
para aislar y reproducir la transformación cartográfica. FastAPI y Uvicorn
son dependencias internas de NiceGUI; no se creó un servicio independiente.
No hay React, Streamlit, Docker, bases de datos ni compilación frontend.

Para reconstruir este mismo entorno en macOS arm64 y Python 3.11:

~~~sh
python3 -m venv .venv-nicegui
PIP_CACHE_DIR="$PWD/.cache-nicegui/pip" .venv-nicegui/bin/python -m pip install \
  --require-hashes -r requirements/nicegui-macos-py311.lock
./scripts/run_nicegui.sh
~~~

La instalación inicial requiere acceso a PyPI o las ruedas ya almacenadas;
el funcionamiento posterior no requiere Internet. El lock fija versiones y
SHA-256 de las ruedas concretas, no es un lock multiplataforma. Para otro
intérprete o sistema deben resolverse y comprobarse sus ruedas por separado.
[Registro de instalación](../outputs/intervention007/installation.json),
[versiones instaladas](../outputs/intervention007/pip_freeze.txt).

El arranque usa PYTHONPATH=src, PROJ_NETWORK=OFF y evita cachés Python dentro
del código. El proceso no escribe en SAVIA-X ni importa sus entornos.
La estructura requiere los resultados locales de las intervenciones previas;
clonar Git sin esas evidencias no permite arrancar este prototipo.

## Funciones y experiencia visual

La pantalla combina identidad y aviso sintético, mapa dominante, panel lateral
de simulación y análisis inferior. Se usa una paleta verde/terracota, tipografía
del sistema, espaciado constante y separadores discretos. Las cifras principales
tienen jerarquía propia; los indicadores secundarios no se duplican en tarjetas.

Son operativos:

- Base/cierre, manteniendo el instante y pausando al cambiar de escenario.
- Iniciar, pausar, reiniciar, adelantar 10 s, velocidad 1/5/10/30× y búsqueda por
  deslizador o segundo exacto.
- Zoom, desplazamiento, selección de enlaces, tooltip e ID de vehículo y
  recuperación del encuadre completo.
- Completados finales, tiempos medio/total, waitingTime, timeLoss e impacto.
- Instante, vehículos activos y finalizados sincronizados con summary nativo.
- ECharts por OD, con vista base/cierre y diferencia de medias; serie temporal
  de vehículos activos y guía del instante consultado.
- Sección compacta de objetivo, configuración, resultado, límites y ficha Markdown.

Los indicadores agregados se rotulan como resultados finales del horizonte
1800 s. No se presentan 150 completados como una medición del instante inicial.
El contador temporal sí cambia con la reproducción. waitingTime y timeLoss
se distinguen y no se suman.

En escritorio, el mapa ocupa la mayor parte de la composición. En pantallas
menores, el panel y los gráficos se apilan. Se revisaron alineación, etiquetas,
ausencia de superposiciones y desplazamiento de página a 1024, 768, 390 y
320 px. El aviso de datos sintéticos permanece visible.

## Cartografía y georreferenciación

La red muestra **350 enlaces y 604 carriles externos** procedentes del XML
SUMO original; no se descargó cartografía. La capa predeterminada de teselas
se elimina con clear_layers antes de inicializar ui.leaflet. No hay peticiones
a OpenStreetMap, proveedores comerciales o CDNs. Bibliotecas, fuentes y
recursos de NiceGUI se sirven localmente.

La conversión aplica:

1. Restar a x/y SUMO el netOffset original (-260204.62, -1515196.25).
2. Transformar desde la proyección UTM/WGS84 zona 16 declarada por la red a
   EPSG:4326, con always_xy=True y PROJ sin red.
3. Entregar a Leaflet el orden [latitud, longitud].

Se contrastaron **243 nodos OSM independientes** con sus intersecciones SUMO:
error máximo **0,013238 m**, dentro del redondeo del XML. La ida y vuelta de
todas las coordenadas transformadas tuvo error máximo **2,16 × 10⁻⁹ m**.
El generador se detiene si falta la proyección, no hay anclas suficientes o
estas difieren más de 3 cm; no emplea ubicaciones aproximadas inventadas.
[Validación de proyección y anclas](../outputs/nicegui_prototype/projection_validation.json).

El tramo dirigido **1257993561#5** se marca como abierto en base y cerrado a
passenger en cierre. La ruta W_E ejecutada y sus alternativas se obtienen
del historial verificado. En el cierre, los 45 W_E evitan el tramo mediante
35 Avenida Sur y Calle el Progreso. No se altera la geometría o los permisos
de los experimentos para producir la imagen.

Se comparte un Canvas entre vías y vehículos: varios Canvas superpuestos
interceptaban los clics de los enlaces inferiores y se corrigieron. A escala
general, sentidos separados por pocos metros pueden compartir píxel;
la selección precisa de un enlace dirigido requiere acercarse. La prueba
de selección se realiza a escala de enlace y muestra sus atributos originales.

## Fidelidad y rendimiento temporal

Python reutiliza Sources, geometry, pack_fcd y check_metrics de la intervención
006. Verifica **1.018 artefactos** canónicos, los hashes del visor 006 y la
equivalencia de sus cifras y posiciones. Prepara únicamente Original/0:

| Escenario | Fotogramas | Muestras vehículo-segundo | Tiempo total |
|---|---:|---:|---:|
| Base | 1800 | 19.935 | 19.935 s |
| Cierre | 1800 | 20.340 | 20.340 s |

Son **40.275 posiciones nativas**, a resolución de 1 s, con IDs y velocidades
originales. No hay interpolación. El paquete preparado ocupa **2.109.995 bytes**.
[Manifiesto](../outputs/nicegui_prototype/manifest.json).

El navegador carga el paquete una vez y actualiza localmente los marcadores,
contadores y guía temporal. Python no envía una actualización por vehículo o
fotograma. El tráfico observado durante 2,5 s de reproducción a 30× fue un
acuse de transporte de NiceGUI y ningún mensaje de datos de reproducción.
Los estados de dos clientes se comprobaron independientes.

En la revisión headless, con reproducción entre 400 y unos 475 s a 30×,
se midieron 89 actualizaciones: media **1,10 ms**, P95 **1,50 ms**, máximo
**1,90 ms** de trabajo JavaScript por actualización. El intervalo medio de
callbacks requestAnimationFrame fue **16,67 ms**. No se observaron bloqueos
con esta carga de 150 viajes totales: hasta 26 activos en ese intervalo y
28 como máximo del escenario completo.

La medición JavaScript no incluye todo el pintado asíncrono de Leaflet ni
constituye un benchmark de redes urbanas grandes. A velocidad 1× las posiciones
cambian una vez por segundo, conforme a los datos; su movimiento no es continuo.
Una pérdida prolongada de foco del navegador reduce la velocidad efectiva:
no se inventan fotogramas para recuperar tiempo de pared.

## Pruebas y capturas reales

Pasaron **52 pruebas unitarias**, incluidas las 44 previas y ocho nuevas de
proyección y conservación del visor 006. No se modificaron los experimentos
para facilitar las pruebas. [Registro](../outputs/intervention007/tests.log).

Chrome pasó **48 comprobaciones funcionales**, con todo destino ajeno al
origen local bloqueado: carga, posiciones/IDs, tiempos, cifras, aislamiento
entre escenarios y clientes, gráficos, controles, selección, zoom, pan y
adaptación a cuatro anchos. Hubo **cero solicitudes externas y cero errores
JavaScript**. HTTP y WebSocket de loopback permanecen disponibles: ese es el
canal local necesario para NiceGUI.
[Resultado y diagnóstico de rendimiento](../outputs/intervention007/browser/validation.json).

Capturas tomadas del producto real, sin generación ni retoque:

- [Pantalla inicial](../outputs/intervention007/browser/01_initial_desktop.png).
- [Base con vehículos](../outputs/intervention007/browser/02_base_vehicles.png).
- [Cierre y análisis](../outputs/intervention007/browser/03_closure_desktop.png).
- [Panel de indicadores](../outputs/intervention007/browser/04_indicators.png).
- [Pantalla móvil](../outputs/intervention007/browser/05_mobile_closure.png).
- [Mapa móvil](../outputs/intervention007/browser/06_mobile_map.png).

La prueba del navegador usa tests/browser_nicegui.cjs, Playwright y Chrome ya
disponibles en el entorno de revisión; no son dependencias del prototipo.
Con el servidor activo y un Node que pueda resolver Playwright:

~~~sh
node tests/browser_nicegui.cjs
~~~

Puede indicarse NODE_PATH a los módulos existentes del entorno de revisión.
DT_NICEGUI_URL y DT_CHROME_PATH permiten señalar otro puerto de loopback o
ejecutable Chrome. El script usa un perfil exclusivo dentro de outputs y
bloquea destinos que no coincidan con el servidor probado.

## Integridad, archivos y comparación con la 006

La [auditoría final](../outputs/intervention007/final_validation.json) coteja
los **3.795 archivos previos protegidos**, verifica los datos empaquetados
frente a FCD, XML y métricas nativos, y revisa las huellas de los repositorios
vecinos. .DS_Store se registra por separado. No se reescribe ninguna evidencia
canónica de las intervenciones 001–006 ni el contrato matemático.

Se crearon seis archivos en src/digitaltwins/nicegui_app/, el lanzador
scripts/run_nicegui.sh, el lock de requisitos, dos archivos de pruebas y este
informe. Se actualizaron README.md, tests/README.md, pyproject.toml y .gitignore.
Los productos propios están en outputs/nicegui_prototype/ y las evidencias en
outputs/intervention007/. No se eliminaron archivos anteriores, cambiaron
simulaciones o publicaron cambios remotos.
[Registro de cambios](../outputs/intervention007/changes.json).

| Aspecto | Visor 006 conservado | Prototipo 007 |
|---|---|---|
| Ejecución | Un HTML file:// sin servidor. | Entorno virtual y un proceso local NiceGUI. |
| Alcance | 15 pares, cuatro animaciones y estados semafóricos. | Original/0 base/cierre; sin señales animadas. |
| Mapa | SVG en coordenadas métricas SUMO. | Leaflet georreferenciado, sin teselas. |
| Análisis | Catálogo amplio, matriz, enlaces y casos N_E. | Comparación OD, diferencias y vehículos activos. |
| Presentación | Consulta detallada de evidencias. | Pantalla de presentación más sobria y concentrada. |
| Portabilidad | Se puede compartir el HTML para consultar sus datos integrados. | Requiere Python, dependencias y las evidencias locales para arrancar. |

## Evaluación y recomendación

**Calidad visual:** la composición evita tarjetas repetidas, prioriza el mapa
y separa resultados finales de estado instantáneo. Las capturas muestran una
interfaz legible, alineada y sin superposiciones; en móvil requiere más recorrido
vertical, coherente con la reducción de ancho.

**Capacidad cartográfica:** Leaflet aporta zoom, pan, escala métrica y selección,
con georreferenciación contrastada. Sin teselas, el contexto es exclusivamente
la red importada; no se muestran edificios o referencias urbanas adicionales.
El acercamiento permite distinguir enlaces paralelos.

**Reproducción:** el cliente mantiene fluidez y controles independientes sin
tráfico por marcador desde Python. La resolución discreta y el volumen pequeño
de la prueba delimitan la conclusión de rendimiento.

**Integración:** se reutilizan validadores y evidencias existentes; el código
Python prepara un contrato JSON que la presentación consume sin ejecutar SUMO.
El exportador de la 006 no se modifica ni se vuelve a generar.

**Complejidad:** 747 líneas de código del módulo, incluidas 224 de JavaScript
y 219 de CSS, más un lanzador de diez líneas. Se añaden dos dependencias
directas, con 51 distribuciones resueltas. No se necesita una cadena de
compilación frontend, servicio adicional o base de datos.

**Mantenibilidad:** nuevas simulaciones pueden incorporarse mediante otro
proveedor del mismo esquema JSON, conservando los controles y el diseño.
El cargador actual fija deliberadamente Original/0. El puente JavaScript
accede a las instancias de Leaflet/ECharts expuestas por los componentes de
NiceGUI 4.0.0; se debe repetir la prueba funcional al actualizar esa versión.

**Recomiendo NiceGUI como interfaz principal del laboratorio experimental
actual**, conservando la 006 como visor portátil y herramienta de análisis
amplio. La integración Python, la cartografía y la reproducción solicitadas
quedaron resueltas con una aplicación pequeña y verificable.

Consideraría React si los requisitos evolucionan hacia un producto web con
interacciones cliente mucho más complejas, muchos usuarios o una biblioteca
extensa de componentes propios, y una evaluación demuestra que el puente
JavaScript o el ciclo de desarrollo NiceGUI limitan el trabajo. Este prototipo
no aporta evidencia de que React sea necesario ni un benchmark comparativo
entre frameworks.

Referencias de integración: [Leaflet en NiceGUI](https://nicegui.io/documentation/leaflet),
[ECharts en NiceGUI](https://nicegui.io/documentation/echart) y
[configuración del servidor](https://nicegui.io/documentation/section_configuration_deployment).
