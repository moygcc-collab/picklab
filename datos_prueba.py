# ============================================
# Crea datos FALSOS con el mismo formato que las APIs
# Sirve para ver la pagina funcionando sin llaves
# Uso: python datos_prueba.py  y luego  python calcular_picks.py
# ============================================

import json
import random

random.seed(7)

CASAS = ["DraftKings", "FanDuel", "BetMGM", "Caesars"]

EQUIPOS = {
    "americanfootball_nfl": ["Halcones", "Toros", "Lobos", "Piratas", "Truenos", "Coyotes"],
    "basketball_nba": ["Rayos", "Osos", "Aguilas", "Tiburones", "Leones", "Cometas"],
    "icehockey_nhl": ["Glaciares", "Vikingos", "Linces", "Bisontes"],
    "soccer_mexico_ligamx": ["Club Norte", "Club Sur", "Club Centro", "Club Golfo"],
    "soccer_epl": ["Northside FC", "Riverside FC"],
    "mma_mixed_martial_arts": ["Peleador Rojo", "Peleador Azul"],
    "tennis_atp_finals": ["Tenista Uno", "Tenista Dos"],
}

FECHAS = ["2026-11-20T01:00:00Z", "2026-11-21T00:30:00Z", "2026-11-22T18:00:00Z"]


def momio_cerca(base):
    return base + random.choice([-10, -5, 0, 5, 10])


def mercado(clave, linea, nombres, total):
    salida = {"key": clave, "outcomes": []}
    for i in range(2):
        precio = momio_cerca(-110)
        if total:
            salida["outcomes"].append({"name": nombres[i], "price": precio, "point": linea})
        else:
            punto = linea if i == 0 else -linea
            salida["outcomes"].append({"name": nombres[i], "price": precio, "point": punto})
    return salida


def evento(clave, local, visitante, n):
    spread = random.choice([-7.5, -3.5, -2.5, -1.5, 1.5, 4.5])
    total = random.choice([2.5, 5.5, 44.5, 47.5, 221.5, 228.5])
    libros = []
    for casa in CASAS:
        libros.append({
            "key": casa.lower(),
            "title": casa,
            "markets": [
                mercado("spreads", spread, [local, visitante], False),
                mercado("totals", total, ["Over", "Under"], True),
            ],
        })
    return {
        "id": clave + "_" + str(n),
        "sport_key": clave,
        "commence_time": random.choice(FECHAS),
        "home_team": local,
        "away_team": visitante,
        "bookmakers": libros,
    }


lineas = {}
for clave in EQUIPOS:
    equipos = EQUIPOS[clave]
    lineas[clave] = []
    for i in range(0, len(equipos), 2):
        lineas[clave].append(evento(clave, equipos[i], equipos[i + 1], i))

# ---- Props NBA y estadisticas ----
props = []
stats = {}
MERCADOS = {"player_points": ("puntos", 24.5), "player_rebounds": ("rebotes", 8.5), "player_assists": ("asistencias", 6.5)}
juegos_nba = lineas["basketball_nba"]
for j in range(len(juegos_nba)):
    juego = juegos_nba[j]
    jugadores = []
    for k in range(4):
        equipo = juego["home_team"] if k < 2 else juego["away_team"]
        nombre = "Jugador " + equipo + " " + str(k + 1)
        jugadores.append(nombre)
        partidos = []
        for g in range(15):
            partidos.append({
                "juego": 1000 + g,
                "puntos": max(0, round(random.gauss(24 + k * 2 - 3, 6))),
                "rebotes": max(0, round(random.gauss(8 + k - 1.5, 3))),
                "asistencias": max(0, round(random.gauss(6 - k + 1, 2.5))),
            })
        stats[nombre] = {"equipo": equipo, "partidos": partidos}

    libros = []
    for casa in CASAS:
        mercados = []
        for clave in MERCADOS:
            salida = {"key": clave, "outcomes": []}
            for nombre in jugadores:
                linea = MERCADOS[clave][1]
                salida["outcomes"].append({"name": "Over", "description": nombre, "price": momio_cerca(-115), "point": linea})
                salida["outcomes"].append({"name": "Under", "description": nombre, "price": momio_cerca(-115), "point": linea})
            mercados.append(salida)
        libros.append({"key": casa.lower(), "title": casa, "markets": mercados})
    props.append({
        "id": juego["id"],
        "sport_key": "basketball_nba",
        "commence_time": juego["commence_time"],
        "home_team": juego["home_team"],
        "away_team": juego["away_team"],
        "bookmakers": libros,
    })

with open("datos/lineas.json", "w", encoding="utf-8") as archivo:
    json.dump(lineas, archivo, indent=2)
with open("datos/props.json", "w", encoding="utf-8") as archivo:
    json.dump({"basketball_nba": props}, archivo, indent=2)
ligas = {
    "americanfootball_nfl": {"grupo": "NFL", "liga": "NFL"},
    "basketball_nba": {"grupo": "NBA", "liga": "NBA"},
    "icehockey_nhl": {"grupo": "NHL", "liga": "NHL"},
    "soccer_mexico_ligamx": {"grupo": "Futbol", "liga": "Liga MX"},
    "soccer_epl": {"grupo": "Futbol", "liga": "Premier League"},
    "mma_mixed_martial_arts": {"grupo": "UFC", "liga": "UFC"},
    "tennis_atp_finals": {"grupo": "Tenis", "liga": "ATP Finals"},
}
with open("datos/ligas.json", "w", encoding="utf-8") as archivo:
    json.dump(ligas, archivo, indent=2)
with open("datos/stats_nba.json", "w", encoding="utf-8") as archivo:
    json.dump(stats, archivo, indent=2)
with open("datos/es_prueba.txt", "w", encoding="utf-8") as archivo:
    archivo.write("estos datos son falsos")

print("Datos de prueba creados. Ahora corre: python calcular_picks.py")
