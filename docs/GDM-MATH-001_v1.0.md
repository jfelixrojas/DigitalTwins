# GDM-MATH-001 — Contrato de notación matemática

**Versión:** 1.0  
**Proyecto:** DigitalTwins — Gemelo Digital de Movilidad Urbana (El Salvador)  
**Estado:** Referencia normativa para las implementaciones y los experimentos  
**Ubicación propuesta:** `DigitalTwins/docs/GDM-MATH-001_v1.0.md`  
**Alcance:** modelos de tráfico, estimación de estado, observación, simulación y análisis de resultados.

> **Propósito.** Consolidar las definiciones matemáticas acordadas durante el diseño del gemelo digital y evitar cambios silenciosos de símbolo, significado, índice o unidad entre documentos, código, simulaciones y resultados. Esta versión **no selecciona** un motor definitivo, ni convierte una simulación sintética en una observación del tráfico real.

## 1. Reglas obligatorias

1. Un símbolo conserva su **significado físico**. Un modelo puede añadir índices y subíndices, pero debe documentarlos; no puede redefinir símbolos reservados.
2. Toda variable física debe declarar **unidad**, intervalo de referencia, ámbito espacial y si corresponde a un **dato observado, estado estimado, variable simulada o parámetro supuesto/calibrado**.
3. El índice temporal `t` es **discreto**: denota el inicio de un intervalo de duración `Δt`; no denota por sí mismo segundos transcurridos. Las cantidades `A_t`, `D_t`, `S_t`, `F_{i→j,t}`, `E_{i,t}` y `B_{i,t}` corresponden a **vehículos por intervalo**, no a tasas en vehículos/hora.
4. Las tasas `q_t`, `s`, `c` y `q_i^{max}` se expresan en **veh/h** salvo que se declare expresamente una tasa por carril. No se suman tasas con cantidades sin conversión dimensional.
5. Se conservan las restricciones de **conservación, capacidad, almacenamiento, conectividad y no negatividad**. Cualquier relajación o aproximación debe quedar explícita.
6. CTM y LTM pueden usar **representaciones internas diferentes**; las comparaciones emplearán métricas y condiciones de frontera equivalentes.
7. El laboratorio de simulación está aislado de la infraestructura real. Las entradas semafóricas `u_t` describen **controles registrados o virtuales**, nunca comandos autorizados hacia controladores físicos.
8. Los datos de conteos, operación semafórica y Waze no implican por sí mismos observabilidad completa. La procedencia y la incertidumbre son parte del resultado.
9. Una extensión que cambie las definiciones normativas requiere una **nueva versión del contrato**; no se modifica silenciosamente la v1.0.

## 2. Tiempo, movimiento y variables de tráfico

| Símbolo | Definición estable | Unidad | Comentario |
|---|---|---|---|
| `t` | Índice de tiempo discreto | adimensional | El intervalo es `[tΔt,(t+1)Δt)` en el reloj relativo de simulación. |
| `Δt` | Duración del paso de simulación o agregación | s | Debe declararse y mantenerse consistente en el experimento. |
| `Q_t` | Vehículos en **cola** al inicio del intervalo | veh | No equivale necesariamente a la ocupación total de una celda. |
| `A_t` | Vehículos que **llegan** a la cola durante el intervalo | veh | Cantidad, no tasa. |
| `D_t` | Vehículos que **salen efectivamente** de la cola durante el intervalo | veh | Descarga realizada; no confundir con capacidad. |
| `S_t` | **Capacidad máxima de servicio** disponible para ese movimiento e intervalo | veh | Puede no utilizarse en su totalidad. |
| `s` | Flujo de saturación de un movimiento | veh/h | Debe aclararse si es total o por carril. |
| `g_t` | Duración de verde **efectivo** de un movimiento dentro del intervalo considerado | s | `0 ≤ g_t ≤ Δt` si el intervalo es un paso; para un ciclo completo, `Δt=C`. |
| `C` | Duración del ciclo semafórico | s | Solo para formulaciones por ciclo. |
| `c` | Capacidad **media temporal** del movimiento | veh/h | No es la capacidad en vehículos de un paso. |
| `q_t` | Flujo vehicular | veh/h | Minúscula; no es cola. |
| `k_t` | Densidad vehicular | veh/km | Agregada para la sección definida; declarar si es por carril. |
| `v_t` | Velocidad media espacial del tráfico | km/h | Asociada a `q_t` y `k_t` compatibles. |

### 2.1. Conservación de la cola (ecuación canónica)

$$
\boxed{Q_{t+1}=Q_t+A_t-D_t}
$$

Restricciones mínimas:

$$
Q_t\ge 0,\qquad A_t\ge 0,\qquad 0\le D_t\le Q_t+A_t,\qquad D_t\le S_t.
$$

En una cola simplificada **sin bloqueo aguas abajo**, con vehículos que llegan disponibles para servicio durante el intervalo y suficiente oportunidad temporal para descargarlos:

$$
D_t=\min(Q_t+A_t,S_t).
$$

Solo **bajo esas hipótesis** se deduce:

$$
Q_{t+1}=\max(0,Q_t+A_t-S_t).
$$

Esta forma derivada **no sustituye** la ecuación canónica ni convierte `D_t` y `S_t` en sinónimos. Si hay cola aguas abajo, llegadas tardías o restricciones de movimiento, la descarga efectiva debe calcularse de acuerdo con esas condiciones.

### 2.2. Relación entre servicio y semáforo

Si `s` está expresado en veh/h y `g_t` en segundos de verde efectivo:

$$
\boxed{S_t=s\,\frac{g_t}{3600}} \qquad [\mathrm{veh}].
$$

Si se describe un ciclo completo de duración `C`, con verde efectivo `g` del movimiento por ciclo, la capacidad media es:

$$
\boxed{c=s\,\frac{g}{C}} \qquad [\mathrm{veh/h}].
$$

**Condición:** estas son aproximaciones macroscópicas de servicio. Un verde efectivo no garantiza descarga real si no hay vehículos disponibles o la vía receptora está bloqueada.

### 2.3. Relación fundamental básica

Para flujo, densidad y velocidad definidos sobre la **misma sección y el mismo agregado de carriles**:

$$
\boxed{q_t=k_t\,v_t}.
$$

Con `k_t` en veh/km y `v_t` en km/h, `q_t` está en veh/h. Si la densidad se expresa por carril, el flujo compatible también debe expresarse por carril, o debe agregarse explícitamente.

## 3. Variables generales del gemelo y de la estimación

| Símbolo | Definición estable | Unidad / naturaleza |
|---|---|---|
| `x_t` | Vector de **estado físico** del sistema en `t` | Mixta; declarar cada componente. |
| `\hat{x}_t` | Estimación del vector de estado | Mismas unidades que `x_t`. |
| `y_t` | Vector de **observaciones** disponibles en `t` | Según el sensor o fuente. |
| `u_t` | Entradas de control **registradas o virtuales** (por ejemplo, condiciones semafóricas) | Según la parametrización. |
| `d_t` | Entradas externas (por ejemplo, demanda) | Según la parametrización. |
| `\theta` | Parámetros físicos/estadísticos del modelo | Declarar unidades y procedencia. |
| `G` | Red vial dirigida y sus atributos, en el alcance declarado | Estructura topológica / geométrica. |
| `f_\theta` | Función de evolución dinámica del estado | Compatible con dimensiones de `x_t`. |
| `h_\theta` | Función de observación de variables del estado | Compatible con dimensiones de `y_t`. |
| `\omega_t` | Ruido o error del proceso dinámico | Unidades de `x_t`. |
| `\varepsilon_t` | Error de observación | Unidades de `y_t`. |
| `P_t` | Covarianza del error del **estado estimado** | Unidades de productos de componentes de `x_t`. |
| `R_t` | Covarianza del **error de observación** | Unidades de productos de componentes de `y_t`. |
| `\Omega_t` | Covarianza del **ruido de proceso** | Unidades de productos de componentes de `x_t`. |

Formulación general acordada (la red se muestra como argumento fijo de contexto):

$$
\boxed{x_{t+1}=f_\theta(x_t,u_t,d_t;G)+\omega_t}
$$

$$
\boxed{y_t=h_\theta(x_t)+\varepsilon_t}
$$

Cuando la observación dependa además de control, geometría, demanda o variables exógenas, se **documentará una extensión explícita de la firma de `h_\theta`**, manteniendo su significado como función de observación.

**Nota anti-colisiones:** `Q_t` sigue siendo **cola vehicular**; nunca se reutiliza para la covarianza del proceso. Esta última es `\Omega_t`. `R_t` es covarianza de observación, no una capacidad de recepción CTM.

Si se introduce un filtro de Kalman, `K_t` se reservará para su **ganancia**, y no se confundirá con `k_t` (densidad). En el caso escalar, con varianza previa `P_t^-` y varianza de observación `R_t`:

$$
K_t=\frac{P_t^-}{P_t^-+R_t}.
$$

La ecuación requiere un modelo de observación escalar directo y varianzas compatibles; no es una fórmula universal para cualquier observación de tráfico.

## 4. Ampliación CTM ya introducida durante las clases

Esta sección consolida símbolos **ya utilizados** en la explicación del Cell Transmission Model; no redefine la notación de colas.

| Símbolo | Definición estable | Unidad |
|---|---|---|
| `i,j` | Identificadores de celdas; una flecha `i→j` indica sentido permitido | adimensional |
| `n_{i,t}` | **Ocupación total** de la celda `i` al inicio de `t` | veh |
| `N_i` | Almacenamiento máximo de la celda `i` | veh |
| `F_{i\to j,t}` | Transferencia **efectiva** de `i` a `j` durante el intervalo | veh |
| `\Phi_i` | Cantidad máxima transferible de la celda `i` por intervalo | veh |
| `E_{i,t}` | Cantidad máxima que la celda `i` puede **enviar** | veh |
| `B_{i,t}` | Cantidad máxima que la celda `i` puede **recibir** | veh |
| `v_i^f` | Velocidad libre del tramo asociado a la celda | km/h |
| `w_i` | **Magnitud positiva** de velocidad de propagación de ondas congestionadas hacia atrás | km/h |
| `\Delta z_i` | Longitud de la celda | km |
| `\alpha_i` | Fracción de longitud de celda recorrible a velocidad libre durante `Δt` | adimensional |
| `\beta_i` | Factor de propagación de disponibilidad de espacio en la rama congestionada | adimensional |
| `k_i^{jam}` | Densidad de atasco del tramo | veh/km; aclarar agregado de carriles |
| `k_i^{crit}` | Densidad crítica del tramo | veh/km; mismo agregado |
| `q_i^{max}` | Capacidad de flujo del tramo | veh/h; mismo agregado |
| `\ell_i` | Número de carriles equivalentes en la sección | carriles |

### 4.1. Conservación por celda

Para una celda interior de un corredor unidireccional **sin accesos laterales**:

$$
\boxed{n_{i,t+1}=n_{i,t}+F_{i-1\to i,t}-F_{i\to i+1,t}}.
$$

Para redes, bifurcaciones y accesos laterales se utiliza el balance general:

$$
\boxed{n_{i,t+1}=n_{i,t}+\sum_{j:\,j\to i}F_{j\to i,t}-\sum_{j:\,i\to j}F_{i\to j,t}}
$$

sumando también las transferencias de frontera en la medida en que se representen explícitamente. Siempre debe cumplirse `0 ≤ n_{i,t} ≤ N_i`.

### 4.2. Envío, recepción y transferencia

Para el CTM de corredor y la discretización indicada:

$$
\boxed{E_{i,t}=\min(\alpha_i n_{i,t},\Phi_i)}
$$

$$
\boxed{B_{i,t}=\min\bigl(\Phi_i,\beta_i(N_i-n_{i,t})\bigr)}
$$

$$
\boxed{F_{i\to i+1,t}=\min(E_{i,t},B_{i+1,t})}.
$$

Las relaciones de coeficientes son:

$$
\alpha_i=\frac{v_i^f\Delta t}{3600\,\Delta z_i},\qquad
\beta_i=\frac{w_i\Delta t}{3600\,\Delta z_i}.
$$

Para esta formulación explícita, elegir paso y celda para mantener `0 ≤ α_i ≤ 1` y `0 ≤ β_i ≤ 1`, junto con las hipótesis numéricas aplicables.

**El caso clásico** `Δz_i = v_i^f Δt/3600` implica `α_i=1`. Esto **no** representa un carril, un vehículo ni una restricción de paso «uno a uno»: representa la relación entre distancia recorrida a velocidad libre y longitud de celda. El límite de vehículos transferidos sigue siendo `\Phi_i` y/o la recepción aguas abajo.

En un movimiento individual sujeto a semáforo, **si `S_t` está definido para ese mismo movimiento e intervalo**:

$$
F_{i\to i+1,t}=\min(E_{i,t},B_{i+1,t},S_t).
$$

Cuando existan múltiples movimientos, las capacidades de giros y carriles compartidos deben resolverse con un modelo de nodo; **no basta** con aplicar mínimos independientes que puedan violar restricciones conjuntas.

**Orientación física:** `min(E_{i,t},B_{i+1,t})=min(B_{i+1,t},E_{i,t})` algebraicamente, pero el envío de `i` y la recepción de `i+1` **no intercambian papeles ni sentidos viales**.

### 4.3. Diagrama fundamental triangular

Para una vía homogénea con velocidades positivas `v^f` y `w` (esta última es la **magnitud** de la onda hacia atrás):

$$
q(k)=\min\bigl(v^f k,\;w(k^{jam}-k)\bigr).
$$

El encuentro de sus ramas fija:

$$
k^{crit}=\frac{w k^{jam}}{v^f+w},\qquad
q^{max}=v^f k^{crit}.
$$

Para la celda `i`, usando **densidad agregada para todos los carriles representados**:

$$
N_i=k_i^{jam}\Delta z_i,\qquad
\Phi_i=q_i^{max}\frac{\Delta t}{3600}.
$$

Si la densidad y capacidad disponibles son **por carril**, utilizar explícitamente `\ell_i`:

$$
N_i=k_{i,\mathrm{carril}}^{jam}\Delta z_i\ell_i,\qquad
\Phi_i=q_{i,\mathrm{carril}}^{max}\frac{\Delta t}{3600}\ell_i.
$$

**Hipótesis constitutiva:** el diagrama triangular no es una ley universal de tráfico. Sus parámetros requieren calibración y sus ramas representan una aproximación macroscópica. Si se añade una capacidad independiente menor que la intersección de las dos ramas, la curva resultante podría tener una meseta y **ya no sería estrictamente triangular**.

## 5. Restricciones de modelos y observaciones

- **CTM:** las celdas tienen ocupaciones y transferencias; `n_{i,t}` no se renombra como `Q_t` sin demostrar que la ocupación corresponde a una cola definida de manera explícita.
- **LTM:** representa enlaces, flujos acumulados y sus condiciones de frontera; al introducir su notación específica, declarar símbolos nuevos sin reutilizar los reservados. Comparar resultados CTM/LTM por flujos, acumulaciones, demoras y otras medidas espacial y temporalmente compatibles.
- **SUMO:** es el simulador microscópico del laboratorio inicial; **no es**, por sí mismo, una implementación de CTM/LTM ni validación del tráfico real.
- **GNN/híbridos:** los símbolos de tensores, capas y pesos se documentarán en anexos de modelo; no se reutilizarán `Q_t`, `D_t`, `S_t`, `E_{i,t}`, `B_{i,t}` o `R_t` para pérdidas, embeddings o parámetros de aprendizaje.
- **Waze, conteos, semáforos:** cualquier transformación hacia `y_t` debe especificar operador espacial, alineación temporal, unidades, filtros, cobertura y error de medición. La ausencia de dato no equivale automáticamente a flujo libre.
- **Cierres y cambios de ruta:** conservación y cambio de capacidad no generan por sí solos reasignación de viajes; las reglas de demanda, giros y elección de rutas son hipótesis separadas.
- **Simulación vs. verdad:** distinguir siempre `observado`, `estimado`, `simulado`, `sintético` y `supuesto`. Una salida del simulador no es una medición real.

## 6. Invariantes comprobables para Codex

Cada implementación y experimento debe disponer de pruebas o verificaciones que cubran, según proceda:

1. **Dimensiones:** no mezclar veh con veh/h, segundos con horas o densidades por carril con totales.
2. **Conservación:** `Q_{t+1}−Q_t=A_t−D_t`; para celdas, cambio de ocupación igual a entradas menos salidas; balance agregado con entradas y salidas externas explícitas.
3. **Factibilidad:** no negatividad; `D_t ≤ min(Q_t+A_t,S_t)` bajo el modelo de cola; `F_{i→j,t}` limitado por envío y recepción, y por semáforo cuando corresponda.
4. **Almacenamiento:** ocupaciones CTM en `[0,N_i]` después de cada paso; explicar tolerancias numéricas si se usan valores reales agregados.
5. **Sentido:** el operador `min` es conmutativo, pero `i→j` es dirigido; no inventar giros, accesos o trayectos inversos.
6. **Reproducibilidad:** conservar versión del motor, malla, `Δt`, topología, parámetros, condiciones iniciales, semillas y fuentes.
7. **Validación:** separar calibración de evaluación independiente; documentar el carácter sintético de los primeros pilotos SUMO.
8. **Seguridad de alcance:** el laboratorio no emite órdenes ni escrituras a controladores semafóricos reales.

### Ejemplos de control

**Cola:** `Q_t=7`, `A_t=16`, `S_t=12` y, bajo servicio simplificado sin bloqueo, `D_t=min(23,12)=12`; por conservación, `Q_{t+1}=11` vehículos. Si solo hay cinco vehículos disponibles y `S_t=12`, entonces `D_t=5`, **no 12**.

**CTM:** si `E_{1,t}=9` y `B_{2,t}=4`, entonces `F_{1→2,t}=4`; no se han transferido nueve vehículos aunque la primera celda pueda enviarlos.

**Paso libre:** con `v_i^f=36 km/h`, `Δt=10 s`, `Δz_i=0,1 km`, resulta `α_i=1` independientemente del número de carriles.

## 7. Gobernanza del contrato

- **Archivo canónico:** `docs/GDM-MATH-001_v1.0.md`.
- **Precedencia:** cuando un ejemplo de documentación o una variable de código contradiga este contrato, la inconsistencia debe señalarse y corregirse; **no se redefine silenciosamente el contrato**.
- **Versionado:** cambios de significado o unidades requieren nueva versión y nota de migración; ejemplos nuevos y glosarios auxiliares pueden documentarse aparte sin cambiar símbolos reservados.
- **Instrucción para Codex:** antes de incorporar CTM, LTM, filtros, GNN o nuevas métricas, verificar nombres, unidades, índices y fórmulas contra este archivo. Añadir pruebas para toda relación de conservación o capacidad implementada.

**Fin de GDM-MATH-001 v1.0.**
