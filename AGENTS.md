# DigitalTwins

## Alcance de escritura

- Escribir exclusivamente dentro de este repositorio, `DigitalTwins`.
- `../savia-x-b1`, `../savia-x-lab`, `../x_red_social` y los demás directorios
  de `DC_X` son fuentes de consulta de solo lectura. No instalar, ejecutar
  preparadores ni generar cachés, índices o resultados dentro de ellos.
- Conservar los documentos conceptuales y ejecutivos existentes en `docs/`.
  Consultar primero `docs/concept.md` y `docs/osm_inventory.md`.

## Propósito y límites

- El territorio de investigación es El Salvador; verificar la cobertura de
  cada recurso antes de adoptarlo.
- Las observaciones previstas son conteos vehiculares, registros semafóricos
  y Waze mediante acceso autorizado. Su disponibilidad y calidad se verifican;
  no se presuponen.
- Los sistemas reales y controladores semafóricos son exclusivamente fuentes
  de observación. Están prohibidos los comandos de control, cambios de fases,
  tiempos o ciclos reales y cualquier intervención sobre infraestructura real.
- Los cierres, cambios semafóricos, de capacidad, geometría o demanda solo se
  simulan en un laboratorio aislado, sin canales de escritura al sistema real.
- Distinguir datos observados, inferidos y sintéticos; estados reales, estimados
  y simulados; parámetros medidos, calibrados y supuestos.

## Modelos y notación

- Respetar el contrato **GDM-MATH-001 v1.0**. Los documentos Word existentes
  recogen sus invariantes: `D_t` son salidas efectivas, `S_t` capacidad máxima,
  `Q_t` cola y `n_{i,t}` ocupación total de celda. No intercambiar estos símbolos.
  Consultar el contrato completo antes de introducir formulaciones nuevas.
- CTM es la referencia física experimental inicial y LTM el modelo comparativo.
  Los enfoques híbridos y GNN permanecen como alternativas de evaluación.
- SUMO es inicialmente el entorno de simulación microscópica. Una simulación
  SUMO no constituye una implementación ni una validación de CTM o LTM.
- La intervención 001 no implementa CTM, LTM ni modelos de IA.

## Disciplina de trabajo

- Priorizar cambios pequeños, reproducibles, documentados y verificables.
- Reutilizar los datos locales mediante rutas de lectura y manifiestos con
  versión, tamaño, SHA-256, procedencia y licencia. No copiar extractos grandes
  ni usar alias `latest` sin una necesidad documentada.
- Abrir bases de fuentes con SQLite `mode=ro&immutable=1` y `query_only=ON`;
  no cargar extensiones ni ejecutar scripts de adquisición por su nombre.
- No mezclar cortes OSM de agosto y octubre por ID sin verificar equivalencia.
- Conservar atribuciones y licencias de cada fuente y de sus derivados.
- Registrar versión del simulador, configuración, semillas, entradas y supuestos
  de cada experimento; escribir los productos generados dentro de `outputs/`.
- No añadir servicios web, Docker, CI/CD ni infraestructura compleja sin una
  necesidad demostrada. No crear módulos vacíos de modelos futuros.
- Durante la intervención 001 no instalar dependencias ni descargar datos.
  Las consultas externas con costo requieren autorización explícita.
