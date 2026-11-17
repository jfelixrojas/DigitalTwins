# Sensibilidad temporal del cierre — intervención 005

Matriz de cinco cronogramas por tres desfases globales adicionales, con el
mismo cierre efectivo de `1257993561#5`. Usa SUMO 1.28.0 y los módulos de la
004 sin modificarlos. Los resultados son sintéticos y descriptivos.

Desde la raíz del proyecto:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.sensitivity --output outputs/closure_sensitivity
```

La salida debe ser nueva; se admite un directorio que contenga exclusivamente
`audit/`, para conservar las verificaciones previas. El ejecutor rechaza una
matriz ya iniciada o terminada. Para repetir el conjunto conservando el actual:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.sensitivity --output outputs/closure_sensitivity_reproduction
```

Se requieren los insumos verificados de la 004 y la red OSM de referencia de
la 002, el SUMO/TraCI instalado, Matplotlib y NumPy existentes. Se comprueban
hashes y versiones. No hay instalaciones ni adquisición de datos. El proceso
necesita permiso para los sockets TraCI locales temporales.

[experiment.json](experiment.json) fija:

- Cronograma original, copiado byte a byte, y semillas temporales 101–104.
- Perturbaciones enteras de hasta ±15 s, manteniendo 150 IDs, OD y atributos.
  Para cada movimiento, en el orden de la especificación original, se toma una
  salida uniforme del intervalo factible `[max(0, original−15, anterior+1),
  min(899, original+15)]`. La restricción condiciona la distribución cerca de
  las fronteras y evita inversiones; no es ruido uniforme independiente sin
  restricciones. Los sorteos usan `random.Random(seed)` de Python 3.11.
- Desfases adicionales 0, 30 y 60 s. Cada `tlLogic` adicional conserva `id` y
  `programID`, declara `(offset_original + extra) mod 90` y no contiene fases.
- Semilla SUMO siempre 42, paso 1 s y horizonte 1800 s. El desfase y la demanda
  son idénticos dentro de cada par; solo difieren cierre y reruteo necesario.
- Demora individual elevada: incremento emparejado de duración **≥60 s**.

Se ejecuta primero original/0 y se exige recuperar +405 s, antes de generar
los otros calendarios. Se completan 30 corridas de matriz y dos corridas de
repetición para `jitter101_offset030`. La repetición no se agrega como una
combinación adicional en los descriptivos.

Se conservan configuraciones, calendarios con hashes, rutas ejecutadas,
contabilidad y agregados de enlaces. `SaveTLSStates` escribe los estados de
los 18 semáforos cada segundo; se contrastan con los programas y offsets y
entre base/cierre. `fcd-output` conserva trayectorias nativas, sin modificar la
conducción. Sus dispositivos añaden tokens `fcd_<id>` a `tripinfo.devices`;
solo esos tokens se retiran para la regresión con la 004.

Los dos vehículos N_E tienen trayectorias extraídas y eventos por intersección.
La aproximación de referencia es el conjunto de enlaces `398538074`,
`1182057749` y `1182057747`; su primera muestra no equivale a llegar a una cola
física. Las trayectorias y estados tienen resolución de 1 s.

Los archivos principales son `matrix_comparison.csv`, `movement_comparison.csv`,
`NE_cases.csv`, `summary.json`, `schedules_manifest.json`, `manifest.json` y
`reproducibility.json`. Cada carpeta de combinación conserva comparaciones
por vehículo y enlace, señales, FCD y validación. Hay cinco figuras PNG/SVG.
Ver el [informe](../../docs/closure_sensitivity_report.md).
