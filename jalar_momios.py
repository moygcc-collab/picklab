# ============================================
# JALAR MOMIOS DE THE ODDS API
# Lo corre el workflow "jalar_momios" de GitHub (con el secreto ODDS_API_KEY).
# Guarda en datos/:
#   ligas.json       ligas activas
#   lineas.json      spreads y totales de todas las ligas (todas las casas)
#   props.json       props de jugadores de NBA, NFL y NHL
#   marcadores.json  resultados de los ultimos 3 dias (para calificar solo)
#   uso_api.json     creditos gastados y restantes
#
# Gasto aproximado por corrida: ~60 lineas + ~150 props + ~35 marcadores = ~250 creditos.
# Con el plan de 20,000 al mes alcanza para correr diario y sobra.
# ============================================

import json
import os
from datetime import datetime, timedelta, timezone
import requests
import config

URL_BASE = "https://api.the-odds-api.com/v4"
ERRORES = []
USO = {"restantes": None, "usados": None}


def guardar(nombre_archivo, datos):
    os.makedirs("datos", exist_ok=True)
    with open("datos/" + nombre_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=1)
    print("Guardado:", nombre_archivo)


def pedir(url, parametros):
    parametros["apiKey"] = config.ODDS_API_KEY
    try:
        respuesta = requests.get(url, params=parametros, timeout=30)
    except requests.RequestException as e:
        ERRORES.append("Conexion: " + str(e)[:150])
        return None
    if respuesta.headers.get("x-requests-remaining"):
        USO["restantes"] = respuesta.headers.get("x-requests-remaining")
        USO["usados"] = respuesta.headers.get("x-requests-used")
    if respuesta.status_code != 200:
        error = "The Odds API " + str(respuesta.status_code) + ": " + respuesta.text[:200]
        print("  ERROR", error)
        if error not in ERRORES:
            ERRORES.append(error)
        return None
    return respuesta.json()


def ligas_activas():
    # Esta lista es gratis: nos dice que ligas estan en temporada
    deportes = pedir(URL_BASE + "/sports", {})
    activas = {}
    for d in deportes or []:
        if not d.get("active") or d.get("has_outrights"):
            continue
        clave = d["key"]
        if clave in config.LIGAS:
            grupo, nombre, regiones = config.LIGAS[clave]
            activas[clave] = {"grupo": grupo, "liga": nombre, "regiones": regiones}
        elif (clave.startswith("tennis_atp") or clave.startswith("tennis_wta")) and "doubles" not in clave:
            activas[clave] = {"grupo": "Tenis", "liga": d["title"], "regiones": config.REGION_TENIS}
    return activas


def dentro(iso, horas):
    t = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    ahora = datetime.now(timezone.utc)
    return ahora < t < ahora + timedelta(hours=horas)


def jalar_lineas(activas):
    todas = {}
    for clave, info in activas.items():
        print("Lineas de", clave)
        datos = pedir(URL_BASE + "/sports/" + clave + "/odds", {
            "regions": info["regiones"], "markets": config.MERCADOS, "oddsFormat": "american",
        }) or []
        todas[clave] = [ev for ev in datos if dentro(ev["commence_time"], config.DIAS_ADELANTE * 24)]
    return todas


def jalar_props(activas):
    props = {}
    for clave, ajustes in config.PROPS.items():
        if clave not in activas:
            continue
        eventos = pedir(URL_BASE + "/sports/" + clave + "/events", {}) or []
        eventos = [ev for ev in eventos if dentro(ev["commence_time"], ajustes["horas"])][:ajustes["partidos"]]
        props[clave] = []
        for ev in eventos:
            print("Props de", ev["away_team"], "@", ev["home_team"])
            datos = pedir(URL_BASE + "/sports/" + clave + "/events/" + ev["id"] + "/odds", {
                "regions": "us", "markets": ",".join(ajustes["mercados"]), "oddsFormat": "american",
            })
            if datos:
                props[clave].append(datos)
    return props


def jalar_marcadores(activas):
    marcadores = {}
    for clave in activas:
        datos = pedir(URL_BASE + "/sports/" + clave + "/scores", {"daysFrom": 3})
        marcadores[clave] = [ev for ev in (datos or []) if ev.get("completed")]
    return marcadores


def main():
    llave = config.ODDS_API_KEY.strip()
    if llave.startswith("PEGA_AQUI") or llave == "":
        print("No hay llave ODDS_API_KEY. No se jala nada.")
        return
    print("Largo de la llave:", len(llave))
    activas = ligas_activas()
    if not activas:
        print("No se pudieron leer las ligas:", ERRORES)
        guardar("errores_momios.json", ERRORES)
        raise SystemExit(1)
    lineas = jalar_lineas(activas)
    props = jalar_props(activas)
    marcadores = jalar_marcadores(activas)
    guardar("ligas.json", activas)
    guardar("lineas.json", lineas)
    guardar("props.json", props)
    guardar("marcadores.json", marcadores)
    guardar("errores_momios.json", ERRORES)
    USO["fecha"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    USO["partidos"] = sum(len(v) for v in lineas.values())
    guardar("uso_api.json", USO)
    print("Partidos con lineas:", USO["partidos"], "| creditos restantes:", USO["restantes"])


if __name__ == "__main__":
    main()
