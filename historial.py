# ============================================
# HISTORIAL DE PICKLAB
# Guarda cada pick publicado y lleva el record (ganados, perdidos, unidades).
#
# Uso:
#  - edicion.py lo llama solo para guardar los picks nuevos.
#  - Para calificar: escribe el resultado en resultados.py y corre
#      python historial.py
#    Eso actualiza historial.json y escribe web/historial.js (lo lee la pagina).
# ============================================

import json
import os
from datetime import datetime, timezone
from calcular_picks import a_decimal, prob_implicita

ARCHIVO = "historial.json"
SALIDA_WEB = "web/historial.js"


def clave_de(pick):
    # La clave identifica el pick: dia del partido | partido | pick
    return pick["fecha"][:10] + " | " + pick["partido"] + " | " + pick["pick"]


def cargar():
    if not os.path.exists(ARCHIVO):
        return []
    with open(ARCHIVO, encoding="utf-8") as f:
        return json.load(f)


def guardar_archivo(lista):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=1)


def guardar_edicion(picks, edicion):
    # Agrega los picks de una edicion. Si la misma edicion se vuelve a correr,
    # quita los pendientes que ya no salieron y actualiza los que siguen.
    lista = cargar()
    claves_nuevas = [clave_de(p) for p in picks]

    # Solo se quitan los que todavia no empiezan: lo que ya se jugo se queda para calificarlo
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lista = [h for h in lista
             if not (h["edicion"] == edicion and h["resultado"] is None and h["clave"] not in claves_nuevas
                     and h["fecha"] > ahora)]

    por_clave = {}
    for h in lista:
        por_clave[h["clave"]] = h

    for p in picks:
        clave = clave_de(p)
        nuevo = {
            "clave": clave, "edicion": edicion, "fecha": p["fecha"],
            "grupo": p["grupo"], "liga": p["liga"], "tipo": p["tipo"],
            "partido": p["partido"], "pick": p["pick"], "momio": p["momio"],
            "unidades": p["unidades"], "prob": p["prob"], "ventaja": p["ventaja"],
            "resultado": None,
        }
        # Datos extra: nivel de confianza y lo necesario para calificar solo
        for k in ["nivel", "score", "api_id", "liga_clave", "local", "visitante", "linea_num", "lado", "equipo_pick",
                  "mercado", "jugador", "linea", "casa", "p_mercado_pct", "p_estadisticas", "proyeccion", "senales"]:
            if k in p:
                nuevo[k] = p[k]
        viejo = por_clave.get(clave)
        if viejo is None:
            lista.append(nuevo)
        elif viejo["resultado"] is None and viejo["fecha"] > datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"):
            # Ya estaba publicado y el partido no empieza: el momio con el que se publico se queda,
            # y el de ahora se guarda como "ultimo momio visto" (sirve para medir si le ganamos al cierre)
            if p["momio"] != viejo["momio"]:
                viejo["momio_cierre"] = p["momio"]
                viejo["cierre_fuente"] = "ultima corrida antes del partido"
            for k in ["nivel", "score"]:
                if k in nuevo:
                    viejo[k] = nuevo[k]
        # Si ya estaba en una edicion anterior, se queda el original

    lista.sort(key=lambda h: (h["fecha"], h["clave"]))
    guardar_archivo(lista)
    return lista


def ganancia(h):
    if h["resultado"] == "G":
        return h["unidades"] * (a_decimal(h["momio"]) - 1)
    if h["resultado"] == "P":
        return -h["unidades"]
    return 0


def resumen(lista):
    g = len([h for h in lista if h["resultado"] == "G"])
    p = len([h for h in lista if h["resultado"] == "P"])
    e = len([h for h in lista if h["resultado"] == "E"])
    arriesgado = sum(h["unidades"] for h in lista if h["resultado"] in ("G", "P"))
    neto = sum(ganancia(h) for h in lista)
    return {
        "ganados": g, "perdidos": p, "empates": e,
        "acierto": round(100 * g / (g + p), 1) if g + p > 0 else None,
        "unidades": round(neto, 2),
        "roi": round(100 * neto / arriesgado, 1) if arriesgado > 0 else None,
        "prob_promedio": round(sum(h["prob"] for h in lista) / len(lista), 1) if lista else None,
    }


def calificar_auto(lista):
    # Califica spreads y totales con los marcadores de The Odds API (datos/marcadores.json)
    ruta = "datos/marcadores.json"
    if not os.path.exists(ruta):
        return lista
    with open(ruta, encoding="utf-8") as f:
        marcadores = json.load(f)
    por_id = {}
    for eventos in marcadores.values():
        for ev in eventos or []:
            if ev.get("completed") and ev.get("scores"):
                por_id[ev["id"]] = dict((s["name"], float(s["score"])) for s in ev["scores"])
    for h in lista:
        if h["resultado"] is not None or h.get("api_id") not in por_id or h.get("linea_num") is None:
            continue
        pts = por_id[h["api_id"]]
        if h["tipo"] == "Totales":
            total = sum(pts.values())
            if total == h["linea_num"]:
                h["resultado"] = "E"
            elif (total > h["linea_num"]) == (h.get("lado") == "Over"):
                h["resultado"] = "G"
            else:
                h["resultado"] = "P"
        elif h["tipo"] == "Spreads" and h.get("equipo_pick") in pts:
            rival = [e for e in pts if e != h["equipo_pick"]][0]
            margen = pts[h["equipo_pick"]] - pts[rival] + h["linea_num"]
            h["resultado"] = "E" if margen == 0 else ("G" if margen > 0 else "P")
        if h["resultado"] is not None:
            h["auto"] = True
            print("Calificado solo:", h["clave"], "->", h["resultado"])
    guardar_archivo(lista)
    return lista


def aplicar_resultados(lista):
    try:
        from resultados import RESULTADOS
    except ImportError:
        RESULTADOS = {}
    no_encontradas = []
    claves = [h["clave"] for h in lista]
    for clave, res in RESULTADOS.items():
        res = res.upper()
        if res not in ("G", "P", "E"):
            print("OJO: resultado raro para", clave, "->", res, "(usa G, P o E)")
            continue
        if clave not in claves:
            no_encontradas.append(clave)
            continue
        for h in lista:
            if h["clave"] == clave:
                h["resultado"] = res
    for c in no_encontradas:
        print("OJO: esta clave no esta en el historial:", c)
    return lista


def aplicar_cierres(lista):
    # Momios de cierre que se pegan a mano en resultados.py (CIERRE = {clave: momio})
    try:
        from resultados import CIERRE
    except ImportError:
        CIERRE = {}
    for h in lista:
        if h["clave"] in CIERRE:
            h["momio_cierre"] = CIERRE[h["clave"]]
            h["cierre_fuente"] = "manual"
    return lista


def clv(h):
    # Le ganamos al cierre si nuestro momio paga mas que el de cierre.
    # CLV = probabilidad del cierre - probabilidad de nuestro momio (en puntos %). Positivo = bien.
    if h.get("momio_cierre") is None:
        return None
    return round(100 * (prob_implicita(h["momio_cierre"]) - prob_implicita(h["momio"])), 1)


def resumen_clv(lista):
    con = [h for h in lista if clv(h) is not None]
    if not con:
        return {"picks": 0, "a_favor": 0, "en_contra": 0, "promedio": None}
    valores = [clv(h) for h in con]
    return {"picks": len(con), "a_favor": len([v for v in valores if v > 0]),
            "en_contra": len([v for v in valores if v < 0]), "promedio": round(sum(valores) / len(valores), 2)}


def leer_aprendizaje():
    # Ultimos ajustes que el motor hizo solo (aprendizaje.py)
    cambios = []
    if os.path.exists("aprendizaje.md"):
        with open("aprendizaje.md", encoding="utf-8") as f:
            bloques = f.read().split("\n## ")[1:]
        for b in bloques[-3:]:
            lineas = b.strip().split("\n")
            cambios.append({"titulo": lineas[0], "cambios": [l[2:] for l in lineas[1:] if l.startswith("- ")]})
    return list(reversed(cambios))


def escribir_web(lista):
    lista = aplicar_cierres(lista)
    for h in lista:
        h["clv"] = clv(h)
    calificados = [h for h in lista if h["resultado"] is not None]
    pendientes = [h for h in lista if h["resultado"] is None]

    # Unidades acumuladas pick por pick (para la grafica)
    serie = []
    acumulado = 0
    for h in sorted(calificados, key=lambda x: x["fecha"]):
        acumulado += ganancia(h)
        serie.append({"fecha": h["fecha"][:10], "u": round(acumulado, 2)})

    por_grupo = {}
    for grupo in sorted(set(h["grupo"] for h in calificados)):
        por_grupo[grupo] = resumen([h for h in calificados if h["grupo"] == grupo])
    por_nivel = {}
    for nivel in sorted(set(h.get("nivel", "-") for h in calificados)):
        por_nivel[nivel] = resumen([h for h in calificados if h.get("nivel", "-") == nivel])
    por_tipo = {}
    for tipo in sorted(set(h["tipo"] for h in calificados)):
        por_tipo[tipo] = resumen([h for h in calificados if h["tipo"] == tipo])

    recientes = sorted(calificados, key=lambda x: x["fecha"], reverse=True)
    for h in recientes:
        h["neto"] = round(ganancia(h), 2)

    salida = {
        "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": resumen(calificados),
        "pendientes": len(pendientes),
        "publicados": len(lista),
        "serie": serie,
        "por_grupo": por_grupo,
        "por_tipo": por_tipo,
        "por_nivel": por_nivel,
        "clv": resumen_clv(lista),
        "aprendizaje": leer_aprendizaje(),
        "calificados": recientes,
    }
    with open(SALIDA_WEB, "w", encoding="utf-8") as f:
        f.write("window.HISTORIAL = ")
        f.write(json.dumps(salida, ensure_ascii=False, indent=1))
        f.write(";\n")
    return salida


def main():
    lista = aplicar_resultados(calificar_auto(cargar()))
    guardar_archivo(lista)
    salida = escribir_web(lista)
    t = salida["total"]
    print("Record:", t["ganados"], "-", t["perdidos"], "-", t["empates"],
          "| acierto", t["acierto"], "% | unidades", t["unidades"], "| ROI", t["roi"], "%")
    c = salida["clv"]
    if c["picks"]:
        print("Contra el cierre:", c["a_favor"], "a favor,", c["en_contra"], "en contra | CLV promedio", c["promedio"], "puntos")

    # Lista de pendientes cuyo partido ya empezo, para calificarlos
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    listos = [h for h in lista if h["resultado"] is None and h["fecha"] < ahora]
    if listos:
        print("\nPendientes por calificar (copia la clave a resultados.py):")
        for h in listos:
            print('    "' + h["clave"] + '": "",')
    print("\nPendientes que todavia no se juegan:", len([h for h in lista if h["resultado"] is None]) - len(listos))


if __name__ == "__main__":
    main()
