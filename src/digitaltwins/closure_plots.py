"""Figuras científicas estáticas del cierre, derivadas de sus archivos auditables."""

from collections import Counter
import csv
import importlib.metadata
import json
import os
import xml.etree.ElementTree as ET

from .doctor import sha256


def render(out, net, spec, comparison, routes, edges):
    folder = out / "visual"; folder.mkdir()
    os.environ["MPLCONFIGDIR"] = str(folder / ".mplconfig")
    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D
    blue, orange, purple = "#1768ac", "#d66b17", "#ad168c"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.text(.01, .01, "SUMO sintético · Semilla 42 · Sin calibración real · OSM © OpenStreetMap contributors / Geofabrik", fontsize=8, color="#4b5563")
        fig.tight_layout(rect=(0, .045, 1, .96))
        fig.savefig(folder / (name + ".png"), dpi=150)
        fig.savefig(folder / (name + ".svg")); plt.close(fig)

    def draw(ax, ids=None, color="#cbd1d8", width=.7, **kwargs):
        ids = sorted(net.edges if ids is None else ids)
        lines = LineCollection([net.shapes[e] for e in ids], colors=color, linewidths=width, **kwargs)
        ax.add_collection(lines); ax.autoscale(); ax.set_aspect("equal")
        ax.set_xlabel("Este relativo (m)"); ax.set_ylabel("Norte relativo (m)")

    closed = spec["closed_edge"]
    detours = [e["edge"] for e in edges if e["delta_executed_route_uses"] > 0]
    fig, ax = plt.subplots(figsize=(10, 7)); draw(ax)
    draw(ax, detours, orange, 3); draw(ax, [closed], purple, 5)
    for eid, label, shift in ((closed, "Cierre: 1257993561#5", (30, 90)),
                              ("-175606174", "35 Avenida Sur: 45 viajes desviados", (-330, -100)),
                              ("-198404021", "Calle el Progreso: 45 viajes desviados", (70, -80))):
        x, y = net.shapes[eid][len(net.shapes[eid]) // 2]
        ax.annotate(label, (x, y), xytext=(x + shift[0], y + shift[1]), arrowprops={"arrowstyle": "->"}, fontsize=9,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9})
    ax.legend(handles=[Line2D([0], [0], color=purple, lw=4, label="Passenger prohibido: 0–1800 s"),
                       Line2D([0], [0], color=orange, lw=3, label="Enlaces que reciben desvíos ejecutados")], loc="lower right")
    ax.set_title("Cierre efectivo y desvíos observados en la simulación\nAmbos carriles cerrados; cero pasos por el enlace")
    save(fig, "closure_map")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    route_counts = {}
    for ax, scenario, color in zip(axes, ("base", "closure"), (blue, orange)):
        draw(ax)
        counts = Counter(tuple(r["edges"]) for vid, r in routes[scenario].items() if vid.startswith("W_E."))
        route_counts[scenario] = [{"vehicles": n, "edges": list(seq)} for seq, n in counts.items()]
        for sequence, n in counts.items():
            draw(ax, sequence, color, 2.5)
        draw(ax, [closed], purple, 4, linestyles="--" if scenario == "closure" else "solid")
        ax.set_title(("Base: enlace abierto" if scenario == "base" else "Cierre: alternativa ejecutada") + "\n45 vehículos W_E · destinos y salidas conservados")
        ax.legend(handles=[Line2D([0], [0], color=color, lw=3, label="Ruta final con tiempos de paso"),
                           Line2D([0], [0], color=purple, lw=3, ls="--" if scenario == "closure" else "-", label="Enlace seleccionado")], loc="lower right")
    save(fig, "routes_comparison")
    (folder / "executed_route_counts.json").write_text(json.dumps(route_counts, indent=2) + "\n")

    groups = comparison["by_stream"]; ids = ["W_E", "E_W", "N_W", "E_N", "N_E", "W_S"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(ids)); width = .36
    for label, key, color, delta in (("Base", "base_mean", blue, -width / 2), ("Cierre", "closure_mean", orange, width / 2)):
        values = [groups[s]["duration_s"][key] for s in ids]
        axes[0].bar(x + delta, values, width, label=label, color=color)
    axes[0].set_xticks(x, ids); axes[0].set_ylabel("Tiempo medio de recorrido (s)"); axes[0].legend()
    changes = [groups[s]["duration_s"]["delta_mean"] for s in ids]
    axes[1].bar(x, changes, color=[orange if s == "W_E" else blue for s in ids]); axes[1].axhline(0, color="#555", lw=.7)
    for j, value in enumerate(changes):
        axes[1].annotate(f"{value:+.2f}", (j, value), xytext=(0, 5 if value >= 0 else -14), textcoords="offset points", ha="center", fontsize=9)
    axes[1].set_xticks(x, ids); axes[1].set_ylabel("Cambio medio: cierre − base (s)"); axes[1].margins(y=.2)
    fig.suptitle("Tiempo de recorrido por movimiento · W_E expuesto: 45; resto: 105")
    save(fig, "stream_travel_times")

    with (out / "paired_vehicle_impacts.csv").open() as handle:
        paired = list(csv.DictReader(handle))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    impacts = [float(r["delta_duration_s"]) for r in paired if r["delta_duration_s"]]
    bins = np.arange(np.floor(min(impacts) / 5) * 5 - 2.5, np.ceil(max(impacts) / 5) * 5 + 7.5, 5)
    for exposed, label, color in ((True, "W_E, 45 expuestos", orange), (False, "Otros, 105 no expuestos", blue)):
        values = sorted(float(r["delta_duration_s"]) for r in paired if (r["originally_exposed"] == "True") == exposed and r["delta_duration_s"])
        axes[0].hist(values, bins=bins, alpha=.65, label=label, color=color)
        axes[1].step(values, np.arange(1, len(values) + 1) * 100 / len(values), where="post", label=label, color=color)
    for ax in axes:
        ax.axvline(0, color="#555", ls="--", lw=.8); ax.set_xlabel("Cambio emparejado en duración (s)"); ax.legend(fontsize=8)
    axes[0].set_ylabel("Vehículos (veh)"); axes[1].set_ylabel("Porcentaje acumulado de cada grupo (%)")
    fig.suptitle("Distribución de impactos por identificador · una realización determinista")
    save(fig, "paired_travel_impacts")

    with (out / "edge_interval_comparison.csv").open() as handle:
        intervals = list(csv.DictReader(handle))
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharex=True)
    for row, (eid, label) in enumerate(((closed, "Enlace cerrado"), ("-175606174", "35 Avenida Sur"), ("-198404021", "Calle el Progreso"))):
        values = [r for r in intervals if r["edge"] == eid]
        time = [float(r["begin_s"]) / 60 for r in values] + [float(values[-1]["end_s"]) / 60]
        for col, (field, unit) in enumerate((("flow_in_veh_h", "Flujo de entrada (veh/h)"), ("occupancy_pct", "Ocupación SUMO (%)"))):
            for scenario, name, color in (("base", "Base", blue), ("closure", "Cierre", orange)):
                y = [float(v[scenario + "_" + field]) for v in values]
                axes[row, col].step(time, y + [y[-1]], where="post", label=name, color=color)
            axes[row, col].set_title(label + " · " + eid, fontsize=10); axes[row, col].set_ylabel(unit); axes[row, col].legend(fontsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("Minutos desde el inicio · intervalos de 60 s")
    fig.suptitle("Evolución de flujos y ocupación en cierre y desvíos · sin recortar valores")
    save(fig, "affected_edge_timeseries")

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for scenario, label, color in (("base", "Base", blue), ("closure", "Cierre", orange)):
        steps = ET.parse(out / scenario / "summary.xml").getroot().findall("step")
        time = [float(s.get("time")) / 60 for s in steps]
        axes[0, 0].plot(time, [int(s.get("running")) for s in steps], label=label, color=color)
        axes[0, 1].plot(time, [int(s.get("halting")) for s in steps], label=label, color=color)
        axes[1, 0].plot(time, [int(s.get("arrived")) for s in steps], label=label, color=color)
    axes[0, 0].set_ylabel("Vehículos presentes en red (veh)"); axes[0, 1].set_ylabel("Vehículos detenidos en red (veh)")
    axes[1, 0].set_ylabel("Viajes completados acumulados (veh)")
    fields = ["duration_s", "time_loss_s", "waiting_time_s"]; x = np.arange(3)
    for scenario, label, color, shift in (("base_mean", "Base", blue, -.18), ("closure_mean", "Cierre", orange, .18)):
        axes[1, 1].bar(x + shift, [comparison["system"][f][scenario] for f in fields], .36, color=color, label=label)
    axes[1, 1].set_xticks(x, ["Recorrido", "timeLoss", "waitingTime"]); axes[1, 1].set_ylabel("Media por viaje completado (s)")
    axes[1, 1].set_title("Medidas solapadas; no se suman", fontsize=10)
    for ax in axes.flat:
        ax.legend(fontsize=8); ax.grid(alpha=.15)
    for ax in (axes[0, 0], axes[0, 1], axes[1, 0]):
        ax.set_xlabel("Minutos desde el inicio")
    fig.suptitle("Sistema completo: misma demanda de 150 vehículos, semilla 42")
    save(fig, "system_indicators")
    source_names = ["comparison.json", "paired_vehicle_impacts.csv", "edge_interval_comparison.csv", "edge_totals_comparison.csv",
                    "base/summary.xml", "closure/summary.xml", "base/executed_routes.json", "closure/executed_routes.json", "controlled.net.xml"]
    (folder / "manifest.json").write_text(json.dumps({"kind": "Static scientific plots of synthetic SUMO outputs",
        "packages": {p: importlib.metadata.version(p) for p in ("matplotlib", "numpy")},
        "source_sha256": {n: sha256(out / n) for n in source_names},
        "figures": [p.name for p in sorted(folder.iterdir()) if p.suffix in (".png", ".svg")]}, indent=2) + "\n")
