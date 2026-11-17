# Pruebas

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
dispositivo adicional `vehroute`. El total es **25 pruebas**.

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
