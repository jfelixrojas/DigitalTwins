# Pruebas

La intervención 008 deja **56 pruebas Python y 10 pruebas JavaScript**,
además de 55 comprobaciones del comparador en Chrome y las 48 comprobaciones
de regresión del modo único. Las pruebas JavaScript usan node:test, incluido
con Node; no añaden paquetes al proyecto.

~~~sh
PYTHONPATH=src .venv-nicegui/bin/python -B -m unittest discover -s tests -v
node --test tests/test_replay_model.cjs
~~~

Las pruebas unitarias usan fixtures pequeños y temporales; no necesitan los
datos OSM ni los resultados excluidos de Git. Las revisiones de Chrome sí
requieren las evidencias locales y el visualizador en ejecución.

El modelo de presentación prueba un único reloj, pausa, búsqueda, horizonte,
snapshots con ambos escenarios en el mismo segundo, conservación de posiciones
y rutas y ausencia de coordenadas inventadas para vehículos sin muestra.
La prueba Chrome del comparador está en tests/browser_comparison.cjs.
La prueba histórica tests/browser_nicegui.cjs ahora guarda sus resultados
en outputs/intervention008/regression007/ y apunta al mapa principal, para
conservar las evidencias de la 007. Se mantiene su conjunto de 48 comprobaciones.
[Resultados y límites](../docs/nicegui_comparison_report.md).

La intervención 007 dejó 52 pruebas unitarias. Añadió
ocho pruebas de georreferenciación: contraste con nodos OSM independientes,
orden lat/lon, signo del desplazamiento, reversibilidad métrica, rechazo de
proyección ausente o coordenadas no finitas, anclas insuficientes y lectura
inmutable del visor 006 con rechazo de hashes o esquema alterados.

~~~sh
PYTHONPATH=src .venv-nicegui/bin/python -B -m unittest discover -s tests -v
~~~

Hay además una prueba de Chrome en tests/browser_nicegui.cjs. Usa Playwright
ya disponible en el entorno de revisión, sin incorporarlo a la aplicación.
Bloquea solicitudes fuera del servidor local y comprueba posiciones, IDs,
selección de escenarios, controles, gráficos, zoom, selección de enlaces,
clientes independientes, cuatro tamaños y tráfico durante la reproducción.
Los resultados y las 48 comprobaciones están en
[outputs/intervention007/](../outputs/intervention007/browser/validation.json).
La [receta y sus límites](../docs/nicegui_prototype_report.md) documentan cómo
repetir la revisión. Las pruebas de las intervenciones anteriores se conservan.

La intervención 002 añade siete pruebas sintéticas: detección de giros
prohibidos, ausencia de una maniobra prohibida, nodos via no mapeados,
distinción entre desconexión y falta de camino dirigido, balances de vehículos
y rechazo de resultados sin recorridos completados.

La intervención 003 añade ocho: conteo y unidades de llegadas periódicas,
generación determinista y rechazo de tasa inválida, conectividad dirigida,
alternativas sin mutar el grafo, permisos de conexión y carril interno,
agregación por enlace y un contraejemplo de balance temporal. Son 15 pruebas
de las intervenciones anteriores; usan fixtures locales y eliminan sus temporales.

La intervención 004 añade diez pruebas: rechazo de rutas por el enlace cerrado,
giros inválidos, omisiones de vehículos y cambios de salida o destino;
separación de propuestas reemplazadas y rutas ejecutadas; exigencia de tiempos
de paso; conservación de pares pendientes; distinción entre duración y
`timeLoss`; percentiles y denominadores nulos; normalización limitada al
dispositivo adicional `vehroute`. La intervención 004 deja 25 pruebas.

La intervención 005 añade ocho pruebas de conservación del calendario original,
cronogramas distintos y acotados, determinismo, conservación de ID/OD y cantidades,
offsets y coordinación relativa, rechazo de ciclos distintos de 90 s,
detección de desfases ignorados usando estados efectivos y descriptivos de
cambios de signo. La intervención 005 deja 33 pruebas.

La intervención 006 añade once pruebas de integridad del visor: coordenadas
FCD nativas y pasos vacíos; cobertura temporal e IDs/carriles; asociación
semafórica por conexión y geometría interna; rechazo de índices inválidos;
compresión temporal sin pérdida; rechazo de estados o tiempos incoherentes;
unidades de flujo, porcentaje y presencia; cobertura de intervalos; totales,
medias y denominadores contrastados con tripinfo; JSON seguro para HTML; y
rechazo de fuentes alteradas o fuera del repositorio. La intervención 006 deja 44 pruebas.

```sh
PYTHONPATH=src python3 -B -m unittest discover -s tests -v
```

Las pruebas no sustituyen la ejecución real. Sus evidencias están en
`outputs/pilot_verified/` y `outputs/intervention002/final_validation.json`:
red no vacía, once restricciones revisadas, 109 rutas válidas y completadas,
balances coherentes y repetición con métricas y atributos tripinfo idénticos.

La ejecución controlada verificada está en `outputs/pilot_controlled_verified/`:
150 solicitudes aceptadas y completadas, dos corridas idénticas y doce
secuencias alternativas validadas en la red abierta. La nueva regresión del
piloto anterior está en `outputs/intervention003/regression002/`; la comparación
con sus resultados protegidos está en `outputs/intervention003/regression_comparison.json`.
El registro de las 15 pruebas está en `outputs/intervention003/tests.log`.

El registro actual está en `outputs/intervention004/tests.log`. La comprobación
integrada del cierre está en `outputs/closure_experiment_verified/`: 3600
muestras carril-paso por corrida, rutas y tiempos de salida de cada enlace,
repetición de métricas y rutas, y regresión de la base frente a la 003. Se
revisa también el balance en cada paso y la igualdad entre la integral de
vehículos presentes y el tiempo total de recorrido. La auditoría final conserva
los hashes anteriores en `outputs/intervention004/final_validation.json`.

Las 33 pruebas de la intervención 005 están registradas en
`outputs/closure_sensitivity/audit/tests.log`. La matriz de la 005 conserva
estados semafóricos nativos y trayectorias; los 15 pares y la repetición nueva
verifican permisos, rutas, balances y equivalencia temporal. Las comprobaciones
de integridad y de las fuentes están en
`outputs/closure_sensitivity/audit/final_validation.json`.

Las 44 pruebas y la auditoría de la 006 quedan en
[tests.log](../outputs/intervention006/tests.log) y
[final_validation.json](../outputs/intervention006/final_validation.json).
La comprobación en Chrome usa el HTML mediante file://, contexto sin conexión,
HTTP(S) bloqueado y un perfil exclusivo de prueba; comprueba reproducción,
pausa, selección de los 15 pares, cifras, cuatro fichas, posiciones y señales,
ausencia de posiciones en pares sin FCD empaquetado y tamaños móviles:
[evidencia del navegador](../outputs/intervention006/browser/validation.json).
No es una dependencia de ejecución ni requiere instalar Playwright para usar
o regenerar el visor.
