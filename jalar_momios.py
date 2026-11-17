# ============================================
# PASO 1: Jalar momios de The Odds API
# Guarda: datos/lineas.json y datos/props.json
# ============================================

import json
import requests
import config

URL_BASE = "https://api.the-odds-api.com/v4"


def guardar(nombre_archivo, datos):
    with open("datos/" + nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=2)
    print("Guardado:", nombre_archivo)


def pedir(url, parametros):
    parametros["apiKey"] = config.ODDS_API_KEY
    respuesta = requests.get(url, params=parametros, timeout=30)
    print("  Creditos restantes:", respuesta.headers.get("x-requests-remaining"))
    if respuesta.status_code != 200:
        print("  ERROR", respuesta.status_code, respuesta.text)
        return None
    return respuesta.json()


def ligas_activas():
    # Esta lista es gratis: nos dice que ligas estan en temporada
    deportes = pedir(URL_BASE + "/sports", {})
    activas = {}
    if not deportes:
        return activas
    for d in deportes:
        if not d.get("active") or d.get("has_outrights"):
            continue
        clave = d["key"]
        grupo = config.GRUPOS.get(d["group"])
        if grupo is None:
            continue
        if clave in config.LIGAS:
            activas[clave] = {"grupo": grupo, "liga": config.LIGAS[clave]}
        elif clave.startswith("tennis_atp") or clave.startswith("tennis_wta"):
            activas[clave] = {"grupo": "Tenis", "liga": d["title"]}
    guardar("ligas.json", activas)
    return activas


def jalar_lineas(activas):
    # Spreads y totales: 2 creditos por liga
    todas = {}
    for clave in activas:
        print("Pidiendo lineas de", clave)
        datos = pedir(URL_BASE + "/sports/" + clave + "/odds", {
            "regions": config.REGION,
            "markets": "spreads,totals",
            "oddsFormat": "american",
        })
        todas[clave] = datos or []
    guardar("lineas.json", todas)


def jalar_props(activas):
    props = {}
    for clave in config.PROPS:
        if clave not in activas:
            continue
        ajustes = config.PROPS[clave]
        print("Pidiendo partidos de", clave)
        eventos = pedir(URL_BASE + "/sports/" + clave + "/events", {}) or []
        props[clave] = []
        for evento in eventos[:ajustes["partidos"]]:
            print("  Props de", evento["away_team"], "@", evento["home_team"])
            datos = pedir(URL_BASE + "/sports/" + clave + "/events/" + evento["id"] + "/odds", {
                "regions": config.REGION,
                "markets": ",".join(ajustes["mercados"]),
                "oddsFormat": "american",
            })
            if datos:
                props[clave].append(datos)
    guardar("props.json", props)


def main():
    activas = ligas_activas()
    jalar_lineas(activas)
    jalar_props(activas)


if __name__ == "__main__":
    main()
