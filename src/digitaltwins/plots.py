"""Figuras estáticas de geometrías y estados sintéticos, sin servicios de mapas."""

from collections import defaultdict
import importlib.metadata
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET


def render(net, out, spec, candidates):
    folder = out / "visual"; folder.mkdir()
    os.environ["MPLCONFIGDIR"] = str(folder / ".mplconfig")
    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.collections import LineCollection
    from matplotlib.colors import LogNorm
    from matplotlib.lines import Line2D
    from matplotlib.patches import Rectangle
    from pyproj import Transformer

    colors = ["#1768ac", "#e07a16", "#8456a5", "#268475", "#c23b53", "#705b36"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    def draw(ax, ids=None, color="#cbd1d8", width=0.7, **kwargs):
        ids = sorted(net.edges if ids is None else ids)
        item = LineCollection([net.shapes[e] for e in ids], colors=color, linewidths=width, **kwargs)
        ax.add_collection(item); ax.autoscale(); ax.set_aspect("equal")
        ax.set_xlabel("Este relativo (m)"); ax.set_ylabel("Norte relativo (m)")
        return item

    def save(fig, name):
        fig.text(0.01, 0.012, "Simulación sintética · OSM © OpenStreetMap contributors / Geofabrik · Sin observaciones reales", fontsize=8, color="#4b5563")
        fig.tight_layout(rect=(0,0.045,1,.97))
        fig.savefig(folder/(name+".png"), dpi=160)
        fig.savefig(folder/(name+".svg"))
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10,8))
    for i, group in enumerate(net.weak):
        draw(ax, group, colors[i], 1.35)
    offset = [float(x) for x in net.xml.find("location").get("netOffset").split(",")]
    # El bbox experimental es el fijado por la intervención 002, no el nacional.
    ref = Path(json.loads((out/"manifest.json").read_text())["reference_manifest"])
    b = json.loads(ref.read_text())["bbox_crs84"]
    transform = Transformer.from_crs("EPSG:4326","EPSG:32616",always_xy=True)
    x1,y1 = transform.transform(b[0],b[1]); x2,y2 = transform.transform(b[2],b[3])
    ax.add_patch(Rectangle((x1+offset[0],y1+offset[1]), x2-x1,y2-y1,fill=False,edgecolor="#222",linestyle="--",linewidth=1.1))
    ax.set_title("Red original conservada y componentes passenger\nEl recorte conserva vías completas fuera del rectángulo")
    handles=[Line2D([0],[0],color=colors[i],lw=3,label=f"Componente {i}: {len(group)} enlaces") for i,group in enumerate(net.weak)]
    handles.append(Line2D([0],[0],color="#222",ls="--",label="Ventana solicitada"))
    ax.legend(handles=handles,loc="lower right")
    ax.annotate("Héroes / 49 Avenida\n21 enlaces",(150,850),xytext=(400,1000),arrowprops={"arrowstyle":"->","color":colors[1]},color=colors[1])
    small_points=[p for e in net.weak[2] for p in net.shapes[e]]
    small_center=(sum(p[0] for p in small_points)/len(small_points),sum(p[1] for p in small_points)/len(small_points))
    ax.annotate("Residencial sin nombre\n8 enlaces",small_center,xytext=(790,1060),arrowprops={"arrowstyle":"->","color":colors[2]},color=colors[2])
    save(fig,"network_components")

    movements=json.loads((out/"controlled_movements.json").read_text())["routes_by_stream"]
    fig,ax=plt.subplots(figsize=(12,8));draw(ax)
    for i, stream in enumerate(spec["streams"]):
        draw(ax,movements[stream["id"]],colors[i],2.3 if i<2 else 1.5,alpha=.8)
        point=net.shapes[stream["from"]][0]
        ax.scatter(*point,color=colors[i],s=35,zorder=5)
    signals=[j for j in net.junctions.values() if j.get("type","").startswith("traffic_light")]
    ax.scatter([float(j.get("x")) for j in signals],[float(j.get("y")) for j in signals],s=28,facecolors="white",edgecolors="#19724a",zorder=6)
    for i,c in enumerate(candidates):
        draw(ax,[c["edge"]],"#b000a0",4.5)
        shape=net.shapes[c["edge"]];x,y=shape[len(shape)//2]
        ax.annotate(f'C{i+1}: {c["edge"]}',(x,y),xytext=(x+70,y+90*(1 if i==0 else -1)),arrowprops={"arrowstyle":"->"},fontsize=9,bbox={"facecolor":"white","alpha":.85,"edgecolor":"none"})
    ax.set_title("Seis movimientos explícitos del escenario controlado\nC1 y C2 son candidatos futuros; aquí permanecen abiertos")
    ax.legend(handles=[Line2D([0],[0],color=colors[i],lw=3,label=f'{s["id"]}: {s["rate_veh_h"]} veh/h') for i,s in enumerate(spec["streams"])] +
              [Line2D([0],[0],marker="o",color="white",markeredgecolor="#19724a",label="Semáforo sintético")],loc="lower right")
    save(fig,"controlled_routes")

    fig,axes=plt.subplots(1,2,figsize=(15,6))
    for ax,c in zip(axes,candidates):
        draw(ax)
        od=next(v for v in c["ODs"] if v["baseline_uses_candidate"])
        draw(ax,od["baseline_route"],colors[0],2)
        draw(ax,od["alternative_route_without_candidate"]["edges"],colors[1],2,linestyles="--")
        draw(ax,[c["edge"]],"#b000a0",4)
        ax.set_title(f'{c["edge"]} · OD {od["stream"]}\nConsulta topológica, sin simulación de cierre')
        ax.legend(handles=[Line2D([0],[0],color=colors[0],lw=2,label="Ruta base"),Line2D([0],[0],color=colors[1],lw=2,ls="--",label="Alternativa estática"),Line2D([0],[0],color="#b000a0",lw=4,label="Candidato")],loc="lower right")
    save(fig,"closure_candidates")

    audit=json.loads((out/"edge_attribute_audit.json").read_text())["edges"]
    fig,ax=plt.subplots(figsize=(10,8));draw(ax)
    for value,color,label in (("high", "#bd3749", "Default en rutas usadas"),("review","#e6a648","Otro default")):
        draw(ax,[r["edge"] for r in audit if r["priority"]==value],color,2)
    for jid in ("1538961972","1901675110"):
        if jid in net.junctions:
            j=net.junctions[jid];x,y=float(j.get("x")),float(j.get("y"));ax.scatter(x,y,marker="D",s=45,color="#482878")
            ax.annotate(jid,(x,y),xytext=(x+100,y+45),arrowprops={"arrowstyle":"->"},fontsize=8)
    ax.set_title("Prioridad de revisión de atributos inferidos\nDiamantes: nodos con advertencias de forma")
    ax.legend(handles=[Line2D([0],[0],color="#bd3749",lw=3,label="Default y ruta 002/003 o corredor"),Line2D([0],[0],color="#e6a648",lw=3,label="Default en otros enlaces"),Line2D([0],[0],color="#cbd1d8",lw=3,label="Atributos de fuente disponibles")],loc="lower right")
    save(fig,"attribute_priorities")

    metrics=json.loads((out/"base/metrics.json").read_text())
    steps=ET.parse(out/"base/summary.xml").getroot().findall("step");time=[float(s.get("time"))/60 for s in steps]
    fig,axes=plt.subplots(2,2,figsize=(13,8))
    axes[0,0].plot(time,[int(s.get("running")) for s in steps],label="En red",color=colors[0])
    axes[0,0].plot(time,[int(s.get("halting")) for s in steps],label="Detenidos",color=colors[1]);axes[0,0].set_ylabel("Vehículos (veh)");axes[0,0].legend()
    for key,label,color in (("inserted","Ingresados",colors[0]),("arrived","Completados",colors[1])):
        axes[0,1].plot(time,[int(s.get(key)) for s in steps],label=label,color=color)
    axes[0,1].set_ylabel("Vehículos acumulados (veh)");axes[0,1].legend()
    data=ET.parse(out/"base/edge_data.xml").getroot().findall("interval")
    for i,c in enumerate(candidates):
        xs=[];ys=[]
        for interval in data:
            e=next(e for e in interval.findall("edge") if e.get("id")==c["edge"])
            xs.append(float(interval.get("begin"))/60);ys.append(float(e.get("sampledSeconds",0))/(float(interval.get("end"))-float(interval.get("begin"))))
        axes[1,0].step(xs,ys,where="post",label=c["edge"],color=colors[i])
    axes[1,0].set_ylabel("Vehículos medios por enlace (veh)");axes[1,0].legend(fontsize=8)
    ids=[s["id"] for s in spec["streams"]];a=metrics["per_stream"]
    for i,(field,label) in enumerate((("mean_duration_s","Recorrido"),("mean_time_loss_s","timeLoss"),("mean_waiting_time_s","Detenido"))):
        axes[1,1].bar([j+(i-1)*.25 for j in range(len(ids))],[a[s][field] for s in ids],width=.24,label=label,color=colors[i])
    axes[1,1].set_xticks(range(len(ids)),ids);axes[1,1].set_ylabel("Media por vehículo (s)");axes[1,1].legend(fontsize=8)
    for ax in (axes[0,0],axes[0,1],axes[1,0]):ax.set_xlabel("Tiempo desde el inicio (min)");ax.grid(alpha=.15)
    fig.suptitle("Estados y métricas SUMO sintéticos · escenario controlado, semilla 42")
    save(fig,"traffic_indicators")

    max_occ=defaultdict(float)
    for interval in data:
        for edge in interval.findall("edge"):max_occ[edge.get("id")]=max(max_occ[edge.get("id")],float(edge.get("occupancy",0)))
    fig,ax=plt.subplots(figsize=(10,8));draw(ax)
    used=[e for e,v in max_occ.items() if v>0]
    values=[max_occ[e] for e in used]
    lines=LineCollection([net.shapes[e] for e in used],array=np.array(values),cmap="magma",norm=LogNorm(vmin=min(values),vmax=max(values)),linewidths=2.5)
    ax.add_collection(lines);fig.colorbar(lines,ax=ax,label="Máxima ocupación en intervalo de 60 s (%) · escala log")
    ax.set_title("Ocupación por enlace reportada por SUMO\nSin recortar valores; revisar la interpretación en segmentos muy cortos")
    save(fig,"edge_occupancy")
    (folder/"manifest.json").write_text(json.dumps({"kind":"Static scientific figures from local SUMO XML, not GUI screenshots or observed traffic.",
        "packages":{p:importlib.metadata.version(p) for p in ("matplotlib","pyproj","numpy")},
        "figures":[p.name for p in sorted(folder.glob('*')) if p.suffix in ('.png','.svg')]},indent=2)+'\n')
