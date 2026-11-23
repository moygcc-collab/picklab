# ============================================
# APRENDIZAJE DE PICKLAB
# Cada vez que se actualiza la pagina, este archivo revisa los picks calificados
# y ajusta el motor solo, con limites para no sobre-reaccionar a una mala racha:
#
#  1. Por segmento (ej. "Props NBA Over", "Spreads NFL"): si pegamos menos de lo que
#     el motor esperaba, ese segmento recibe un factor que baja su confianza.
#     Solo con 15+ picks en el segmento, el factor se suaviza segun la muestra y
#     nunca sube la confianza arriba de lo que dice el modelo.
#  2. Pesos del modelo: con 40+ picks que guardaron la probabilidad del mercado y la de
#     las estadisticas, busca el peso que mejor hubiera predicho los resultados
#     (menor log-loss). Se mueve maximo 0.1 por actualizacion y queda entre 0.15 y 0.5.
#
# Escribe ajustes_motor.json (lo lee motor.py) y anota cada cambio en aprendizaje.md.
# Uso: python aprendizaje.py
# ============================================

import json
import math
import os
from datetime import datetime

ARCHIVO = "ajustes_motor.json"
BITACORA = "aprendizaje.md"
MIN_SEGMENTO = 15       # picks minimos para ajustar un segmento
PRIOR_SEGMENTO = 30     # que tanto se suaviza el factor (mas grande = mas prudente)
MIN_PESOS = 40          # picks minimos (con datos guardados) para mover los pesos
PASO_PESO = 0.1         # lo maximo que se mueve un peso por actualizacion
PESO_MIN, PESO_MAX = 0.15, 0.5


def lado_de(h):
    if h.get("lado") in ("Over", "Under"):
        return h["lado"]
    for lado in ("Over", "Under"):
        if " " + lado + " " in " " + h["pick"] + " ":
            return lado
    return "Lado"


def segmentos_de(h):
    # Del mas general al mas especifico
    return [h["tipo"], h["grupo"] + "|" + h["tipo"], h["grupo"] + "|" + h["tipo"] + "|" + lado_de(h)]


def cargar():
    with open("historial.json", encoding="utf-8") as f:
        return [h for h in json.load(f) if h.get("resultado") in ("G", "P")]


def factor_segmento(lista):
    n = len(lista)
    esperado = sum(h["prob"] / 100 for h in lista) / n
    real = len([h for h in lista if h["resultado"] == "G"]) / n
    if n < MIN_SEGMENTO or real >= esperado or esperado <= 0.5:
        return 1.0, esperado, real
    crudo = max(0.5, min(1.0, (real - 0.5) / (esperado - 0.5)))
    # Suavizado por muestra: con 15 picks se mueve un tercio, con 60 se mueve 2/3
    peso = n / (n + PRIOR_SEGMENTO)
    return round(1 - peso * (1 - crudo), 2), esperado, real


def logloss(p, gano):
    p = min(max(p, 0.01), 0.99)
    return -math.log(p if gano else 1 - p)


def mejor_peso(lista, actual):
    # Busca el peso del modelo (estadisticas vs mercado) que mejor predijo los resultados
    con = [h for h in lista if h.get("p_mercado_pct") is not None and h.get("p_estadisticas") is not None]
    if len(con) < MIN_PESOS:
        return actual, len(con), None
    mejor, mejor_ll = actual, None
    for i in range(0, 61):
        w = i / 100
        ll = sum(logloss(w * h["p_estadisticas"] / 100 + (1 - w) * h["p_mercado_pct"] / 100, h["resultado"] == "G")
                 for h in con) / len(con)
        if mejor_ll is None or ll < mejor_ll:
            mejor, mejor_ll = w, ll
    nuevo = max(actual - PASO_PESO, min(actual + PASO_PESO, mejor))
    nuevo = round(max(PESO_MIN, min(PESO_MAX, nuevo)), 2)
    return nuevo, len(con), mejor


def leer_ajustes():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    return {"segmentos": {}, "pesos": {}}


def main():
    import motor
    lista = cargar()
    viejo = leer_ajustes()
    nuevo = {"actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"), "picks": len(lista),
             "segmentos": {}, "pesos": dict(viejo.get("pesos", {})), "detalle": {}}

    # 1. Segmentos
    grupos = {}
    for h in lista:
        for s in segmentos_de(h):
            grupos.setdefault(s, []).append(h)
    for s, hs in sorted(grupos.items()):
        f, esp, real = factor_segmento(hs)
        g = len([h for h in hs if h["resultado"] == "G"])
        nuevo["detalle"][s] = {"picks": len(hs), "record": str(g) + "-" + str(len(hs) - g),
                               "esperado": round(esp * 100, 1), "real": round(real * 100, 1), "factor": f}
        if f < 1.0:
            nuevo["segmentos"][s] = f

    # 2. Pesos
    actual_props = viejo.get("pesos", {}).get("PESO_MAX_PROPS", motor.PESO_MAX_PROPS)
    actual_eq = viejo.get("pesos", {}).get("PESO_MAX_EQUIPOS", motor.PESO_MAX_EQUIPOS)
    w_props, n_props, opt_props = mejor_peso([h for h in lista if h["tipo"] == "Props"], actual_props)
    w_eq, n_eq, opt_eq = mejor_peso([h for h in lista if h["tipo"] != "Props"], actual_eq)
    nuevo["pesos"] = {"PESO_MAX_PROPS": w_props, "PESO_MAX_EQUIPOS": w_eq}
    nuevo["datos_pesos"] = {"props": n_props, "equipos": n_eq}

    # Bitacora: que cambio y por que
    cambios = []
    for s in sorted(set(list(nuevo["segmentos"]) + list(viejo.get("segmentos", {})))):
        a, b = viejo.get("segmentos", {}).get(s, 1.0), nuevo["segmentos"].get(s, 1.0)
        if a != b:
            d = nuevo["detalle"].get(s, {})
            cambios.append("- " + s + ": factor " + str(a) + " -> " + str(b) + " (" + d.get("record", "") +
                           ", esperado " + str(d.get("esperado")) + "%, real " + str(d.get("real")) + "%)")
    for k, a, b, opt, n in [("PESO_MAX_PROPS", actual_props, w_props, opt_props, n_props),
                            ("PESO_MAX_EQUIPOS", actual_eq, w_eq, opt_eq, n_eq)]:
        if a != b:
            cambios.append("- " + k + ": " + str(a) + " -> " + str(b) + " (el mejor con " + str(n) + " picks era " + str(opt) + ")")

    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(nuevo, f, ensure_ascii=False, indent=1)
    if cambios:
        if not os.path.exists(BITACORA):
            with open(BITACORA, "w", encoding="utf-8") as f:
                f.write("# Bitacora de aprendizaje de PickLab\n\nCada ajuste que el motor hizo solo, con el record que lo provoco.\n")
        with open(BITACORA, "a", encoding="utf-8") as f:
            f.write("\n## " + nuevo["actualizado"] + " (" + str(len(lista)) + " picks calificados)\n" + "\n".join(cambios) + "\n")

    print("Aprendizaje con", len(lista), "picks calificados")
    for s, d in sorted(nuevo["detalle"].items(), key=lambda x: -x[1]["picks"]):
        if d["picks"] >= 5:
            print("  ", s.ljust(24), d["record"].ljust(6), "esperado", d["esperado"], "real", d["real"], "-> factor", d["factor"])
    print("Pesos:", nuevo["pesos"], "| picks con datos para pesos:", nuevo["datos_pesos"])
    print("Cambios:" if cambios else "Sin cambios nuevos.")
    for c in cambios:
        print(c)
    return nuevo


if __name__ == "__main__":
    main()
