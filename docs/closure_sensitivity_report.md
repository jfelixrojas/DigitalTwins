# Intervención 005 — sensibilidad temporal del primer cierre

El incremento original de **+405 s (+2,03 %)** es sensible a la configuración
temporal. En los 15 pares evaluados, el cambio de tiempo total va de **−19 a
+405 s**: 14 aumentos y una reducción. La mediana de los cambios entre diseños
es +248 s; el porcentaje mediano es +1,27 %. El efecto directo W_E resulta
más estable: su mediana individual aumenta entre **14 y 16 s en los 15 pares**.

Los dos vehículos N_E que antes registraron +88 y +90 s solo vuelven a superar
el umbral de +60 s en la combinación original. Otros vehículos N_E también
presentan episodios grandes, de ambos signos. No hay evidencia para considerar
el +2,03 % un efecto fijo del cierre ni para atribuir todos los retrasos a
saturación. Son resultados sintéticos, sin calibración operacional.

Todos los productos están en `outputs/closure_sensitivity/`:
[matriz](../outputs/closure_sensitivity/matrix_comparison.csv),
[descriptivos](../outputs/closure_sensitivity/summary.json),
[manifiesto](../outputs/closure_sensitivity/manifest.json),
[repetición](../outputs/closure_sensitivity/reproducibility.json) y
[validación final](../outputs/closure_sensitivity/audit/final_validation.json).

## Diseño y reproducción del punto original

Antes de generar las perturbaciones se reprodujo la base y el cierre de la
004 usando sus configuraciones y módulos sin cambios. Se recuperaron
**19 935 s en base, 20 340 s con cierre y +405 s de diferencia**. Coincidieron
todos los atributos por vehículo, intervalos de enlaces y series temporales
salvo tiempo de CPU. [Verificación previa](../outputs/closure_sensitivity/audit/regression004/validation.json).

Se reutilizó la misma red SUMO; no hubo extracción ni reconstrucción de OSM.
El tratamiento sigue siendo la prohibición de `passenger` en ambos carriles de
`1257993561#5` durante [0, 1800) s, con el rerouter en `198404000` y modo 8
documentados en la 004. Se conservaron reglas de conducción, destinos, tipos,
identificadores y cantidades de los seis movimientos. Semilla SUMO **42**,
paso **1 s**, horizonte **1800 s** y agregación de enlaces **60 s** en todos
los pares. No hay cambios de semilla del simulador entre combinaciones.

La matriz contiene 30 corridas: cinco calendarios por tres offsets por dos
condiciones. Se repitió un par nuevo, añadiendo dos corridas. El comando
principal realiza esas **32 corridas**; las dos verificaciones previas de la
004 quedan separadas en `audit/`, sumando 34 en esta intervención. La repetición
no se cuenta como un diseño adicional.

## Calendarios de salida

El calendario original y su archivo de rutas se copiaron byte a byte. Los
otros cuatro usan `random.Random` con semillas 101, 102, 103 y 104 de Python
3.11. Cada salida es un segundo entero, a no más de ±15 s de la original.
Se conserva el orden estricto por movimiento y la ventana **0 ≤ salida < 900 s**.

Para cada vehículo, siguiendo el orden de movimientos de la especificación,
se sortea uniformemente dentro de:

```text
[max(0, salida_original − 15, salida_anterior_del_movimiento + 1),
 min(899, salida_original + 15)]
```

Esta restricción condiciona la distribución cerca de las fronteras y evita
inversiones de orden. No se supone ruido uniforme independiente sin esas
restricciones, ni se reemplazan solicitudes. El desplazamiento y el intervalo
factible de cada vehículo se conservan en `perturbations.json`.

| Calendario | Semilla temporal | Salidas modificadas | Primera / última salida (s) | Prefijo SHA-256 del calendario |
|---|---:|---:|---:|---|
| Original | — | 0 | 0 / 890 | `4ef49d9b118a` |
| J101 | 101 | 145 | 0 / 895 | `2dab6a0fbeb5` |
| J102 | 102 | 146 | 4 / 899 | `8bad5ac38199` |
| J103 | 103 | 144 | 3 / 893 | `c275de70a8cf` |
| J104 | 104 | 143 | 0 / 895 | `0448a3c69e38` |

Los cinco hashes completos son distintos y están en
[schedules_manifest.json](../outputs/closure_sensitivity/schedules_manifest.json),
junto a los hashes de las rutas. Cada calendario conserva 150 vehículos:
W_E 45, E_W 45 y 15 en cada uno de N_W, E_N, N_E y W_S. Cambian sus tiempos,
no sus OD ni atributos de conducción. Son diseños reproducibles, no muestras
independientes de tráfico real.

## Desfases semafóricos y comprobación efectiva

Se aplicaron desplazamientos globales adicionales de 0, 30 y 60 s respecto
de los offsets originales, normalizados módulo 90 s. Los 18 programas son
estáticos, con ciclos de 90 s. Se conservan ID, `programID`, estados, duraciones
de fases y diferencias relativas de offset entre controladores.

Se usó la modificación especial de offset de SUMO:

```xml
<tlLogic id="ID_EXISTENTE" programID="0" offset="30"/>
```

No se incluyen fases en la redefinición. Este mecanismo está descrito en
[Modifying Existing TLS-Programs](https://sumo.dlr.de/docs/Simulation/Traffic_Lights.html#modifying-existing-tls-programs).
Se comprobó en el SUMO **1.28.0 instalado**, no solo a partir del XML declarado.

La salida nativa
[`SaveTLSStates`](https://sumo.dlr.de/docs/Simulation/Output/Traffic_Lights.html)
registra cada segundo ID, programa, índice de fase y estado de conexiones.
Se contrastaron contra las fases originales y el reloj
`(tiempo − offset_original − desfase_adicional) mod 90`. Cada corrida de matriz
y repetición aporta **32 400 estados**, 18 por 1800 pasos: **1 036 800 registros
validados** en total. Las líneas de estados de base y cierre son idénticas
dentro de cada par. Así se descarta un desfase declarado pero ignorado.

Se añadieron FCD y registro de señales como instrumentación común. FCD añade
el token `fcd_<id>` a `tripinfo.devices`; solo ese token se retira para comparar
con la 004. La combinación original/0 reproduce todos los demás atributos,
agregados y métricas, incluido +405 s. No se alteraron módulos anteriores ni
se añadieron acciones de control real.

## Los 15 contrastes

Las diferencias son **cierre menos base**. Cada porcentaje utiliza el tiempo
total base de su propia combinación. Todos los pares tienen 150 solicitudes,
insertados y completados por condición, con cero rechazados, pendientes,
eliminados, teletransportes y colisiones. Se conservan las comprobaciones de
seguridad y los archivos nativos de cada corrida.

| Calendario | Extra (s) | Δ tiempo total (s) | Δ total (%) | Δ media W_E (s) | Δ mediana W_E (s) | Δ media N_E (s) |
|---|---:|---:|---:|---:|---:|---:|
| Original | 0 | +405 | +2,03 | +4,78 | +15 | +12,27 |
| Original | 30 | +211 | +1,06 | +4,71 | +16 | −0,07 |
| Original | 60 | +394 | +1,97 | +4,82 | +15 | +12,13 |
| J101 | 0 | +341 | +1,74 | +7,44 | +16 | +0,20 |
| J101 | 30 | +199 | +0,99 | +4,58 | +15 | −6,13 |
| J101 | 60 | +171 | +0,88 | +3,87 | +15 | −0,07 |
| J102 | 0 | +212 | +1,07 | +6,91 | +15 | −6,20 |
| J102 | 30 | +35 | +0,17 | +2,67 | +15 | −6,27 |
| J102 | 60 | +248 | +1,27 | +7,38 | +16 | −6,20 |
| J103 | 0 | **−19** | **−0,10** | +5,56 | +15 | −12,07 |
| J103 | 30 | +205 | +1,04 | +6,89 | +16 | −6,27 |
| J103 | 60 | +308 | +1,57 | +6,73 | +16 | −0,13 |
| J104 | 0 | +404 | +2,11 | +7,38 | +16 | −0,27 |
| J104 | 30 | +263 | +1,36 | +7,80 | +16 | −6,13 |
| J104 | 60 | +273 | +1,40 | +4,27 | +14 | +0,13 |

![Matriz de diferencias](../outputs/closure_sensitivity/visual/total_time_matrix.png)

La tabla estructurada conserva además los tiempos absolutos, medias, mediana,
P05 y P95 de impactos individuales, `waitingTime`, `timeLoss`, longitud,
pendientes y máximos simultáneos. Las comparaciones por vehículo y enlace se
conservan por separado en cada carpeta de combinación.

## Robustez global, directa e indirecta

| Descriptivo de los 15 diseños | Δ tiempo total |
|---|---:|
| Media | +243,33 s |
| Mediana | +248 s |
| Desviación típica, divisor 15 | 119,04 s |
| Mínimo / máximo | −19 / +405 s |
| Amplitud | 424 s |
| P25 / P75 | +202 / +324,5 s |
| Pares que aumentan / reducen / no cambian | 14 / 1 / 0 |

El porcentaje medio es +1,24 %, el mediano +1,27 % y el rango
**−0,096 % a +2,114 %**. El original +405 s es el máximo absoluto de esta
matriz; su +2,03 % está en la zona alta, sin ser el mayor porcentaje porque
los denominadores base varían. No representa la magnitud central observada.
Estos son descriptivos de una cuadrícula finita, sin intervalos de confianza
ni extrapolación poblacional.

**W_E:** las 15 medias de impacto son positivas, entre +2,67 y +7,80 s; las
medianas van de +14 a +16 s. El perjuicio mediano directo es consistente dentro
de este dominio temporal, aunque algunos vehículos individuales se benefician.
Los 45 W_E usan el mismo desvío de la 004: 35 Avenida Sur y Calle el Progreso,
con +105,55 m por viaje. El aumento medio de longitud de toda la red permanece
en +31,665 m. Distancia adicional no equivale por sí sola a congestión.

![Medias y medianas W_E](../outputs/closure_sensitivity/visual/WE_means_and_medians.png)

**Otros movimientos:** el tiempo total indirecto varía entre −269 y +190 s.
En J103/0, W_E suma +250 s, pero los otros movimientos restan 269 s, dando
−19 s de red. Los rangos de cambios medios por movimiento son:

| Movimiento | Mínimo / máximo de Δ media de recorrido (s) |
|---|---:|
| E_W | −1,87 / +1,80 |
| N_W | −0,20 / +0,40 |
| E_N | −0,40 / +0,33 |
| N_E | −12,07 / +12,27 |
| W_S | −0,40 / +0,20 |

![Distribuciones por movimiento](../outputs/closure_sensitivity/visual/movement_impact_distributions.png)

La figura agrupa 2250 diferencias vehículo-combinación con IDs repetidos;
no las interpreta como 2250 observaciones independientes. Los episodios grandes
de N_E, y algunos de E_W, pueden quedar ocultos en promedios cercanos a cero.

En todos los pares bajan `waitingTime` medio (entre −4,10 y −1,99 s) y
`timeLoss` medio (−3,21 a −0,42 s). Ello no convierte en mejoras los 14 aumentos
del tiempo total. Son medidas solapadas, reportadas por separado.

### Separación de las dos sensibilidades

Con **cronograma fijo**, cambiar únicamente el desfase cambia el impacto total
en 141–327 s según el calendario. El original pasa de +405 a +211 y +394 s.
Con J103 pasa de −19 a +205 y +308 s: la señal del resultado global puede
cambiar sin alterar ese calendario.

Con **desfase fijo**, la variación entre cronogramas abarca 424 s para +0,
228 s para +30 y 223 s para +60. Las medias sobre los cinco calendarios son
+268,6, +182,6 y +278,8 s, respectivamente. +30 tiene menor media en este
conjunto, pero esto no lo convierte en una coordinación óptima: no se realizó
optimización ni se evaluó desempeño operacional real.

![Sensibilidades separadas](../outputs/closure_sensitivity/visual/variability_summary.png)

Los efectos dependen de la combinación de factores; no se propone un único
coeficiente aditivo para horario y offset. Las líneas comparan diseños
equivalentes y los calendarios nuevos conservan cantidades y OD.

## Los dos casos N_E y la evidencia temporal

Se fijó antes de las corridas una demora adicional elevada como
**Δ duración individual ≥60 s**. Cada uno de los dos IDs cumple esa condición
en **1 de 15 combinaciones**, exclusivamente original/0; en las otras 14 no
reaparecen sus +88/+90 s.

| ID | Δ en original/0 | Mediana de Δ entre diseños | Rango de Δ | Combinaciones ≥+60 s |
|---|---:|---:|---:|---:|
| `N_E.0007` | +88 s | −1 s | −3 a +88 s | 1/15 |
| `N_E.0013` | +90 s | 0 s | **−90 a +90 s** | 1/15 |

Se conserva una fila por ID y combinación en
[NE_cases.csv](../outputs/closure_sensitivity/NE_cases.csv). Las trayectorias
FCD y `NE_intersection_events.csv` permiten contrastar posición, velocidad,
salidas de enlaces y señales. Para el análisis focal se define como aproximación
el conjunto `398538074`, `1182057749` y `1182057747`; su primera muestra no
equivale a una cola física ni a una llegada exacta a la línea de detención.

En original/0, ambos escenarios muestran la primera aproximación en **476 s**
para `0007` y **836 s** para `0013`, con verde en la conexión 0 de `4011718406`.
Sin embargo, la salida del enlace de entrada `1182057747` pasa de 480 a 540 s
y de 840 a 900 s. Cada vehículo acumula 57 muestras de velocidad ≤0,1 m/s
en la aproximación del cierre: **9 con verde, 3 con amarillo y 45 con rojo**.
El paso posterior coincide con el inicio de un nuevo verde.

Existe asociación temporal entre detención y espera durante rojo, pero la
detención comienza con verde. No es suficiente atribuirla únicamente a llegar
a un rojo, a saturación del desvío o a la coordinación. Permanecen abiertas
las interacciones de carril/nodo y la sensibilidad de segmentos muy cortos.
Las señales y los verdes no cambiaron dentro de esos pares.

Con +60 s, los mismos IDs esperan durante rojo en ambos escenarios y salen
de la entrada en los mismos instantes: 510 s y 870 s; sus impactos finales son
0 y +1 s. Con J103/0, `N_E.0013` invierte el caso: −90 s. Cambiar horarios
del conjunto puede cambiar interacciones aun cuando la primera aproximación
del vehículo focal coincida.

![Evolución de los casos focales](../outputs/closure_sensitivity/visual/NE_temporal_cases.png)

La figura selecciona la combinación original, la de mayor retraso conjunto de
estos dos IDs entre las otras y una de impacto conjunto mínimo; el criterio
exacto está guardado. Su fondo muestra solo una señal, no todas las que
atraviesa el vehículo. Los eventos por intersección incluyen los otros
controladores y la resolución temporal es de 1 s.

Considerando **todos los N_E**, hay cinco diferencias ≥+60 s en tres
combinaciones, todas con el calendario original; se desplazan a otros IDs
con offsets +30 y +60. También hay nueve diferencias ≤−60 s en ocho
combinaciones. Por ello, los dos IDs originales son casos excepcionales,
mientras que los episodios temporales grandes del movimiento pueden cambiar
de vehículo y signo. [Recuento verificable](../outputs/closure_sensitivity/audit/NE_all_vehicles.json).

## Flujos, ocupación y contabilidad

Cada cierre desvía 45 vehículos por cada uno de `-175606174` y `-198404021`,
frente a cero en su base. Los máximos por intervalo de 60 s varían entre
240 y 360 veh/h en ambos enlaces. La ocupación máxima de cada corrida varía
entre 3,71–5,95 % en 35 Avenida Sur y 3,02–5,50 % en Calle el Progreso.
Son valores nativos del experimento, sin validación de capacidad física.

Los máximos simultáneos de red van de 25 a 27 veh en las bases y de 28 a 30
con cierre. Se conservan flujos, ocupación y vehículos medios por enlace e
intervalo, y la serie `summary.running` para acumulación total. Se verifica
en cada paso el balance de vehículos y, al completarse todos, la igualdad
entre la integral temporal de vehículos en red y el tiempo total de viaje.

Las entradas por período son cantidades en veh; los flujos se convierten a
veh/h. Ocupación porcentual, vehículos medios y vehículos detenidos son
indicadores distintos. Conforme a GDM-MATH-001, no se renombran como cola
`Q_t` ni como estado de celda CTM `n_{i,t}`. No se suman porcentajes de enlaces.

## Validación, reproducción y alcance

Se comprobaron conservación de IDs, OD, tipos, horarios y conducción; rutas
originales y alternativas ya validadas estrictamente en la 004; movimientos
ejecutados; estados semafóricos efectivos; permisos de todos los carriles en
las instantáneas de control; y ausencia de pasos por el enlace cerrado en
las 16 corridas de cierre de matriz y repetición.

La repetición de **J101/+30** coincide en ambos escenarios en todos los
atributos `tripinfo`, intervalos de enlaces, series temporales salvo CPU,
señales, trayectorias FCD y muestras de permisos. No se agrega al resumen
descriptivo. Pasan **33 pruebas**, las 25 anteriores y ocho nuevas sobre
calendarios, offsets, estados efectivos y conteos descriptivos.

Los archivos experimentales anteriores, las cuatro fuentes y los repositorios
vecinos se verifican mediante los inventarios y hashes en `audit/`. Los cambios
de `.DS_Store` se registran aparte como metadatos del sistema, sin relajar
comparaciones de contenido científico. El resultado exacto está en
[final_validation.json](../outputs/closure_sensitivity/audit/final_validation.json).
No se modificó código de las intervenciones 002–004 ni sus evidencias.

Comando único para una salida nueva:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.sensitivity --output outputs/closure_sensitivity_reproduction
```

La [receta](../scenarios/closure_sensitivity/README.md) describe insumos y
condiciones. Se utilizan SUMO/TraCI 1.28.0, Python 3.11 y Matplotlib/NumPy ya
instalados, con puerto local temporal. No hubo instalaciones ni adquisición
de datos. El manifiesto conserva versiones, hashes de calendarios, offsets,
código, entradas y productos. Se revisaron cinco figuras PNG/SVG; un ajuste
de margen de leyenda se regeneró desde las mismas tablas, sin repetir ni
modificar simulaciones, conservando su procedencia previa en `audit/`.

Se añadieron tres módulos `sensitivity*`, un escenario, ocho pruebas y este
informe; se actualizaron README y documentación de pruebas. No se eliminaron
archivos previos. [Inventario de cambios](../outputs/closure_sensitivity/audit/changes.json).

## Qué queda respaldado y qué sigue abierto

Está respaldada la reproducibilidad técnica y, dentro de esta cuadrícula,
un aumento mediano directo W_E. El efecto agregado tiende a empeorar, pero
su magnitud es sensible y su signo no es universal. No queda respaldado usar
+2,03 % como efecto típico, ni una explicación única de los episodios N_E.

**Se puede avanzar a sensibilidad de demanda como experimento sintético**,
conservando la dimensión temporal: comparar niveles de carga con los mismos
calendarios/offsets entre base y cierre de cada par, registrar completados y
pendientes, y mantener visibles los impactos por movimiento. No conviene
escalar únicamente el caso original ni interpretar sus porcentajes como
predicción operacional. Las interacciones que generan detenciones con verde
merecen diagnóstico adicional si se buscan conclusiones físicas.

No hay calibración, conteos, Waze ni semáforos reales. Los parámetros inferidos
de velocidades, carriles y geometría de las intervenciones anteriores siguen
limitando la interpretación. No se implementaron CTM, LTM, GNN, servicios ni
dashboard, y no se accedió a infraestructura real.

Datos derivados: **© OpenStreetMap contributors / Geofabrik**,
[ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Se conserva atribución
con los productos.
