# Escenario base controlado — intervención 003

Experimento microscópico sintético sobre la red verificada de Alameda Franklin
Delano Roosevelt, San Salvador. La red, los atributos y los programas
semafóricos se conservan. No se ejecuta ningún cierre ni se integran observaciones.

Desde la raíz de `DigitalTwins`, con Python 3.11, SUMO 1.28.0 y los paquetes
Matplotlib/PyProj existentes:

```sh
PYTHONPATH=src python3 -B -m digitaltwins.controlled --output outputs/pilot_controlled_reproduction
```

La salida debe ser un directorio nuevo dentro de `outputs/`. Se requieren los
insumos protegidos de `outputs/pilot_verified/` y el índice OSM nacional local;
sus hashes se comprueban antes de simular. No se requieren instalaciones ni
descargas. Las rutas y versiones efectivas quedan en `manifest.json` y cada
comando en `commands.json`.

La especificación versionada es [demand.json](demand.json). Llegadas periódicas
en `begin_s + k * 3600 / rate_veh_h`, estrictamente antes de 900 s:

| Movimiento | Origen SUMO | Destino SUMO | Tasa (veh/h) | Inicio (s) | Solicitudes |
|---|---|---|---:|---:|---:|
| W_E | `198404000` | `1225540290#2` | 180 | 0 | 45 |
| E_W | `1255704511#0` | `54144834` | 180 | 10 | 45 |
| N_W | `24556748#0` | `54144834` | 60 | 5 | 15 |
| E_N | `1255704511#0` | `179733827#1` | 60 | 15 | 15 |
| N_E | `141164180#0` | `1225540290#2` | 60 | 20 | 15 |
| W_S | `198404000` | `198404004#1` | 60 | 25 | 15 |

Las tasas suman 600 veh/h durante 15 minutos: 150 vehículos. Son parámetros
de experimento, no conteos observados. Semilla 42, paso 1 s, final 1800 s y
agregación de enlaces cada 60 s. Vehículos `passenger`, `speedFactor=1`,
`speedDev=0`, salida con `departLane=best` y `departSpeed=0`; los demás
parámetros de conducción son los predeterminados de SUMO 1.28.0.

Se usa `duarouter` estricto, un hilo y los OD fijados. El ejecutor comprueba
cada solicitud, hora y movimiento, y conserva las secuencias explícitas en
`controlled.rou.xml` y `controlled_movements.json`. No se sustituyen rechazos.
Doce alternativas topológicas se validan en la red abierta con
`--skip-new-routes true`, preservando sus secuencias. Esta validación no
ejecuta vehículos adicionales ni simula cierres.

Las dos corridas `base/` y `repeat/` deben coincidir en métricas, todos los
atributos de `tripinfo`, intervalos de enlaces, configuraciones y serie temporal
de red, excluyendo solo la duración de CPU. Se verifica el balance de vehículos
en cada paso. Los XML originales y los CSV derivados se conservan juntos.

Para una comparación posterior deben mantenerse OD, identificadores, tipos,
horas de salida, semilla, paso, horizonte, atributos de red y programas
semafóricos. Habrá que declarar una política de reasignación de rutas: las
secuencias base no se pueden atravesar por un enlace cerrado. La comparación
debe contabilizar también rechazos y pendientes, sin eliminar solicitudes.

El resultado entregado es `outputs/pilot_controlled_verified/`.
Ver el [informe](../../docs/pilot_controlled_report.md) para diagnósticos,
unidades, advertencias y límites de calibración. El escenario aleatorio anterior
se reproduce de forma independiente con `python3 -B -m digitaltwins.pilot`.
