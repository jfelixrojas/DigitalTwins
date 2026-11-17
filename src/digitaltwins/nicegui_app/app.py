"""Una pantalla NiceGUI, Leaflet sin teselas y ECharts locales."""
from pathlib import Path

from nicegui import app, ui

from .data import OUT, ROOT, prepare
from . import layout

HERE = Path(__file__).parent
STREAMS = ["W_E", "E_W", "N_W", "E_N", "N_E", "W_S"]
BASE = "#23685b"
CLOSURE = "#b86332"


def od_options(data):
    return {
        "animation": False, "color": [BASE, CLOSURE],
        "textStyle": {"fontFamily": "Arial, sans-serif", "fontSize": 12, "color": "#66716b"},
        "grid": {"left": 42, "right": 18, "top": 38, "bottom": 34},
        "legend": {"top": 0, "right": 8, "itemWidth": 12, "itemHeight": 5,
                   "textStyle": {"color": "#66716b", "fontSize": 11}},
        "tooltip": {"trigger": "axis", ":valueFormatter": "value => Number(value).toFixed(2) + ' s'"},
        "xAxis": {"type": "category", "data": STREAMS, "axisTick": {"show": False},
                  "axisLine": {"lineStyle": {"color": "#d7ddd7"}}, "axisLabel": {"color": "#66716b"}},
        "yAxis": {"type": "value", "name": "s / viaje", "nameTextStyle": {"align": "left", "padding": [0, 0, 0, -34]},
                  "splitLine": {"lineStyle": {"color": "#ebeeea"}}},
        "series": [{"name": name, "type": "bar", "barMaxWidth": 20, "itemStyle": {"borderRadius": [3, 3, 0, 0]},
                    "data": [data["comparison"]["by_stream"][stream]["duration_s"][scenario + "_mean"] for stream in STREAMS]}
                   for name, scenario in [("Base", "base"), ("Cierre", "closure")]],
    }


def active_options(data):
    return {
        "animation": False, "color": [BASE, CLOSURE],
        "textStyle": {"fontFamily": "Arial, sans-serif", "fontSize": 12, "color": "#66716b"},
        "grid": {"left": 38, "right": 26, "top": 38, "bottom": 34},
        "legend": {"top": 0, "right": 8, "itemWidth": 14, "itemHeight": 5,
                   "textStyle": {"color": "#66716b", "fontSize": 11}},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "value", "min": 0, "max": 1800, "interval": 600, "axisTick": {"show": False},
                  "axisLine": {"lineStyle": {"color": "#d7ddd7"}}, "axisLabel": {"formatter": "{value} s", "color": "#66716b"}},
        "yAxis": {"type": "value", "name": "vehículos", "minInterval": 1,
                  "nameTextStyle": {"align": "left", "padding": [0, 0, 0, -30]}, "splitLine": {"lineStyle": {"color": "#ebeeea"}}},
        "series": [{"name": name, "type": "line", "showSymbol": False, "smooth": False,
                    "lineStyle": {"width": 1.7}, "data": [[t, value] for t, value in enumerate(data["active"][scenario])]}
                   for name, scenario in [("Base", "base"), ("Cierre", "closure")]],
    }



def launch(port=8087):
    data = prepare()
    app.add_static_files("/prototype-assets", HERE / "assets", max_cache_age=0)
    app.add_static_file(local_file=OUT / "data.json", url_path="/prototype-data.json", max_cache_age=0)
    app.add_static_file(local_file=OUT / "vehicle_catalog.json", url_path="/vehicle-catalog.json", max_cache_age=0)
    for code in ("SIM-002", "SIM-003", "SIM-004", "SIM-005"):
        app.add_static_file(local_file=ROOT / f"docs/simulations/{code}.md", url_path=f"/experiment/{code}.md", max_cache_age=0)

    def page():
        ui.add_css((HERE / "assets/comparison.css").read_text())
        for asset in ("replay-model.js", "map-pane.js", "comparison.js"):
            ui.add_head_html(f'<script defer src="/prototype-assets/{asset}"></script>')
        with ui.element("main").classes("prototype-shell").props('data-mode=single'):
            ui.html(layout.HEADER, sanitize=False).classes("app-header")
            ui.html(layout.INTRO, sanitize=False).classes("intro")
            ui.html(layout.MODE_TOOLS, sanitize=False).classes("mode-tools")
            with ui.element("div").classes("workspace"):
                with ui.element("section").classes("map-area"):
                    ui.html(layout.MAP_HEADING, sanitize=False).classes("map-heading")
                    ui.html(layout.PLAYBACK, sanitize=False).classes("playback")
                    with ui.element("div").classes("maps-grid"):
                        maps = []
                        for key, title in (("primary", "Base · red abierta"), ("secondary", "Cierre virtual")):
                            panel = ui.element("section").classes("map-panel").props(f'id={key}-map-panel')
                            if key == "secondary":
                                panel.props("hidden")
                            with panel:
                                ui.html(f'<h3 id="pane-{key}-title">{title}</h3><span id="pane-{key}-count"></span>', sanitize=False).classes("pane-heading")
                                center = tuple((a + b) / 2 for a, b in zip(*data["bounds"]))
                                m = ui.leaflet(center=center, zoom=17, options={"preferCanvas": True, "zoomSnap": .25, "zoomDelta": .5,
                                              "minZoom": 14, "maxZoom": 22, "zoomControl": True, "attributionControl": True, "inertia": False})
                                m.clear_layers()
                                m.classes("corridor-map " + key + "-map")
                                maps.append(m)
                    ui.html(layout.MAP_FOOT, sanitize=False).classes("map-footer")
                    ui.html(layout.VEHICLE_INSPECTOR, sanitize=False).classes("vehicle-inspector-host")
                with ui.element("details").classes("indicators-panel").props('id=indicators-panel open'):
                    ui.html('Indicadores del experimento <span aria-hidden="true">⌄</span>', sanitize=False, tag="summary")
                    ui.html(layout.SIMULATION, sanitize=False).classes("simulation-panel").props('id=single-indicators')
                    ui.html(layout.comparative_metrics(data), sanitize=False).classes("compare-indicators").props('id=compare-indicators hidden')
            with ui.element("details").classes("analysis-details").props('id=analysis-details open'):
                ui.html('Análisis por movimiento y evolución <span aria-hidden="true">⌄</span>', sanitize=False, tag="summary")
                with ui.element("section").classes("analysis-area"):
                    with ui.element("div").classes("chart-block"):
                        ui.html(layout.ANALYSIS_HEADING, sanitize=False).classes("analysis-heading")
                        od = ui.echart(od_options(data), renderer="svg").classes("analysis-chart od-chart")
                        ui.html('<p id="od-note" class="chart-note">Medias por viaje, en segundos.</p>', sanitize=False)
                    with ui.element("div").classes("chart-block active-block"):
                        ui.html(layout.ACTIVE_HEADING, sanitize=False).classes("analysis-heading")
                        active = ui.echart(active_options(data), renderer="svg").classes("analysis-chart active-chart")
                        ui.html('<p class="chart-note">Vehículos presentes en toda la red, incluidas conexiones internas. La guía sigue el reloj compartido.</p>', sanitize=False)
            ui.html(layout.experiment(data["catalog"]), sanitize=False)
            ui.html('<span>© OpenStreetMap contributors / Geofabrik · ODbL 1.0</span><span>Resultados simulados · sin intervención sobre infraestructura real</span>', sanitize=False).classes("app-footer")
            ui.html('<div id="runtime-error" role="alert" hidden></div>', sanitize=False)

        async def initialize():
            for m in maps:
                await m.initialized()
            await ui.run_javascript(f"return window.DT008.start({maps[0].id}, {maps[1].id}, {od.id}, {active.id});", timeout=30)

        ui.timer(.1, initialize, once=True)

    ui.run(page, host="127.0.0.1", port=port, title="DigitalTwins · Comparación sincronizada",
           favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="9" fill="#28665b"/><text x="20" y="26" fill="white" font-size="16" text-anchor="middle" font-family="Arial">DT</text></svg>',
           language="es", reload=False, show=False, on_air=False, tailwind=False, binding_refresh_interval=None,
           fastapi_docs=False, endpoint_documentation="none")
