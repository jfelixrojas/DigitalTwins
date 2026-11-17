### Contrato de propósito, alcance y límites

**Proyecto**: Gemelo digital de Movilidad Urbana

**Versión**: 0.1.0

1. Propósito formal:

Desarrollar una arquitectura experimental de gemelo digital de movilidad urbana, alimentada mediante datos de conteos vehiculares, registros de operación semafórica e información de Waze, que permita reconstruir y estimar el estado de una red vial, investigar su comportamiento dinámico y evaluar escenarios hipotéticos de intervención mediante simulaciones aisladas, sin ejecutar comandos ni modificar la infraestructura vial real.

2. Naturaleza del sistema:

El proyecto tendrá una arquitectura de propósito dual:

A. Componente operacional de solo lectura

Permitirá observar, reconstruir y estimar el comportamiento de la red vial a partir de datos reales, así como generar diagnósticos y resultados de apoyo a decisiones para un centro de gestión de movilidad.

B. Componente científico y experimental

Permitirá crear modelos matemáticos, ejecutar simulaciones, introducir sensores sintéticos, modificar virtualmente condiciones operacionales, comparar hipótesis y evaluar la validez de los resultados.

Ambos componentes podrán compartir modelos y recursos verificados, pero conservarán estados y ejecuciones independientes.

3. Fuentes de información iniciales

Se consideran tres fuentes principales, sujetas a caracterización y verificación de su disponibilidad y calidad:

Conteos vehiculares.

Registros históricos o disponibles de operación de controladores semafóricos, incluyendo fases, estados y tiempos.

Información de tráfico e incidentes procedente de Waze, mediante los mecanismos de acceso autorizados.

Se incorporará una representación geográfica y topológica de la red vial. Podrán añadirse nuevas fuentes de observación cuando exista justificación científica y disponibilidad legítima.

4. Capacidades incluidas en el alcance

- El proyecto podrá desarrollar:
- Reconstrucción histórica de condiciones de tráfico.
- Estimación de estados no observados directamente.
- Modelado de colas, flujos, velocidades, demoras y propagación de congestiones.
- Detección y análisis de anomalías e incidentes.
- Simulación de cierres de vías y restricciones de capacidad.
- Simulación de cambios en programación y coordinación semafórica.
- Evaluación de desvíos y redistribución hipotética de tráfico.
- Simulación de sensores y procesos de observación.
- Análisis de incertidumbre, observabilidad e información incremental.
- Comparación de alternativas para apoyo a decisiones operacionales.
- Cada capacidad quedará condicionada a la disponibilidad de datos, la identificabilidad del modelo y su validación.

5. Límites operacionales obligatorios

El sistema será de lectura respecto de la infraestructura vial real.

Queda fuera del alcance:
- Enviar comandos a controladores semafóricos reales.
- Modificar directamente fases, ciclos o tiempos de operación reales.
- Ejecutar cierres o restricciones en infraestructura física.
- Automatizar intervenciones operacionales sobre sistemas de producción.
- Utilizar interfaces de control para las que no existe autorización.

Toda modificación de programación semafórica, capacidad, geometría, demanda o disponibilidad vial ocurrirá exclusivamente en ambientes de simulación aislados.

Los escenarios hipotéticos no tendrán canales de escritura hacia la infraestructura física.

6. Principios científicos

Se deberán distinguir explícitamente:

- Estado real, estado estimado y estado simulado.
- Datos observados, datos inferidos y datos sintéticos.
- Reproducción histórica, predicción y simulación contrafactual.
- Parámetros medidos, calibrados y supuestos.
- Incertidumbre del estado, de los parámetros y de los escenarios.
- Resultados de simulación y efectos causales efectivamente demostrados.

Toda conclusión deberá delimitar los supuestos y la evidencia que la respaldan.

7. Reproducibilidad y validación

Los experimentos deberán permitir reconstruir las entradas, versiones de datos, configuración, parámetros, modelos, escenarios y resultados.

La calibración se realizará sobre datos identificados para ese propósito y la validación empleará observaciones independientes siempre que estén disponibles.

Se documentarán las limitaciones de cobertura espacial y temporal, los errores de las fuentes, las incertidumbres y el alcance de las conclusiones.

8. Pregunta científica central

¿Hasta qué punto los conteos vehiculares, los registros de operación semafórica y las observaciones de Waze permiten reconstruir el estado de una red vial y evaluar intervenciones que nunca se ejecutaron físicamente?

9. Resultado esperado

Una arquitectura experimental reproducible que permita:

1. Determinar qué estados del tráfico pueden observarse o estimarse.
2. Cuantificar el valor informativo de las fuentes disponibles.
3. Representar la dinámica del sistema bajo condiciones reales.
4. Evaluar escenarios hipotéticos bajo supuestos explícitos.

Proporcionar resultados interpretables para investigación y apoyo a decisiones de gestión de movilidad.