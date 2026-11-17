# Intervención 008 — Comparación sincronizada con NiceGUI

**Fecha:** 17 de noviembre de 2026, America/Bogota. **Versión:** 1.0.0.

El visualizador conserva el modo único y añade dos mapas **Base / Cierre**
para Original/0, con un solo reloj y selección del mismo vehículo. No se
ejecutaron simulaciones nuevas ni se añadieron dependencias.

## Inicio y uso

Desde la raíz de DigitalTwins:

~~~sh
./scripts/run_nicegui.sh
~~~

Abrir **http://127.0.0.1:8087**. El servidor continúa limitado a loopback,
sin recarga automática ni exposición a la red local. Se reutilizan el entorno
.venv-nicegui y el lock de la 007: NiceGUI 4.0.0, PyProj 3.7.2, Leaflet 1.9.4
y ECharts 6.1.0. La preparación valida entradas y escribe exclusivamente su
nuevo paquete en outputs/nicegui_comparison/.

1. Elegir **Comparar base y cierre**; ambos mapas conservan el instante elegido.
2. Reproducir, pausar, reiniciar, adelantar 10 s o indicar un segundo exacto.
   Las velocidades disponibles son 1, 5, 10 y 30×.
3. Buscar un ID original o pulsar un vehículo. El mismo ID se resalta en amarillo
   en ambos escenarios, con sus rutas efectivamente ejecutadas.
4. Usar **Localizar en ambos** para encuadrar sus posiciones registradas;
   **Encuadrar** recupera la red completa.
5. Volver a **Un mapa** y elegir Base/Cierre. El selector permanece accesible
   en móvil aunque los indicadores estén contraídos.

## Sincronización y fidelidad

ReplayClock es un modelo de presentación, no un modelo de tráfico. Solo existe
una instancia por página. Su tiempo entero selecciona un snapshot con las
muestras nativas de base y cierre en ese mismo segundo. Los dos MapPane
consumen el snapshot dentro de la misma ejecución JavaScript, sin esperas
asíncronas entre ellos ni temporizadores independientes.

La animación usa requestAnimationFrame, pero cambia posiciones únicamente en
los segundos registrados. **No hay interpolación**. Cambiar modo o escenario
pausa la reproducción y conserva el instante; cambiar velocidad mantiene
el reloj compartido. En modo único se evita repintar el panel oculto; al
reactivar la comparación se actualizan ambos paneles antes de continuar.

Los datos de posiciones conservan exactamente los **2.109.995 bytes y el
SHA-256 de la 007**. Son 1800 fotogramas por escenario y 40.275 muestras
vehículo-segundo: 19.935 base y 20.340 cierre. No se reconstruyen trayectorias
a partir de promedios.

El catálogo individual nuevo contiene **300 registros**, uno por cada ID y
escenario, procedentes de tripinfo y executed_routes originales. Permite
distinguir un vehículo activo, uno que aún no salió y uno que ya finalizó,
usando su registro individual. Si falta una muestra dentro del viaje se
declara la ausencia: no se inventa una coordenada ni se reutiliza una posición
anterior. El catálogo ocupa 161.237 bytes.

Los mapas vinculan zoom y desplazamiento. La revisión del arrastre midió una
diferencia entre centros de **0,0302 píxeles CSS**, dentro de un píxel de
redondeo cartográfico de Leaflet. Esta tolerancia de cámara no afecta la
igualdad exacta del segundo, los IDs o las coordenadas FCD consumidas.

## Mejoras visuales y cartográficas

- Se aumentó el contraste de la red y el peso visual del corredor experimental.
  Esta jerarquía es gráfica; no declara una clasificación vial oficial nueva.
- Base y cierre conservan verde/terracota. El cierre usa una línea discontinua
  de color vino, el desvío un trazo ocre y el ID elegido un punto amarillo
  con borde oscuro. La leyenda distingue estos elementos.
- La selección de un enlace se refleja en ambos mapas. La lista de 350 enlaces
  permite elegir un sentido concreto cuando varios trazos comparten píxel
  a escala general.
- El rótulo fijo del cierre cede espacio al ID seleccionado para evitar
  superposiciones; la línea, leyenda y encabezado mantienen identificado el cierre.
- Las etiquetas principales usan términos comprensibles: tiempo detenido,
  tiempo perdido, activos y viajes finalizados. Los nombres waitingTime y
  timeLoss se conservan como referencia técnica y se advierte su solapamiento.
- La comparación presenta una tabla común de indicadores, evitando dos paneles
  completos repetidos. Los indicadores finales se separan de los contadores
  del instante consultado.

La geometría sigue siendo la red verificada de 350 enlaces y 604 carriles
externos. Se conserva la conversión UTM/WGS84 a coordenadas Leaflet y la
validación contra 243 nodos OSM; no se usan ubicaciones aproximadas.
El enlace intervenido sigue siendo **1257993561#5**, abierto en base y cerrado
a passenger en cierre. Solo cambia su representación, no los experimentos.

Se eliminan las teselas predeterminadas antes de inicializar cada ui.leaflet.
Todos los recursos, fuentes y gráficos se sirven localmente. No hay CDNs,
fondos cartográficos externos ni datos de tráfico reales.

## Escritorio, móvil y trazabilidad

En escritorio, los mapas se presentan lado a lado. En móvil se apilan para
mantener una superficie útil, con los controles temporales accesibles al
desplazarse. Indicadores y gráficos empiezan contraídos por debajo de 760 px
y pueden abrirse independientemente. La selección Base/Cierre y los controles
de reproducción permanecen fuera de esas secciones.

Se revisaron 1600, 1024, 768, 390 y 320 px, sin desbordamiento horizontal.
Las capturas finales se inspeccionaron para comprobar texto, cifras, leyendas,
controles y ausencia de rótulos superpuestos.
Una revisión adicional a 390 × 900 px confirmó que los controles se mantienen
en el área visible al desplazarse hasta el segundo mapa:
[comprobación del control móvil](../outputs/intervention008/browser/mobile_controls_validation.json).

La pantalla identifica **SIM-005 / Original / desfase 0 s**, la fuente FCD,
los parámetros y las limitaciones. Las fichas SIM-002 a SIM-005 se sirven
como referencia documental, sin reescribirlas. Se mantienen demanda sintética,
atributos inferidos, semáforos virtuales y ausencia de calibración real.
El visor 006 continúa siendo la referencia para la matriz completa, señales
por segundo y los demás análisis.

## Pruebas y rendimiento

Pasaron **56 pruebas Python** y **10 pruebas JavaScript** del reloj, snapshots,
identificadores, rutas y estados individuales:

~~~sh
PYTHONPATH=src .venv-nicegui/bin/python -B -m unittest discover -s tests -v
node --test tests/test_replay_model.cjs
~~~

La revisión Chrome pasó **55 comprobaciones del comparador**. Auditó **161
observaciones de animación**, todas con el mismo segundo y las posiciones
FCD exactas en ambos mapas. También contrastó búsquedas, pausa, reinicio,
velocidad, horizontes, ausencia de vehículos, rutas, cámaras, cifras,
cuatro fichas y expansión de secciones móviles.

Se conservó el conjunto de **48 comprobaciones de regresión de la 007**:
modo único, cifras, FCD, gráficos, controles, selección, zoom, pan, clientes
independientes y adaptación móvil. Solo se adaptaron los selectores de prueba
al mapa principal y la apertura de indicadores plegables. Sus resultados se
guardan en la 008 para no sobrescribir evidencias históricas.

Ambas revisiones tuvieron **cero solicitudes externas y cero errores
JavaScript**. HTTP/WebSocket de loopback permanecen disponibles para NiceGUI.
La reproducción observada no envió actualizaciones de vehículos desde Python:
el tráfico de transporte registrado fue exclusivamente de acuses de recibo.

| Muestra instrumentada a 30× | Modo único, regresión | Dos mapas e ID seleccionado |
|---|---:|---:|
| Actualizaciones medidas | 91 | 96 |
| Trabajo JavaScript medio | 1,23 ms | 2,31 ms |
| P95 | 2,00 ms | 4,80 ms |
| Máximo | 2,90 ms | 5,50 ms |

El intervalo medio de callbacks requestAnimationFrame fue aproximadamente
16,67 ms. No se observaron bloqueos con esta carga: 150 viajes por escenario,
hasta 25 activos en base y 28 en cierre. El pintado asíncrono de Leaflet queda
fuera de la medición de trabajo JavaScript. Son muestras cortas en Chrome
headless con instrumentación de validación; no constituyen un benchmark de
redes grandes o de hardware distinto. A 1×, la actualización de posición
sigue siendo una vez por segundo.

Evidencias: [pruebas Python](../outputs/intervention008/tests.log),
[pruebas JavaScript](../outputs/intervention008/model_tests.log),
[Chrome comparador](../outputs/intervention008/browser/validation.json),
[sincronización observada](../outputs/intervention008/browser/synchronization.json)
y [regresión 007](../outputs/intervention008/regression007/browser/validation.json).
Con el servidor activo y el Playwright ya disponible en el entorno de revisión:

~~~sh
node tests/browser_comparison.cjs
node tests/browser_nicegui.cjs
~~~

NODE_PATH puede apuntar a los módulos existentes de revisión. No es una
dependencia del producto y no se instaló software para estas pruebas.

## Capturas reales de Chrome

- [Modo único en escritorio](../outputs/intervention008/browser/01_single_desktop.png).
- [Comparación, reloj e indicadores](../outputs/intervention008/browser/02_comparison_desktop.png).
- [Detalle de ambos mapas](../outputs/intervention008/browser/03_two_maps.png).
- [Comparación móvil con secciones contraídas](../outputs/intervention008/browser/04_comparison_mobile.png).
- [Análisis móvil expandido](../outputs/intervention008/browser/05_mobile_analysis.png).
- [Modo único móvil y selector visible](../outputs/intervention008/browser/06_single_mobile.png).
- [Controles visibles al desplazarse al segundo mapa](../outputs/intervention008/browser/07_mobile_controls_scrolled.png).

## Archivos, conservación y límites

Se refactorizó app.py y data.py, y se añadió layout.py. El cliente anterior
replay.js y styles.css se sustituyó por comparison.js, comparison.css,
map-pane.js y replay-model.js. Se añadieron las pruebas específicas,
se adaptó tests/browser_nicegui.cjs y se actualizaron README.md y tests/README.md.
El comando de inicio y las dependencias permanecieron iguales.

Los productos nuevos están en outputs/nicegui_comparison/ y la auditoría en
outputs/intervention008/. El código original 007 quedó archivado con hashes
antes de la refactorización. Los resultados científicos, capturas y auditorías
001–007, los originales OSM, el contrato matemático y los repositorios vecinos
se conservan. .DS_Store se registra separadamente.

La [auditoría final](../outputs/intervention008/final_validation.json) revisa
3.830 archivos previos protegidos, la igualdad del paquete FCD con la 007,
los 300 registros individuales y sus rutas y la coherencia con los resultados
canónicos. [Registro de cambios](../outputs/intervention008/changes.json).

El alcance animado sigue limitado a Original/0. No se incorporaron señales
animadas ni observaciones reales, ni se ejecutaron modelos o simulaciones.
La resolución de 1 s produce movimiento discreto. Los enlaces muy próximos
requieren zoom o selección por lista. La comparación móvil usa mapas apilados;
se revisó en Chrome, sin extender la validación a otros navegadores.
