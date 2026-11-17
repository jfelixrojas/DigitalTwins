"""Cinco figuras descriptivas de la matriz temporal, sin inferencia poblacional."""

import csv
import importlib.metadata
import json
import os

from .doctor import sha256
from .sensitivity_analysis import xml, FOCAL_TLS, FOCAL_IDS


def render(out, rows, movements, cases):
    folder = out / "visual"; folder.mkdir()
    os.environ["MPLCONFIGDIR"] = str(folder / ".mplconfig"); os.environ["MPLBACKEND"] = "Agg"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import TwoSlopeNorm
    from matplotlib.lines import Line2D
    blue, orange = "#1768ac", "#d66b17"
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.text(.01, .012, "SUMO sintético · 15 diseños deterministas · Sin calibración ni inferencia poblacional · OSM © OpenStreetMap contributors", fontsize=8, color="#4b5563")
        fig.tight_layout(rect=(0, .05, 1, .95)); fig.savefig(folder / (name + ".png"), dpi=150)
        fig.savefig(folder / (name + ".svg")); plt.close(fig)

    schedules = ["original", "jitter101", "jitter102", "jitter103", "jitter104"]
    lookup = {(r["schedule"], r["offset_s"]): r for r in rows}
    matrix = np.array([[lookup[s, off]["delta_total_duration_s"] for off in (0, 30, 60)] for s in schedules])
    limit = max(1, abs(matrix).max())
    fig, ax = plt.subplots(figsize=(8, 6)); im = ax.imshow(matrix, cmap="RdBu_r", norm=TwoSlopeNorm(vmin=-limit, vcenter=0, vmax=limit), aspect="auto")
    for i in range(5):
        for j in range(3):
            value = matrix[i, j]; pct = lookup[schedules[i], (0, 30, 60)[j]]["delta_total_duration_pct"]
            ax.text(j, i, f"{value:+.0f} s\n{pct:+.2f} %", ha="center", va="center", color="white" if abs(value) > limit * .55 else "#111")
    ax.set_xticks(range(3), ["Original", "+30 s", "+60 s"]); ax.set_yticks(range(5), ["Original", "Semilla 101", "Semilla 102", "Semilla 103", "Semilla 104"])
    ax.set_xlabel("Desfase global adicional"); ax.set_ylabel("Cronograma de salidas")
    ax.set_title("Tiempo total de recorrido: cierre − base\nMisma demanda dentro de cada celda")
    fig.colorbar(im, ax=ax, label="Diferencia de tiempo total (s)"); save(fig, "total_time_matrix")

    groups = ["W_E", "E_W", "N_W", "E_N", "N_E", "W_S"]; pooled = {s: [] for s in groups}
    for row in rows:
        with (out / "combinations" / row["combination"] / "paired_vehicle_impacts.csv").open() as handle:
            for r in csv.DictReader(handle):
                if r["delta_duration_s"]:
                    pooled[r["stream"]].append(float(r["delta_duration_s"]))
    fig, ax = plt.subplots(figsize=(11, 5)); box = ax.boxplot([pooled[s] for s in groups], tick_labels=groups, whis=(5, 95), patch_artist=True, showfliers=True)
    for item, stream in zip(box["boxes"], groups):
        item.set_facecolor(orange if stream == "W_E" else blue); item.set_alpha(.6)
    ax.axhline(0, color="#333", ls="--", lw=.8); ax.set_ylabel("Diferencia emparejada de duración (s)")
    ax.set_title("Distribuciones por movimiento, agrupando los 15 diseños\nIDs repetidos: 2250 pares vehículo-combinación; bigotes P05–P95")
    save(fig, "movement_impact_distributions")

    fig, ax = plt.subplots(figsize=(13, 5)); x = np.arange(len(rows))
    ax.bar(x - .19, [r["W_E_mean_delta_duration_s"] for r in rows], .38, color=blue, label="Media W_E")
    ax.bar(x + .19, [r["W_E_median_delta_duration_s"] for r in rows], .38, color=orange, label="Mediana W_E")
    labels = [("Orig" if r["schedule"] == "original" else r["schedule"].replace("jitter", "")) + f"/{r['offset_s']}" for r in rows]
    ax.set_xticks(x, labels, rotation=45, ha="right"); ax.axhline(0, color="#444", lw=.8)
    ax.set_xlabel("Cronograma / desfase adicional (s)"); ax.set_ylabel("Cierre − base (s por viaje W_E)")
    ax.set_ylim(0, max(r["W_E_median_delta_duration_s"] for r in rows) * 1.3); ax.legend()
    ax.set_title("Impacto directo en los mismos 45 W_E · medias y medianas emparejadas")
    save(fig, "WE_means_and_medians")

    scores = {r["combination"]: sum(c["delta_duration_s"] for c in cases if c["combination"] == r["combination"]) for r in rows}
    original = "original_offset000"; other = [c for c in scores if c != original]
    high = max(other, key=lambda k: (scores[k], k)); low = min((c for c in other if c != high), key=lambda k: (abs(scores[k]), k))
    selected = [original, high, low]
    fig, axes = plt.subplots(3, 2, figsize=(13, 10))
    for i, cid in enumerate(selected):
        with (out / "combinations" / cid / "NE_trajectories.csv").open() as handle:
            trajectory = list(csv.DictReader(handle))
        for j, vid in enumerate(FOCAL_IDS):
            ax = axes[i, j]; case = next(c for c in cases if c["combination"] == cid and c["id"] == vid)
            depart = case["scheduled_depart_s"]; last = 0
            for scenario, label, color in (("base", "Base", blue), ("closure", "Cierre", orange)):
                points = [r for r in trajectory if r["id"] == vid and r["scenario"] == scenario]
                times = [float(r["elapsed_since_scheduled_depart_s"]) for r in points]
                ax.plot(times, [float(r["speed_m_s"]) for r in points], label=label, color=color, lw=1.1)
                last = max(last, max(times))
                arrival = case[scenario + "_first_approach_sample_s"] - depart
                ax.axvline(arrival, color=color, ls=":", lw=.9)
            states = [r for r in xml(out / "combinations" / cid / "base/tls_states.xml.gz").findall("tlsState") if r.get("id") == FOCAL_TLS]
            for state in states:
                t = float(state.get("time")) - depart
                if 0 <= t <= last and state.get("state")[0] in "ry":
                    ax.axvspan(t, t + 1, color="#e8a4a4" if state.get("state")[0] == "r" else "#edcf80", alpha=.20, lw=0)
            ax.set_xlim(0, last + 3); ax.set_title(f"{cid} · {vid} · Δ={case['delta_duration_s']:+.0f} s", fontsize=10)
            ax.set_ylabel("Velocidad (m/s)"); ax.set_xlabel("Segundos desde salida programada"); ax.legend(fontsize=8)
    fig.suptitle("Casos N_E: original, mayor retraso conjunto nuevo y menor impacto conjunto\nFondo rojo/amarillo: señal 4011718406, conexión 0; líneas punteadas: primera muestra en aproximación")
    save(fig, "NE_temporal_cases")
    (folder / "NE_plot_selection.json").write_text(json.dumps({"combinations": selected, "criterion": "original; highest combined focal delay among others; smallest absolute combined focal delay among remaining"}, indent=2) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5)); colors = ["#1768ac", "#d66b17", "#36816c", "#8858a8", "#a43a50"]
    for s, color in zip(schedules, colors):
        axes[0].plot([0, 30, 60], [lookup[s, off]["delta_total_duration_s"] for off in (0, 30, 60)], marker="o", label=s.replace("jitter", ""), color=color)
    axes[0].set_xlabel("Desfase global adicional (s)"); axes[0].set_ylabel("Cambio de tiempo total (s)"); axes[0].set_title("Desfase con cronograma fijo"); axes[0].legend(fontsize=8)
    for off, color in zip((0, 30, 60), colors):
        values = [lookup[s, off]["delta_total_duration_s"] - lookup["original", off]["delta_total_duration_s"] for s in schedules[1:]]
        axes[1].plot([101, 102, 103, 104], values, marker="o", label=f"Offset +{off}s", color=color)
    axes[1].set_xticks([101, 102, 103, 104]); axes[1].set_xlabel("Semilla del cronograma"); axes[1].set_ylabel("Cambio respecto a cronograma original (s)")
    axes[1].set_title("Perturbación con desfase fijo"); axes[1].legend(fontsize=8)
    values = [r["delta_total_duration_s"] for r in rows]
    axes[2].hist(values, bins=7, color=blue, alpha=.75); axes[2].axvline(405, color=orange, ls="--", label="Original: +405s")
    axes[2].axvline(float(np.median(values)), color="#222", label=f"Mediana: {np.median(values):.0f}s")
    axes[2].set_xlabel("Cambio de tiempo total (s)"); axes[2].set_ylabel("Combinaciones (de 15)"); axes[2].set_title("Variabilidad descriptiva"); axes[2].legend(fontsize=8)
    for ax in axes[:2]:
        ax.axhline(0, color="#555", lw=.8); ax.grid(alpha=.15)
    fig.suptitle("Separación de sensibilidades · todos los contrastes usan pares equivalentes")
    save(fig, "variability_summary")
    sources = ["matrix_comparison.csv", "movement_comparison.csv", "NE_cases.csv", "summary.json"]
    (folder / "manifest.json").write_text(json.dumps({"kind": "Static descriptive sensitivity plots",
        "packages": {p: importlib.metadata.version(p) for p in ("matplotlib", "numpy")},
        "sources_sha256": {s: sha256(out / s) for s in sources},
        "figures": [p.name for p in sorted(folder.iterdir()) if p.suffix in (".png", ".svg")]}, indent=2) + "\n")
