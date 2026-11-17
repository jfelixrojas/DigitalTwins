# Instalación mínima para el piloto SUMO

Estado: **autorizado explícitamente por el usuario** en este chat, mediante
«Autorizo el plan de instalación y continuar con el piloto». El alcance
aprobado incluye las descargas, rutas de sistema y dependencias descritas abajo.
Los resultados efectivos se registran en `outputs/intervention002/`.

Se volvieron a comprobar los cuatro recursos de `data/osm/sources.json`:
tamaños y SHA-256 coinciden. En el diagnóstico inicial faltaban `sumo`,
`netconvert`, `duarouter`, `osmium` y `SUMO_HOME`; XQuartz tampoco estaba instalado.
Python 3.11.5 y Homebrew ya están disponibles.

## SUMO 1.28.0 mediante el instalador oficial

- Descarga: [sumo-1.28.0.pkg](https://sumo.dlr.de/releases/1.28.0/sumo-1.28.0.pkg),
  aproximadamente 122 MB, para Apple Silicon.
- SHA-256 publicado por SUMO:
  `ff81b37ad302652c32ab286d8308c98aa83466c27a1f25bbaeecbb0ead2d0f8c`.
- Guardar instalador y evidencias dentro de `outputs/intervention002/install/`.
- Instalación de sistema: `/Library/Frameworks/EclipseSUMO.framework/`.
- El paquete oficial incluye los lanzadores `/Applications/SUMO sumo-gui.app`,
  `/Applications/SUMO netedit.app` y `/Applications/SUMO Scenario Wizard.app`.
  No se usarán Scenario Wizard ni servicios web.
- Requiere autorización de administrador de macOS para instalar en `/Library`
  y `/Applications`. La contraseña se introduce solo en la interfaz local de
  macOS; no se solicita ni se registra en el chat.

Comandos propuestos desde la raíz de DigitalTwins, después de autorización:

```sh
mkdir -p outputs/intervention002/install
curl --fail --location \
  https://sumo.dlr.de/releases/1.28.0/sumo-1.28.0.pkg \
  --output outputs/intervention002/install/sumo-1.28.0.pkg
shasum -a 256 outputs/intervention002/install/sumo-1.28.0.pkg
pkgutil --check-signature outputs/intervention002/install/sumo-1.28.0.pkg
sudo /usr/sbin/installer \
  -pkg outputs/intervention002/install/sumo-1.28.0.pkg -target /
```

No ejecutar `installer` si el hash no coincide. Si el agente no dispone de
privilegios administrativos, abrir el paquete con Installer y dejar la
autenticación al usuario. Antes de instalar se inspeccionará el contenido y
se contrastarán las rutas con este plan.

Para el proceso del piloto se fijarán variables de entorno, sin editar el
perfil global de la terminal:

```sh
export SUMO_HOME=/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/share/sumo
export PATH=/Library/Frameworks/EclipseSUMO.framework/Versions/1.28.0/EclipseSUMO/bin:/opt/homebrew/bin:$PATH
```

Se comprobarán las rutas reales y `tools/randomTrips.py` después de instalar;
no se usará silenciosamente otra versión de SUMO.

## Osmium mediante Homebrew

[Osmium-tool](https://formulae.brew.sh/formula/osmium-tool) tiene actualmente
versión estable 1.19.1, revisión de fórmula 1. El plan usa binarios Homebrew,
sin compilar desde fuentes. Descargas de botellas y metadatos desde los
repositorios oficiales de Homebrew (`ghcr.io` y `formulae.brew.sh`).

La cadena de dependencias publicada es `osmium-tool → boost, lz4` y
`boost → icu4c@79, xz, zstd`. Boost e ICU versionado no están instalados;
LZ4, XZ y Zstd existen en versiones antiguas. Homebrew puede necesitar
actualizarlos para satisfacer las dependencias del binario. Estas son las
únicas dependencias transitivas contempladas; registrar el plan efectivo
antes de aplicarlo. No actualizar paquetes ajenos, Python ni SAVIA-X.

```sh
HOMEBREW_NO_AUTO_UPDATE=1 \
HOMEBREW_NO_ANALYTICS=1 \
HOMEBREW_NO_INSTALL_CLEANUP=1 \
HOMEBREW_NO_INSTALLED_DEPENDENTS_CHECK=1 \
HOMEBREW_CACHE="$PWD/outputs/intervention002/homebrew-cache" \
HOMEBREW_LOGS="$PWD/outputs/intervention002/homebrew-logs" \
/opt/homebrew/bin/brew install --formula --force-bottle --dry-run osmium-tool
```

Tras revisar el resultado, ejecutar el mismo comando quitando `--dry-run`.
Esto escribe en `/opt/homebrew/Cellar`, `/opt/homebrew/opt` y sus enlaces de
ejecutables, además de la caché y los registros locales indicados. Homebrew
normalmente no necesita `sudo`, pero el agente necesita permiso para salir
del ámbito de escritura del proyecto. No se ejecutará `brew update`,
`brew upgrade` ni limpieza automática.

## Comprobación y alcance autorizado

```sh
sumo --version
netconvert --version
duarouter --version
osmium --version
test -f "$SUMO_HOME/tools/randomTrips.py"
PYTHONPATH=src python3 -B -m digitaltwins.doctor --verify-source --require-sumo
```

XQuartz queda fuera de esta instalación mínima. `sumo-gui` puede estar en el
paquete, pero su visualización no se exige para ejecutar el piloto por CLI.
Si las herramientas CLI necesitan una dependencia adicional no prevista,
se documentará antes de ampliar el alcance. No se modificarán mecanismos de
seguridad de macOS ni entornos Python existentes.

La necesidad de autorización procede de la **fase 1, puntos 4 y 5 de la
intervención 002 del usuario**, que exige mostrar cambios y obtener aprobación
antes de instalar. AGENTS.md limita las escrituras habituales a DigitalTwins;
esta aprobación debe cubrir expresamente las rutas de sistema anteriores.

Fuentes verificadas: [descargas oficiales SUMO](https://sumo.dlr.de/docs/Downloads.php),
[constructor del instalador 1.28.0](https://github.com/eclipse-sumo/sumo/blob/v1_28_0/tools/build_config/buildMacOSInstaller.py),
[fórmula Osmium](https://github.com/Homebrew/homebrew-core/blob/main/Formula/o/osmium-tool.rb)
y [fórmula Boost](https://github.com/Homebrew/homebrew-core/blob/main/Formula/b/boost.rb).

## Resultado efectivo

SUMO 1.28.0 fue instalado mediante Installer, con firma y notarización
verificadas fuera del sandbox, y aceptación EPL 2.0 confirmada en el chat.
Homebrew instaló Osmium 1.19.1_1, Boost 1.92.0_1, ICU 79.1 y las versiones
necesarias de XZ 5.8.4, LZ4 1.11.1 y Zstd 1.5.7_1. No hubo compilación,
actualización general, instalación XQuartz ni cambios de entornos Python.

La CLI administrativa inicial no pudo abrir el paquete del Escritorio;
la interfaz Installer sí completó la operación. El diagnóstico posterior
con SUMO_HOME/PATH del proyecto y verificación de fuentes pasó.

Se resolvió la falta de datos PROJ del paquete reutilizando en lectura la
base existente de PyProj, compatible con libproj 9.5.1. No fue necesaria una
instalación adicional. Ver `docs/pilot_report.md` y las evidencias dentro de
`outputs/intervention002/`.
