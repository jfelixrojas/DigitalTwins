# Primer piloto SUMO reproducible de Alameda Roosevelt

Intervención 002 · cierre 2026-11-17, America/Bogota.

**El escenario base funciona por línea de comandos y es reproducible.** De
150 solicitudes sintéticas, 109 tienen ruta válida, ingresan y completan su
recorrido. Las otras 41 se conservan como rechazos identificados. No quedan
vehículos pendientes ni se registran colisiones o teletransportes. Las dos
corridas finales producen las mismas métricas y atributos por vehículo.
Este resultado verifica un flujo técnico, no un gemelo digital calibrado.

## A. Herramientas y entorno

| Herramienta | Versión y ubicación |
| --- | --- |
| SUMO, netconvert y duarouter | **1.28.0**, instalador oficial Apple Silicon, `/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/bin/` |
| SUMO_HOME | `/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/share/sumo` |
| Osmium | **1.19.1**, fórmula Homebrew `1.19.1_1`, `/opt/homebrew/bin/osmium`; libosmium 2.23.1 |
| Python | 3.11.5; código del proyecto basado en biblioteca estándar |
| Datos PROJ reutilizados | PyProj 3.7.2 ya instalado, base PROJ 9.5.1; misma versión que la biblioteca incluida en SUMO |

La instalación fue autorizada explícitamente. Se comprobó el hash oficial
del paquete, firma y notarización; se aceptó EPL 2.0 tras confirmación del
usuario. La llamada administrativa CLI no pudo abrir el paquete del Escritorio;
la aplicación Installer completó la instalación. El primer chequeo de firma
dentro del sandbox falló; el chequeo con acceso al servicio de confianza de
macOS confirmó firma y notarización válidas. Ambas evidencias se conservan.

Homebrew instaló Boost 1.92.0_1 e ICU 79.1 y actualizó las dependencias necesarias
LZ4 a 1.11.1, XZ a 5.8.4 y Zstd a 1.5.7_1. Se deshabilitaron actualización
general, limpieza y actualización de dependientes ajenos. No se modificaron
entornos Python de SAVIA-X. Los kegs antiguos de LZ4, XZ y Zstd permanecen.
`sumo-gui` viene en el paquete, pero no se probó la visualización: no se instaló
XQuartz. Tampoco se ejecutó Scenario Wizard ni un servicio web.

## B. Entrada y red generada

Fuente: PBF Geofabrik El Salvador, datos a **2026-10-14 20:21:12 UTC**, SHA-256
`73369769b9a7f45dd9f0b3a44511da0c29101c7268805b9c9f415114a6c27672`.
Se volvió a verificar antes y después del proceso. No se descargaron mapas.

Se mantuvo la ventana inicial `[-89.216,13.699,-89.207,13.705]`, CRS84. El
recorte `smart`, completando relaciones `restriction`, contiene 4.502 nodos,
664 vías y 32 relaciones; 356 vías tienen `highway`. Completar vías y giros
extiende sus geometrías fuera del rectángulo: la red resultante alcanza
`[-89.217181,13.695954,-89.204717,13.705878]`, aproximadamente 1.351 × 1.099 m
en UTM 16N. Esto es efecto de conservación de miembros, no una ampliación
manual para mejorar los resultados.

| Elemento SUMO | Resultado |
| --- | ---: |
| Enlaces externos dirigidos, para automóviles | 350 |
| Carriles externos | 604 |
| Nodos junction externos | 243 |
| Nodos extremos dead_end incluidos en los anteriores | 21 |
| Nodos con tres o más vecinos distintos | 87 |
| Conexiones externas entre carriles para passenger | 810 |
| Conexiones XML totales, incluidas internas | 1.667 |
| Aristas internas de intersecciones | 605 |
| Programas semafóricos generados | 18 |
| Componentes débilmente conexas, por enlaces | 321, 21 y 8 |

Los nodos junction incluyen subdivisiones y extremos: 243 no equivale a 243
intersecciones físicas. La medida de 87 se define por vecinos distintos y
tampoco sustituye una inspección geométrica. La conectividad utilizable se
acredita además mediante las rutas y sus movimientos comprobados.

Las **11 relaciones de giro** del recorte tienen miembros completos: siete
`no_left_turn` y cuatro `only_straight_on`. Se mapearon por vía OSM y nodo via
contra las conexiones para automóviles: **cero maniobras prohibidas detectadas**.
IDs, miembros y resultados individuales están en `osm_audit.json` y
`network_audit.json`. No se afirma validez de todas las restricciones del PBF
nacional ni que la ausencia de una etiqueta demuestre permiso de circulación.

## C. Resultados de las dos corridas

Demanda sintética de automóviles: semilla **42**, inicio 0 s, fin de generación
900 s, período 6 s, horizonte de simulación 1800 s. Sin conteos, Waze ni
registros operacionales reales.

| Métrica | Base | Repetición |
| --- | ---: | ---: |
| Solicitudes originales | 150 | 150 |
| Rutas válidas | 109 | 109 |
| Solicitudes rechazadas | 41 | 41 |
| Vehículos cargados e ingresados | 109 | 109 |
| Recorridos completados | 109 | 109 |
| Pendientes dentro de la red | 0 | 0 |
| Pendientes de ingreso | 0 | 0 |
| Vehículos retirados | 0 | 0 |
| Teletransportes / colisiones | 0 / 0 | 0 / 0 |
| Frenadas de emergencia / paradas de emergencia | 0 / 0 | 0 / 0 |
| Tiempo medio de recorrido | 114,83 s | 114,83 s |
| Tiempo medio detenido, waitingTime de tripinfo | 33,47 s | 33,47 s |
| Pérdida media de tiempo, timeLoss | 54,05 s | 54,05 s |
| Demora media de salida | 0,28 s | 0,28 s |
| Longitud media de recorrido | 932,37 m | 932,37 m |
| Velocidad media reportada por SUMO | 9,10 m/s | 9,10 m/s |

Balances comprobados: `150 = 109 + 41` y `109 ingresados = 109 completados +
0 en circulación + 0 retirados`. Los 109 cargados coinciden con ingresados
más pendientes de ingreso. Los 41 rechazos no son vehículos que hayan
ingresado ni vehículos pendientes al terminar.

## D. Advertencias, supuestos y correcciones

**Solicitudes sin ruta.** Se conservaron los 150 viajes antes de validación y
los 41 IDs rechazados, con sus extremos. Hay 29 pares en distintas componentes
y 12 sin camino dirigido dentro de su componente. No se eliminaron calles ni
se unieron extremos artificialmente para mejorar la aceptación. La ventana
original ya permite una prueba funcional; tratar sus bordes y componentes
es trabajo posterior.

**Comportamiento de randomTrips 1.28.0.** El valor por defecto vuelve a sortear
OD fallidos para llenar la cuota. Se añadió `--min-success-rate 1` para evitar
ese relleno y conservar el balance solicitado/aceptado/rechazado. La primera
generación usa `--no-validate` para preservar solicitudes originales. La
validación mantiene semilla, período, ventana temporal y clase vehicular.
Se verificó que las 109 rutas aceptadas conservan origen, destino y salida
de las solicitudes originales.

La herramienta oficial llama internamente a duarouter con `--ignore-errors`
para descartar viajes sin ruta. Esto se declara en `routing_audit.json`, no
se interpreta como aceptación de los 150. Se conservaron salida y registros
de advertencias. La simulación SUMO se ejecutó con tratamiento normal de
errores, sin opciones para ignorarlos, sin desactivar colisiones o teletransportes
y sin modificar las solicitudes fallidas.

**Datos inferidos.** El recorte tiene 71 vías `highway` con `lanes` y 63 con
`maxspeed`. En la red final se registran defaults de número de carriles en
138 enlaces, de velocidad en 137 y de ambos en 113; son 162 enlaces con al
menos uno de esos defaults. Se guardó el hash del typemap y las anotaciones
`osmDefaults`. Los conteos de vías OSM y enlaces SUMO tienen denominadores
diferentes por filtrado, segmentación y sentidos.

Hay 21 nodos OSM semafóricos; tres no controlan conexiones retenidas y SUMO
no construyó sus programas (`191997676`, `192024481`, `4337995469`). Los 18
programas restantes son **sintéticos**, no fases ni ciclos observados. No se
accedió a controladores reales.

**Conversión.** Se conservaron 25 líneas de advertencia en netconvert, con
agregación: tipos ajenos al modo passenger, paradas/líneas de transporte público
incompletas, radio de giro pronunciado, desplazamientos de forma de dos nodos,
programas semafóricos sin conexiones, una posible falta de carril de giro y
18 reducciones de velocidad en conexiones por radio de giro. No se modela
transporte público en este piloto. `warnings.json` conserva los mensajes y
grupos agregados; el número de líneas no es el número total de eventos.

El enrutador registra tres familias de avisos correspondientes a los 41
rechazos. Las dos simulaciones finales tienen registros de errores y
advertencias vacíos. No se ocultaron las advertencias de conversión ni los
rechazos del enrutador.

**PROJ.** La primera ejecución encontró `Cannot find proj.db`: el instalador
incluye libproj 9.5.1 pero carece del directorio de datos esperado. Se corrigió
`PROJ_DATA` solo para los procesos del piloto usando la base PROJ 9.5.1 ya
existente en PyProj. Se fijó su SHA-256 en el manifiesto y se mantuvo
`PROJ_NETWORK=OFF`. No se instaló ni modificó PyProj. La ejecución final no
emite esos avisos; la inicial se conserva separadamente en `outputs/pilot/`.

## E. Reproducibilidad y evidencias

La ejecución final está en **`outputs/pilot_verified/`**. `base/` y `repeat/`
usan exactamente la misma red, rutas, versión y semilla, con configuraciones
de contenido idéntico. Coinciden conteos, seguridad, teletransportes, métricas
agregadas y todos los atributos por vehículo de `tripinfo`. Las cabeceras con
fecha, rutas de archivos y estadísticas de CPU/reloj no se usan para exigir
igualdad binaria de todas las salidas.

Se ejecutaron siete pruebas sintéticas focales. La validación real comprobó
la red no vacía, las once restricciones, cada transición de las 109 rutas,
los balances, los hashes de artefactos y los de las fuentes. Se verificó además
que el hash del ejecutor coincide con el manifiesto. El éxito exige recorridos
completados y balances coherentes, además del código cero del simulador.

Los cuatro recursos principales y documentos originales conservan sus hashes.
La comparación de árboles con la intervención 001 detectó dos archivos Finder
`.DS_Store` adicionales, con fechas anteriores al archivo del encargo 002;
al excluir únicamente esos dos añadidos, coinciden las huellas de los 95.157
archivos originales. Se conservaron esos archivos y el resultado inicial de
la comprobación, sin modificar los repositorios vecinos.

Archivos principales:

- Red: `outputs/pilot_verified/pilot.net.xml`.
- Solicitudes y rutas: `requested.trips.xml`, `pilot.trips.xml`, `pilot.rou.xml`.
- Configuraciones: `base/pilot.sumocfg`, `repeat/pilot.sumocfg`.
- Salidas: `tripinfo.xml`, `statistics.xml`, `summary.xml`, `collisions.xml` en cada corrida.
- Resumen y auditoría: `summary.json`, `routing_audit.json`, `network_audit.json`,
  `osm_audit.json`, `warnings.json`, `reproducibility.json`.
- Procedencia: `manifest.json`, `environment.json`, `commands.json`, `ATTRIBUTION.txt`.
- Instalación, diagnóstico y verificación adicional: `outputs/intervention002/`.

Para repetir el proceso completo en un directorio nuevo:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.pilot --output outputs/pilot_reproduction
```

La [receta](../scenarios/pilot/README.md) explica requisitos, rutas y verificaciones.

## F. Recomendación para la intervención 003

1. Definir la red y sus entradas/salidas del corredor; explicar los 29 enlaces
   de componentes menores y los 41 OD rechazados, sin forzar conexiones a
   través de barreras o accesos privados. Ampliar el recorte solo si resuelve
   movimientos concretos que cruzan su borde.
2. Revisar geometrías y las advertencias de giros, velocidades y semáforos;
   fijar supuestos de carriles y capacidad con trazabilidad por enlace.
3. Crear una demanda sintética explícita por entrada y movimiento para evaluar
   el escenario base, conservando el caso aleatorio como prueba de regresión.
4. Diseñar la caracterización de conteos, ubicación de sensores y registros
   fase–movimiento antes de calibrar. Cualquier adquisición real requiere su
   propio alcance autorizado. No iniciar CTM, LTM o IA como consecuencia
   automática de este resultado.

Datos: **© OpenStreetMap contributors**, procesados por **Geofabrik GmbH**,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
No se simularon cierres ni se incorporaron observaciones reales; tampoco se
operó infraestructura física.
