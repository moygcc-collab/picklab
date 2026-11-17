# ============================================
# PASO 2: Jalar estadisticas de jugadores NBA de API-Sports
# Usa datos/props.json para saber que equipos juegan
# Guarda: datos/stats_nba.json
# ============================================

import json
import os
import requests
import config

URL_BASE = "https://v2.nba.api-sports.io"


def pedir(ruta, parametros):
    encabezados = {"x-apisports-key": config.API_SPORTS_KEY}
    respuesta = requests.get(URL_BASE + ruta, headers=encabezados, params=parametros, timeout=30)
    datos = respuesta.json()
    if datos.get("errors"):
        print("  ERROR:", datos["errors"])
        return []
    return datos.get("response", [])


def cargar_equipos():
    # La lista de equipos casi no cambia, la guardamos para no gastar requests
    ruta = "datos/equipos_nba.json"
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as archivo:
            return json.load(archivo)

    print("Pidiendo equipos de NBA")
    equipos = {}
    for equipo in pedir("/teams", {}):
        if equipo.get("nbaFranchise"):
            equipos[equipo["name"]] = equipo["id"]
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(equipos, archivo, indent=2)
    return equipos


def jugo(stat):
    # Regresa False si el jugador no jugo ese partido
    minutos = stat.get("min")
    if stat.get("points") is None:
        return False
    if minutos is None or minutos == "" or minutos == "0" or minutos == "0:00" or minutos == "-":
        return False
    return True


def main():
    with open("datos/props.json", encoding="utf-8") as archivo:
        props = json.load(archivo).get("basketball_nba", [])

    # Equipos que juegan en los partidos con props
    nombres_equipos = []
    for partido in props:
        if partido["home_team"] not in nombres_equipos:
            nombres_equipos.append(partido["home_team"])
        if partido["away_team"] not in nombres_equipos:
            nombres_equipos.append(partido["away_team"])

    equipos = cargar_equipos()
    jugadores = {}

    for nombre in nombres_equipos:
        if nombre not in equipos:
            print("No encontre el equipo", nombre, "en API-Sports")
            continue
        print("Pidiendo estadisticas de", nombre)
        stats = pedir("/players/statistics", {"team": equipos[nombre], "season": config.TEMPORADA_NBA})

        for stat in stats:
            if not jugo(stat):
                continue
            jugador = stat["player"]["firstname"] + " " + stat["player"]["lastname"]
            if jugador not in jugadores:
                jugadores[jugador] = {"equipo": nombre, "partidos": []}
            jugadores[jugador]["partidos"].append({
                "juego": stat["game"]["id"],
                "puntos": stat.get("points") or 0,
                "rebotes": stat.get("totReb") or 0,
                "asistencias": stat.get("assists") or 0,
            })

    # Ordenamos los partidos de cada jugador del mas viejo al mas nuevo
    for jugador in jugadores:
        jugadores[jugador]["partidos"].sort(key=lambda p: p["juego"])

    with open("datos/stats_nba.json", "w", encoding="utf-8") as archivo:
        json.dump(jugadores, archivo, indent=2)
    print("Guardado: stats_nba.json con", len(jugadores), "jugadores")


if __name__ == "__main__":
    main()
