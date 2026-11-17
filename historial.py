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
from calcular_picks import a_decimal

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

    lista = [h for h in lista
             if not (h["edicion"] == edicion and h["resultado"] is None and h["clave"] not in claves_nuevas)]

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
        viejo = por_clave.get(clave)
        if viejo is None:
            lista.append(nuevo)
        elif viejo["resultado"] is None and viejo["edicion"] == edicion:
            viejo.update(nuevo)
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


def escribir_web(lista):
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
        "calificados": recientes,
    }
    with open(SALIDA_WEB, "w", encoding="utf-8") as f:
        f.write("window.HISTORIAL = ")
        f.write(json.dumps(salida, ensure_ascii=False, indent=1))
        f.write(";\n")
    return salida


def main():
    lista = aplicar_resultados(cargar())
    guardar_archivo(lista)
    salida = escribir_web(lista)
    t = salida["total"]
    print("Record:", t["ganados"], "-", t["perdidos"], "-", t["empates"],
          "| acierto", t["acierto"], "% | unidades", t["unidades"], "| ROI", t["roi"], "%")

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
