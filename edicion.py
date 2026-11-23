# ============================================
# EDICION DE PICKLAB
# Edicion: lunes 23 de noviembre de 2026 (cubre lunes 23 a miercoles 25)
#
# Aqui van los datos que se juntan a mano (estadisticas, contexto y, si la API
# no los trae, momios). La decision de cada pick la toma motor.py.
# Si existe datos/lineas.json (The Odds API), esas ligas usan los momios de la API
# con el mejor precio entre todas las casas, y las tablas de aqui alimentan el modelo.
#
# Uso: python edicion.py  -> escribe web/picks.js y actualiza el historial
# ============================================

import json
from datetime import datetime, timezone
from calcular_picks import prob_implicita, a_decimal, a_americano
import motor
import api_picks
import historial

EDICION = "lunes 23 de noviembre"
FECHA_EDICION = "2026-11-23"  # para el historial (AAAA-MM-DD)

sin_comision = motor.sin_comision


def texto_linea(punto):
    if punto == int(punto):
        return str(int(punto))
    return str(punto)

# ---------- NBA: props de esta noche ----------

# Partidos NBA del lunes 23 nov (hora UTC del martes 24). Momios: Covers / RotoBaller (solo un lado publicado)
# Valores y minutos: Land of Basketball (ultimos 10 jugados, del mas viejo al mas nuevo)
MEM_CHA = ("nba_MEM_CHA", "Grizzlies @ Hornets", "2026-11-24T00:00:00Z")
POR_PHI = ("nba_POR_PHI", "Trail Blazers @ 76ers", "2026-11-24T00:00:00Z")
MIL_TOR = ("nba_MIL_TOR", "Bucks @ Raptors", "2026-11-24T00:30:00Z")
BKN_MIN = ("nba_BKN_MIN", "Nets @ Timberwolves", "2026-11-24T00:30:00Z")
PHX_NO = ("nba_PHX_NO", "Suns @ Pelicans", "2026-11-24T01:00:00Z")
LAC_HOU = ("nba_LAC_HOU", "Clippers @ Rockets", "2026-11-24T01:30:00Z")
COVERS = "Covers"
RB = "RotoBaller"
PROPS_NBA = [
    ["Moussa Diabate", "Hornets", MEM_CHA, "Rebotes", 9.5, -130, None, "bet365", COVERS, [17, 9, 12, 8, 9, 6, 13, 12, 16, 15]],
    ["Cedric Coward", "Grizzlies", MEM_CHA, "Triples", 2.5, 135, None, "bet365", COVERS, [4, 2, 1, 1, 0, 4, 2, 4, 5, 4]],
    ["Cedric Coward", "Grizzlies", MEM_CHA, "Pts + Reb + Ast", 26.5, -115, None, "Fanatics", RB, [36, 19, 13, 30, 27, 39, 32, 28, 27, 32]],
    ["Deni Avdija", "Trail Blazers", POR_PHI, "Puntos", 22.5, -120, None, "BetMGM", COVERS, [24, 28, 21, 22, 15, 24, 28, 34, 27, 20]],
    ["Tyler Herro", "Bucks", MIL_TOR, "Puntos", 20.5, None, -110, "bet365", COVERS, [21, 25, 23, 13, 27, 18, 5, 8, 19, 50]],
    ["Julius Randle", "Nets", BKN_MIN, "Puntos", 21.5, None, -118, "DraftKings", COVERS, [20, 21, 22, 19, 13, 17, 22, 33, 17, 27]],
    ["Alperen Sengun", "Rockets", LAC_HOU, "Puntos", 21.5, None, -111, "DraftKings", COVERS, [26, 17, 15, 20, 19, 43, 19, 23, 7, 28]],
    ["Jeremiah Fears", "Pelicans", PHX_NO, "Puntos", 17.5, 100, None, "Novig", RB, [24, 25, 11, 14, 18, 13, 19, 16, 22, 29]],
]


# ---------- NFL semana 11: props de jugadores ----------
# Mismo formato. Valores: todos los partidos que jugo en 2026 (NFL.com game logs), del mas viejo al mas nuevo.
CIN_WSH = ("nfl_CIN_WSH", "Bengals @ Commanders", "2026-11-24T01:15:00Z")
SFA = "Sharp Football Analysis"
# Monday Night Football: no se encontro linea actual de props (Burrow / Chase); la del 19 nov ya no se usa
PROPS_NFL = [
]

# ---------- Minutos y proyeccion (props) ----------
# MINUTOS: minutos de cada uno de sus ultimos partidos, en el mismo orden que sus valores.
#   {"Jalen Brunson": [34, 36, 33, ...]}   (Land of Basketball / StatMuse traen los minutos)
#   Con minutos, el motor usa "produccion por minuto x minutos de hoy" (pesa 70%) y la racha (30%).
# PROYECCION: ajustes verificados para hoy:
#   "min": minutos esperados (ej. 38 si sale un titular de su posicion), "factor": ajuste por rival/uso (1.05 = +5%),
#   "texto": por que.   {"Jalen Brunson": {"min": 37, "factor": 1.05, "texto": "Sin Anunoby: mas tiros"}}
MINUTOS = {
    "Moussa Diabate": [35, 35, 31, 28, 24, 29, 32, 26, 38, 30],
    "Cedric Coward": [33, 23, 28, 27, 30, 33, 27, 33, 25, 30],
    "Deni Avdija": [30, 35, 35, 39, 24, 34, 35, 35, 30, 36],
    "Tyler Herro": [31, 33, 35, 27, 35, 34, 20, 24, 31, 40],
    "Julius Randle": [37, 36, 31, 34, 30, 29, 31, 34, 27, 39],
    "Alperen Sengun": [38, 39, 32, 35, 37, 37, 28, 30, 14, 36],
    "Jeremiah Fears": [36, 29, 29, 28, 34, 33, 29, 31, 38, 34],
}
PROYECCION = {
}


# ---------- Draftea (o cualquier casa con lineas alternas) ----------
# Si en Draftea ves otra linea para un jugador de arriba, pegala aqui con su momio:
#   [jugador, mercado, lado, linea, momio]   ej. ["Jalen Brunson", "Puntos", "Over", 22.5, -250]
# El motor la evalua con la linea principal del mercado + sus ultimos partidos y,
# si pasa las reglas (55%, 3% de ventaja, nivel A o B), sale como pick.
DRAFTEA = [
]


# ---------- NFL: Monday Night Football (semana 11) ----------
# Equipo: (partidos jugados, puntos a favor, puntos en contra)  ESPN standings hasta el domingo 22 nov
NFL_EQUIPOS = {
    "BUF": ("Bills", 10, 313, 208), "MIA": ("Dolphins", 10, 157, 250), "NE": ("Patriots", 10, 221, 242),
    "NYJ": ("Jets", 11, 221, 278), "CLE": ("Browns", 10, 188, 220), "PIT": ("Steelers", 10, 214, 201),
    "BAL": ("Ravens", 11, 242, 294), "CIN": ("Bengals", 9, 278, 193), "TEN": ("Titans", 10, 197, 290),
    "IND": ("Colts", 11, 211, 297), "HOU": ("Texans", 10, 259, 222), "JAX": ("Jaguars", 10, 287, 167),
    "LAC": ("Chargers", 10, 168, 266), "DEN": ("Broncos", 10, 236, 210), "KC": ("Chiefs", 10, 271, 163),
    "LV": ("Raiders", 11, 275, 327), "PHI": ("Eagles", 10, 167, 237), "WSH": ("Commanders", 9, 196, 223),
    "NYG": ("Giants", 10, 226, 214), "DAL": ("Cowboys", 11, 337, 312), "MIN": ("Vikings", 10, 186, 161),
    "GB": ("Packers", 10, 226, 221), "CHI": ("Bears", 10, 262, 197), "DET": ("Lions", 10, 288, 220),
    "ATL": ("Falcons", 10, 201, 258), "NO": ("Saints", 10, 215, 257), "TB": ("Buccaneers", 10, 223, 209),
    "CAR": ("Panthers", 10, 254, 269), "ARI": ("Cardinals", 11, 191, 323), "SEA": ("Seahawks", 10, 223, 175),
    "LAR": ("Rams", 10, 248, 187), "SF": ("49ers", 10, 316, 206),
}

# visitante, local, spread del local, momio visitante, momio local, total, over, under, hora UTC, neutral
# MNF: DraftKings en la pagina del partido de ESPN (23 nov)
# Semana 12 (25-30 nov): ya hay spread y total (DraftKings via CBS), pero ninguna fuente publico el momio
# de cada lado (spread ni over/under), asi que todavia no entran al motor.
NFL_PARTIDOS = [
    ("CIN", "WSH", 6.0, -113, -107, 54.5, -116, -103, "2026-11-24T01:15:00Z", False),
]


# ---------- NHL de hoy: totales ----------
# (partidos, goles a favor, goles en contra)  ESPN standings (hasta el 22 nov)
NHL_EQUIPOS = {
    "BOS": ("Bruins", 23, 83, 61), "BUF": ("Sabres", 23, 67, 81), "DET": ("Red Wings", 23, 60, 71),
    "FLA": ("Panthers", 24, 76, 71), "MTL": ("Canadiens", 24, 77, 71), "OTT": ("Senators", 24, 79, 70),
    "TB": ("Lightning", 22, 82, 62), "TOR": ("Maple Leafs", 25, 78, 90), "CAR": ("Hurricanes", 23, 95, 53),
    "CBJ": ("Blue Jackets", 21, 54, 68), "NJ": ("Devils", 23, 88, 73), "NYI": ("Islanders", 22, 71, 63),
    "NYR": ("Rangers", 22, 67, 58), "PHI": ("Flyers", 26, 67, 88), "PIT": ("Penguins", 22, 67, 80),
    "WSH": ("Capitals", 21, 72, 83), "CHI": ("Blackhawks", 23, 58, 93), "COL": ("Avalanche", 23, 90, 68),
    "DAL": ("Stars", 22, 64, 56), "MIN": ("Wild", 25, 90, 56), "NSH": ("Predators", 23, 71, 69),
    "STL": ("Blues", 23, 77, 73), "UTA": ("Mammoth", 24, 80, 81), "WPG": ("Jets", 24, 75, 82),
    "ANA": ("Ducks", 24, 87, 92), "CGY": ("Flames", 24, 60, 84), "EDM": ("Oilers", 25, 97, 72),
    "LA": ("Kings", 21, 58, 70), "SJ": ("Sharks", 25, 69, 89), "SEA": ("Kraken", 20, 67, 71),
    "VAN": ("Canucks", 25, 71, 108), "VGK": ("Golden Knights", 25, 85, 75),
}

# visitante, local, linea, over, under, hora UTC  (DraftKings via ESPN odds, 23 nov)
# Martes 24 solo hay VGK @ EDM (sin casa confirmada) y los 14 del miercoles todavia no tienen linea
NHL_PARTIDOS = [
    ("CBJ", "NJ", 6.5, 110, -130, "2026-11-24T00:00:00Z"),
    ("CGY", "OTT", 5.5, -125, 105, "2026-11-24T00:30:00Z"),
    ("UTA", "WPG", 6.5, -110, -110, "2026-11-24T00:30:00Z"),
    ("LA", "MTL", 6.5, 110, -130, "2026-11-24T00:30:00Z"),
    ("TOR", "NYI", 6.5, -108, -112, "2026-11-24T00:30:00Z"),
    ("ANA", "SEA", 6.5, -125, 105, "2026-11-24T02:40:00Z"),
    ("MIN", "SJ", 6.5, 105, -125, "2026-11-24T03:00:00Z"),
]


# ---------- Futbol (23 al 25 nov): totales ----------
# Equipo: (partidos, goles a favor, goles en contra)
# Momios: FOX Sports (casa no indicada). local, visitante, linea, over, under, hora UTC
# Premier y Serie A: tabla FOX Sports; solo queda el partido del lunes
EPL_EQUIPOS = {
    "Arsenal": (10, 15, 5), "Brighton": (10, 26, 7), "Man City": (10, 21, 13), "Liverpool": (10, 14, 10),
    "Chelsea": (10, 19, 16), "Everton": (10, 12, 10), "Bournemouth": (10, 16, 14), "Brentford": (10, 16, 11),
    "Leeds": (10, 10, 8), "Aston Villa": (10, 14, 17), "Tottenham": (10, 10, 11), "Newcastle": (10, 13, 16),
    "Hull City": (10, 11, 11), "Ipswich": (10, 15, 20), "Fulham": (10, 10, 12), "Nottm Forest": (10, 9, 13),
    "Coventry": (10, 10, 19), "Man United": (10, 14, 19), "Sunderland": (10, 8, 17), "Crystal Palace": (10, 10, 24),
}
EPL_PARTIDOS = [
    ("Brentford", "Everton", 2.5, -145, 105, "2026-11-23T20:00:00Z"),
]

SERIEA_EQUIPOS = {
    "Lazio": (11, 25, 9), "Inter": (11, 28, 13), "Roma": (11, 31, 10), "Milan": (11, 23, 13), "Como": (11, 18, 10),
    "Frosinone": (11, 24, 15), "Juventus": (11, 15, 12), "Bologna": (11, 16, 14), "Cagliari": (11, 10, 15),
    "Napoli": (11, 18, 14), "Torino": (11, 15, 17), "Atalanta": (11, 17, 20), "Genoa": (11, 11, 16),
    "Lecce": (11, 12, 22), "Fiorentina": (11, 17, 25), "Parma": (11, 9, 17), "Sassuolo": (11, 16, 29),
    "Monza": (11, 17, 25), "Venezia": (11, 8, 21), "Udinese": (11, 12, 25),
}
SERIEA_PARTIDOS = [
    ("Monza", "Fiorentina", 2.5, -174, 132, "2026-11-23T19:45:00Z"),
]

# Champions League, jornada 5 (martes 24 y miercoles 25). Tabla de la fase de liga: soccernews.com (23 nov)
UCL_EQUIPOS = {
    "PSG": (4, 20, 5), "Real Madrid": (4, 13, 7), "Arsenal": (4, 8, 3), "Como": (4, 19, 6), "Barcelona": (4, 14, 6),
    "Aston Villa": (4, 12, 6), "Manchester City": (4, 12, 7), "Liverpool": (4, 14, 10), "Club Brugge": (4, 11, 7),
    "Sporting CP": (4, 8, 4), "Real Betis": (4, 8, 6), "Borussia Dortmund": (4, 7, 5), "Bayern Munich": (4, 12, 5),
    "VfB Stuttgart": (4, 7, 4), "Inter": (4, 8, 6), "LASK": (4, 10, 9), "Manchester United": (4, 8, 8),
    "Galatasaray": (4, 8, 9), "Fenerbahce": (4, 6, 11), "Roma": (4, 10, 8), "Shakhtar Donetsk": (4, 4, 4),
    "Viking": (4, 9, 10), "Atletico Madrid": (4, 4, 5), "PSV": (4, 3, 4), "Bodo/Glimt": (4, 4, 9), "Porto": (4, 6, 7),
    "Napoli": (4, 6, 11), "Villarreal": (4, 8, 14), "AEK Athens": (4, 5, 11), "RB Leipzig": (4, 5, 11),
    "Sabah": (4, 4, 10), "Feyenoord": (4, 4, 11), "Lens": (4, 4, 16), "Slavia Prague": (4, 5, 9), "Lille": (4, 4, 10),
    "Slovan Bratislava": (4, 1, 17),
}
UCL_PARTIDOS = [
    ("Bodo/Glimt", "LASK", 3.5, -139, 109, "2026-11-24T17:45:00Z"),
    ("Galatasaray", "Aston Villa", 3.5, -122, -105, "2026-11-24T17:45:00Z"),
    ("Arsenal", "Borussia Dortmund", 2.5, -155, 121, "2026-11-24T20:00:00Z"),
    ("Como", "AEK Athens", 3.5, -115, -110, "2026-11-24T20:00:00Z"),
    ("Feyenoord", "Porto", 2.5, -164, 129, "2026-11-24T20:00:00Z"),
    ("Manchester City", "Napoli", 3.5, -115, -111, "2026-11-24T20:00:00Z"),
    ("RB Leipzig", "Lens", 3.5, -133, 103, "2026-11-24T20:00:00Z"),
    ("Real Madrid", "PSV", 4.5, 104, -133, "2026-11-24T20:00:00Z"),
    ("Slovan Bratislava", "Real Betis", 3.5, -112, -113, "2026-11-24T20:00:00Z"),
    ("Sabah", "Barcelona", 4.5, -149, 114, "2026-11-25T17:45:00Z"),
    ("Slavia Prague", "Villarreal", 2.5, -189, 149, "2026-11-25T17:45:00Z"),
    ("Atletico Madrid", "Viking", 3.5, -149, 116, "2026-11-25T20:00:00Z"),
    ("Club Brugge", "Liverpool", 3.5, -130, 102, "2026-11-25T20:00:00Z"),
    ("Inter", "VfB Stuttgart", 3.5, -163, 127, "2026-11-25T20:00:00Z"),
    ("Shakhtar Donetsk", "Fenerbahce", 2.5, -141, 109, "2026-11-25T20:00:00Z"),
    ("Lille", "Bayern Munich", 2.5, -180, 139, "2026-11-25T20:00:00Z"),
    ("PSG", "Roma", 3.5, -119, -107, "2026-11-25T20:00:00Z"),
    ("Sporting CP", "Manchester United", 2.5, -187, 143, "2026-11-25T20:00:00Z"),
]
# Liga MX: cuartos de final de ida el 25 o 26 nov, sin horario ni momios publicados todavia


# ---------- Ultimo enfrentamiento ----------
# Por partido (la misma clave "evento" que usan los picks).
# marcador: [[visitante, puntos], [local, puntos]]  -  los nombres deben ser
# iguales a los que salen en el pick (ej. "Colts +12.5" -> "Colts").
# Solo datos verificados; si no se encuentra, no se pone.
BR = "https://www.basketball-reference.com/boxscores/"
CBS = "https://www.cbssports.com/nfl/gametracker/boxscore/"
ULTIMO_DUELO = {
}

# Ultimo partido de cada jugador contra el rival de hoy (puede ser con otro equipo)
# pts, reb, ast, tri (triples metidos), min (minutos)
ULTIMO_DUELO_JUGADOR = {
    "Tyler Herro": {"rival": "Raptors", "fecha": "2026-11-06", "pts": 23, "reb": 5, "ast": 10, "tri": 1, "min": 35,
                    "fuente": "https://www.landofbasketball.com/nba_players_games/last_10/tyler_herro_all.htm"},
}

# Como se suma cada mercado de props con la linea del jugador
MERCADOS = {
    "Puntos": ["pts"], "Rebotes": ["reb"], "Asistencias": ["ast"], "Triples": ["tri"],
    "Puntos + Asistencias": ["pts", "ast"], "Puntos + Rebotes": ["pts", "reb"],
    "Pts + Reb + Ast": ["pts", "reb", "ast"],
}


def comparar(valor, lado, linea):
    # True si pegaba, False si no, None si fue empate exacto
    if valor == linea:
        return None
    if lado == "Over":
        return valor > linea
    return valor < linea


def agregar_duelo(p):
    # Pega al pick el ultimo enfrentamiento y si con la linea de hoy hubiera pegado
    d = ULTIMO_DUELO.get(p["evento"])
    jug = ULTIMO_DUELO_JUGADOR.get(p.get("jugador", ""))
    if d is None and jug is None:
        return
    duelo = {}
    if d is not None:
        duelo.update(d)
    texto = p["pick"]

    if p["tipo"] == "Props" and jug is not None:
        claves = MERCADOS.get(p["mercado"])
        duelo["jugador"] = jug
        if claves:
            valor = sum(jug[c] for c in claves)
            duelo["valor"] = valor
            duelo["pego"] = comparar(valor, p["lado"], p["linea"])
            duelo["resumen"] = (p["jugador"] + " hizo " + str(valor) + " " + p["mercado"].lower() +
                                " vs " + jug["rival"] + " (linea de hoy " + str(p["linea"]) + ")")
    elif p["tipo"] == "Totales" and d is not None:
        lado, linea = texto.split(" ")[0], float(texto.split(" ")[1])
        total = d["marcador"][0][1] + d["marcador"][1][1]
        duelo["valor"] = total
        duelo["pego"] = comparar(total, lado, linea)
        duelo["resumen"] = "Total de " + str(total) + " contra la linea de hoy de " + texto_linea(linea)
    elif p["tipo"] == "Spreads" and d is not None:
        equipo = texto.rsplit(" ", 1)[0]
        handicap = float(texto.rsplit(" ", 1)[1])
        marcador = dict((e, pts) for e, pts in d["marcador"])
        if equipo in marcador:
            rival = [e for e in marcador if e != equipo][0]
            margen = marcador[equipo] - marcador[rival]
            duelo["valor"] = margen
            duelo["pego"] = comparar(margen + handicap, "Over", 0)
            duelo["resumen"] = (equipo + (" gano por " + str(margen) if margen > 0 else " perdio por " + str(-margen)) +
                                "; con " + texto.rsplit(" ", 1)[1] + " hoy")
    p["duelo"] = duelo


# ---------- Contexto (solo datos verificados) ----------
# Cada ajuste dice a quien ayuda: "Over", "Under" o el nombre del equipo, y cuanto (0.01 = 1 punto).
# El motor los suma con un tope de 5 puntos.
def ajuste(efecto, delta, texto):
    return {"efecto": efecto, "delta": delta, "texto": texto}

# Por jugador (props)
CONTEXTO_JUGADOR = {
}

# Por partido (clave "evento" o, para la API, el texto "Visitante @ Local")
CONTEXTO_EVENTO = {
}

# Estadisticas por liga para el modelo de los picks de la API (pj, a favor, en contra).
# Los nombres pueden ser cortos ("Chiefs"): se buscan dentro del nombre completo de la API.
ALIAS = {"Man City": "Manchester City", "Man United": "Manchester United", "Nottm Forest": "Nottingham Forest",
         "Hull City": "Hull", "Ipswich": "Ipswich Town"}


def tablas_api():
    tablas = {
        "americanfootball_nfl": dict((v[0], v[1:]) for v in NFL_EQUIPOS.values()),
        "icehockey_nhl": dict((v[0], v[1:]) for v in NHL_EQUIPOS.values()),
    }
    for liga, (equipos, partidos, prefijo, clave_api, casa) in FUTBOL_LIGAS.items():
        tablas[clave_api] = equipos
    return tablas

# Ultimos 10 de jugadores para props de la API: {"Jugador": {"player_points": [...]}}
ULTIMOS_API = {}

# ---------- Armar candidatos con los datos de arriba ----------

CLAVE_MERCADO = {"Puntos": "pts", "Rebotes": "reb", "Asistencias": "ast", "Triples": "tri"}


def picks_props(lista, grupo, liga):
    salida = []
    for fila in lista:
        jugador, equipo, partido, mercado, linea, over, under, casa, fuente, valores = fila[:10]
        otras = fila[10] if len(fila) > 10 else []
        opciones = []
        if over is not None and under is not None:
            p_over, p_under = sin_comision(over, under)
            libros = [(casa, over, under)] + list(otras)
            if len(libros) > 1:
                # Consenso: promedio de las probabilidades sin comision y el mejor precio de cada lado
                p_over = sum(sin_comision(o, u)[0] for _, o, u in libros) / len(libros)
                p_under = 1 - p_over
                mejor_o = max(libros, key=lambda x: a_decimal(x[1]))
                mejor_u = max(libros, key=lambda x: a_decimal(x[2]))
                opciones = [("Over", mejor_o[1], p_over, True, mejor_o[0]), ("Under", mejor_u[2], p_under, True, mejor_u[0])]
            else:
                opciones = [("Over", over, p_over, True, casa), ("Under", under, p_under, True, casa)]
        elif over is not None:
            opciones = [("Over", over, prob_implicita(over), False, casa)]
        else:
            opciones = [("Under", under, prob_implicita(under), False, casa)]
        mejor = None
        for lado, momio, p_m, dos, casa_lado in opciones:
            c = {
                "evento": partido[0], "grupo": grupo, "liga": liga, "partido": partido[1], "fecha": partido[2],
                "tipo": "Props", "mercado": mercado, "jugador": jugador, "equipo": equipo,
                "pick": jugador + " " + lado + " " + str(linea), "lado": lado, "linea": linea,
                "momio": momio, "casa": casa_lado, "casas": 1 + len(otras) if dos else 1, "p_mercado": p_m, "dos_lados": dos,
                "valores": valores, "ajustes": CONTEXTO_JUGADOR.get(jugador, []),
                "minutos": MINUTOS.get(jugador) if len(MINUTOS.get(jugador) or []) == len(valores) else None,
                "min_proy": (PROYECCION.get(jugador) or {}).get("min"),
                "factor_proy": (PROYECCION.get(jugador) or {}).get("factor", 1.0),
                "proy_texto": (PROYECCION.get(jugador) or {}).get("texto"),
                "base": "Ultimos " + str(len(valores)) + " partidos + momio. Linea via " + fuente +
                        (", partidos via StatMuse / Land of Basketball" if grupo == "NBA" else ", partidos via NFL.com"),
            }
            agregar_duelo(c)
            motor.evaluar(c)
            if mejor is None or c["ventaja"] > mejor["ventaja"]:
                mejor = c
        ordenados = sorted(valores)
        mejor.update({"promedio": round(sum(valores) / len(valores), 1), "mediana": ordenados[len(ordenados) // 2],
                      "maximo": max(valores), "minimo": min(valores)})
        salida.append(mejor)
    return salida


def picks_draftea(props):
    # Lineas alternas reales (con momio) que el usuario pega en DRAFTEA
    salida = []
    for jugador, mercado, lado, linea, momio in DRAFTEA:
        base = None
        for c in props:
            if c["jugador"] == jugador and c["mercado"] == mercado:
                base = c
        if base is None:
            print("OJO: Draftea sin linea principal para", jugador, mercado)
            continue
        b = dict(base)
        if b["lado"] != lado and not b.get("dos_lados"):
            print("OJO: Draftea pide el otro lado y solo tenemos un lado del momio:", jugador, mercado)
            continue
        if b["lado"] != lado:
            # Voltear al lado pedido usando la probabilidad del otro lado
            b["lado"] = lado
            b["p_mercado"] = 1 - b["p_mercado"]
        alt = motor.alterna(b, linea, momio, "Draftea")
        alt["base"] = "Linea alterna de Draftea: mercado de la linea principal + ultimos partidos"
        salida.append(alt)
    return salida


def pick_equipo(evento, grupo, liga, partido, fecha, tipo, mercado, texto, momio, p_m, p_e, muestra, explicacion, extra, casa):
    c = {
        "evento": evento, "grupo": grupo, "liga": liga, "partido": partido, "fecha": fecha,
        "tipo": tipo, "mercado": mercado, "pick": texto, "momio": momio, "casa": casa, "casas": 1,
        "p_mercado": p_m, "dos_lados": True, "p_modelo": p_e, "muestra": muestra,
        "peso_modelo": motor.PESO_MAX_EQUIPOS * min(1, muestra / 8),
        "modelo_texto": explicacion, "explicacion": explicacion,
        "ajustes": CONTEXTO_EVENTO.get(evento, []),
        "base": "Modelo con estadisticas de la temporada + momio sin comision + contexto",
    }
    c.update(extra)
    agregar_duelo(c)
    return motor.evaluar(c)


def mejor_de(a, b):
    return a if a["ventaja"] >= b["ventaja"] else b


def picks_nfl():
    salida = []
    for vis, loc, spread_loc, m_vis, m_loc, total, m_over, m_under, fecha, neutral in NFL_PARTIDOS:
        nv, gv, pfv, pav = NFL_EQUIPOS[vis]
        nl, gl, pfl, pal = NFL_EQUIPOS[loc]
        casa_v = 0 if neutral else 1.0
        pts_loc = (pfl / gl + pav / gv) / 2 + casa_v
        pts_vis = (pfv / gv + pal / gl) / 2 - casa_v
        proy_total = pts_loc + pts_vis
        margen = pts_loc - pts_vis
        partido = nv + " @ " + nl + (" (Estadio Banorte, CDMX)" if neutral else "")
        evento = "nfl_" + vis + "_" + loc
        muestra = min(gv, gl)

        p_over_m, p_under_m = sin_comision(m_over, m_under)
        p_over = motor.normal_mayor(total, proy_total, 13.5)
        expl = ("Con sus puntos a favor y en contra de la temporada proyectamos " + nl + " " + str(round(pts_loc, 1)) +
                " y " + nv + " " + str(round(pts_vis, 1)) + ": " + str(round(proy_total, 1)) + " puntos")
        a = pick_equipo(evento, "NFL", "NFL", partido, fecha, "Totales", "Total de puntos", "Over " + texto_linea(total),
                        m_over, p_over_m, p_over, muestra, expl, {"lado": "Over"}, "DraftKings")
        b = pick_equipo(evento, "NFL", "NFL", partido, fecha, "Totales", "Total de puntos", "Under " + texto_linea(total),
                        m_under, p_under_m, 1 - p_over, muestra, expl, {"lado": "Under"}, "DraftKings")
        salida.append(mejor_de(a, b))

        p_vis_m, p_loc_m = sin_comision(m_vis, m_loc)
        p_loc = motor.normal_mayor(-spread_loc, margen, 13.5)
        s_loc = ("+" if spread_loc > 0 else "") + texto_linea(spread_loc)
        s_vis = ("+" if -spread_loc > 0 else "") + texto_linea(-spread_loc)
        expl = "Proyectamos que " + nl + " termine con margen de " + ("+" if margen > 0 else "") + str(round(margen, 1)) + " puntos"
        a = pick_equipo(evento, "NFL", "NFL", partido, fecha, "Spreads", "Spread", nl + " " + s_loc, m_loc, p_loc_m, p_loc,
                        muestra, expl, {"equipo_pick": nl, "rival_pick": nv}, "DraftKings")
        b = pick_equipo(evento, "NFL", "NFL", partido, fecha, "Spreads", "Spread", nv + " " + s_vis, m_vis, p_vis_m, 1 - p_loc,
                        muestra, expl, {"equipo_pick": nv, "rival_pick": nl}, "DraftKings")
        salida.append(mejor_de(a, b))
    return salida


def picks_nhl():
    salida = []
    for vis, loc, total, m_over, m_under, fecha in NHL_PARTIDOS:
        nv, gv, gfv, gav = NHL_EQUIPOS[vis]
        nl, gl, gfl, gal = NHL_EQUIPOS[loc]
        lam_loc = (gfl / gl + gav / gv) / 2
        lam_vis = (gfv / gv + gal / gl) / 2
        lam = lam_loc + lam_vis
        p_over = motor.poisson_mayor(total, lam)
        p_over_m, p_under_m = sin_comision(m_over, m_under)
        expl = ("Con sus goles a favor y en contra esperamos " + str(round(lam, 2)) + " goles (" + nl + " " +
                str(round(lam_loc, 2)) + ", " + nv + " " + str(round(lam_vis, 2)) + ")")
        evento = "nhl_" + vis + "_" + loc
        args = (evento, "NHL", "NHL", nv + " @ " + nl, fecha, "Totales", "Total de goles")
        a = pick_equipo(*args, "Over " + texto_linea(total), m_over, p_over_m, p_over, min(gv, gl), expl, {"lado": "Over"}, "DraftKings")
        b = pick_equipo(*args, "Under " + texto_linea(total), m_under, p_under_m, 1 - p_over, min(gv, gl), expl, {"lado": "Under"}, "DraftKings")
        salida.append(mejor_de(a, b))
    return salida


# Ligas de futbol con datos manuales: nombre -> (tabla de equipos, partidos, prefijo, clave de la API, casa)
# Para agregar otra liga (LaLiga, Serie A, Liga MX...) copia el formato de EPL_EQUIPOS y EPL_PARTIDOS.
FUTBOL_LIGAS = {
    "Premier League": (EPL_EQUIPOS, EPL_PARTIDOS, "epl", "soccer_epl", "FOX Sports"),
    "Serie A": (SERIEA_EQUIPOS, SERIEA_PARTIDOS, "seriea", "soccer_italy_serie_a", "FOX Sports"),
    "Champions League": (UCL_EQUIPOS, UCL_PARTIDOS, "ucl", "soccer_uefa_champs_league", "FOX Sports"),
}


def picks_futbol(liga, equipos, partidos, prefijo, casa):
    prom = sum(e[1] for e in equipos.values()) / sum(e[0] for e in equipos.values())
    salida = []
    for loc, vis, total, m_over, m_under, fecha in partidos:
        gl, fl, al = equipos[loc]
        gv, fv, av = equipos[vis]
        # Fuerza de ataque y defensa, jalada 50% hacia el promedio de la liga
        ataque_loc = 0.5 + 0.5 * (fl / gl) / prom
        defensa_loc = 0.5 + 0.5 * (al / gl) / prom
        ataque_vis = 0.5 + 0.5 * (fv / gv) / prom
        defensa_vis = 0.5 + 0.5 * (av / gv) / prom
        lam_loc = prom * 1.1 * ataque_loc * defensa_vis
        lam_vis = prom * 0.9 * ataque_vis * defensa_loc
        lam = lam_loc + lam_vis
        p_over = motor.poisson_mayor(total, lam)
        p_over_m, p_under_m = sin_comision(m_over, m_under)
        expl = ("Con sus goles a favor y en contra en " + liga + " esperamos " + str(round(lam, 2)) + " goles (" + loc + " " +
                str(round(lam_loc, 2)) + ", " + vis + " " + str(round(lam_vis, 2)) + ")")
        evento = prefijo + "_" + loc + "_" + vis
        args = (evento, "Futbol", liga, loc + " vs " + vis, fecha, "Totales", "Total de goles")
        a = pick_equipo(*args, "Over " + texto_linea(total), m_over, p_over_m, p_over, min(gl, gv), expl, {"lado": "Over"}, casa)
        b = pick_equipo(*args, "Under " + texto_linea(total), m_under, p_under_m, 1 - p_over, min(gl, gv), expl, {"lado": "Under"}, casa)
        salida.append(mejor_de(a, b))
    return salida


# ---------- Juntar todo ----------

ORDEN_GRUPOS = ["NFL", "NBA", "Futbol", "MLB", "NHL", "UFC", "Tenis"]


def main():
    candidatos = []
    analizados = {}
    ligas_por_grupo = {}

    def contar(grupo, liga, n):
        analizados[grupo] = analizados.get(grupo, 0) + n
        ligas_por_grupo.setdefault(grupo, [])
        if liga not in ligas_por_grupo[grupo]:
            ligas_por_grupo[grupo].append(liga)

    # 1. Datos manuales (solo para las ligas que la API no trae)
    props_manual = []
    if not api_picks.hay_props("basketball_nba"):
        props_manual += picks_props(PROPS_NBA, "NBA", "NBA")
        contar("NBA", "NBA", len(set(x[2][0] for x in PROPS_NBA)))
    if not api_picks.hay_props("americanfootball_nfl"):
        props_manual += picks_props(PROPS_NFL, "NFL", "NFL")
    candidatos += props_manual + picks_draftea(props_manual)
    if not api_picks.hay_api("americanfootball_nfl"):
        candidatos += picks_nfl()
        contar("NFL", "NFL", len(NFL_PARTIDOS))
    if not api_picks.hay_api("icehockey_nhl"):
        candidatos += picks_nhl()
        contar("NHL", "NHL", len(NHL_PARTIDOS))
    for liga, (equipos, partidos, prefijo, clave_api, casa) in FUTBOL_LIGAS.items():
        if not api_picks.hay_api(clave_api):
            candidatos += picks_futbol(liga, equipos, partidos, prefijo, casa)
            contar("Futbol", liga, len(partidos))

    # 2. The Odds API (todas las ligas activas)
    contexto_api = dict(CONTEXTO_EVENTO)
    lineas_api, por_grupo = api_picks.candidatos_lineas(tablas_api(), ALIAS, contexto_api)
    for c in lineas_api:
        agregar_duelo(c)
        motor.evaluar(c)
    props_api = api_picks.candidatos_props(ULTIMOS_API, CONTEXTO_JUGADOR)
    candidatos += lineas_api + props_api
    for g, n in por_grupo.items():
        analizados[g] = analizados.get(g, 0) + n
    for c in lineas_api + props_api:
        ligas_por_grupo.setdefault(c["grupo"], [])
        if c["liga"] not in ligas_por_grupo[c["grupo"]]:
            ligas_por_grupo[c["grupo"]].append(c["liga"])

    # 3. Quitar partidos que ya empezaron y filtrar: solo lo que pasa las reglas del motor
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    candidatos = [c for c in candidatos if c["fecha"] > ahora]
    picks = [c for c in candidatos if c["publicar"]]
    # Tope por partido: los picks del mismo partido estan conectados (si sale bajo, fallan juntos)
    picks.sort(key=lambda p: (p["score"], p["prob"]), reverse=True)
    por_partido = {}
    filtrados = []
    for p in picks:
        if motor.TOPE_POR_PARTIDO and por_partido.get(p["evento"], 0) >= motor.TOPE_POR_PARTIDO:
            continue
        por_partido[p["evento"]] = por_partido.get(p["evento"], 0) + 1
        filtrados.append(p)
    picks = filtrados

    # Lineas alternas (para Draftea): de cada prop, que tan seguro es bajar (o subir) la linea
    escalera = []
    for c in candidatos:
        if c["tipo"] != "Props" or c.get("casa") == "Draftea" or not c.get("valores"):
            continue
        pasos = motor.escalera(c)
        if pasos:
            escalera.append({"grupo": c["grupo"], "jugador": c["jugador"], "equipo": c.get("equipo", ""),
                             "partido": c["partido"], "fecha": c["fecha"], "mercado": c["mercado"],
                             "linea": c["linea"], "lado": c["lado"], "momio": c["momio"], "casa": c["casa"],
                             "prob_principal": round(c["prob"] * 100, 1), "promedio": round(sum(c["valores"]) / len(c["valores"]), 1),
                             "pasos": pasos})
    escalera.sort(key=lambda e: -e["pasos"][0]["prob"])
    descartados = [c["pick"] + " (" + str(c["score"]) + ")" for c in candidatos if not c["publicar"] and c["tipo"] == "Props"]

    # Orden: primero el nivel de confianza, luego la probabilidad
    picks.sort(key=lambda p: (p["score"], p["prob"]), reverse=True)
    for i, p in enumerate(picks):
        p["id"] = i + 1
        p["prob"] = round(p["prob"] * 100, 1)
        p["ventaja"] = round(p["ventaja"] * 100, 1)
        p["implicita"] = round(prob_implicita(p["momio"]) * 100, 1)
        if "p_estadisticas" in p and not p.get("valores"):
            p["modelo"] = p["p_estadisticas"]
            p["mercado_prob"] = p["p_mercado_pct"]
        for k in ["p_mercado", "p_modelo", "peso_modelo", "ajustes", "publicar", "dos_lados", "muestra", "modelo_texto",
                  "minutos", "min_proy", "factor_proy", "proy_texto"]:
            p.pop(k, None)

    # Parlay: los 3 de mas confianza de partidos diferentes (nivel A primero)
    parlay = []
    usados = []
    for p in picks:
        if p["evento"] not in usados and p["prob"] >= 58:
            parlay.append(p["id"])
            usados.append(p["evento"])
        if len(parlay) == 3:
            break
    decimal = 1
    prob_parlay = 1
    for p in picks:
        if p["id"] in parlay:
            decimal *= a_decimal(p["momio"])
            prob_parlay *= p["prob"] / 100

    grupos = {}
    for g in ORDEN_GRUPOS:
        grupos[g] = {"picks": len([p for p in picks if p["grupo"] == g]), "partidos": analizados.get(g, 0),
                     "ligas": ligas_por_grupo.get(g, [])}

    cal = motor.calibracion()
    salida = {
        "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prueba": False,
        "manual": True,
        "api": bool(api_picks.LINEAS),
        "nota": NOTA,
        "fuentes": FUENTES,
        "reglas": {"prob_minima": round(motor.PROB_MINIMA * 100), "ventaja_minima": round(motor.VENTAJA_MINIMA * 100),
                   "calibracion": cal},
        "partidos_analizados": sum(analizados.values()),
        "candidatos": len(candidatos),
        "descartados": descartados,
        "picks": picks,
        "escalera": escalera,
        "parlay": {"ids": parlay, "momio": a_americano(decimal) if parlay else 0, "prob": round(prob_parlay * 100, 1)},
        "grupos": grupos,
    }

    with open("web/picks.js", "w", encoding="utf-8") as archivo:
        archivo.write("window.PICKS = ")
        archivo.write(json.dumps(salida, ensure_ascii=False, indent=1))
        archivo.write(";\n")

    # Historial: calificar lo que se pueda solo, guardar los picks nuevos y actualizar la pagina
    lista = historial.guardar_edicion(picks, FECHA_EDICION)
    historial.escribir_web(historial.aplicar_resultados(historial.calificar_auto(lista)))

    print("Candidatos:", len(candidatos), "| publicados:", len(picks))
    for p in picks:
        print(p["id"], p["nivel"], p["score"], p["grupo"], "|", p["pick"], "|", p["partido"], "|", p["momio"],
              "| prob", p["prob"], "| ventaja", p["ventaja"], "|", p["unidades"], "u | senales", p["senales"])
    print("Parlay:", salida["parlay"])
    print("Escalera (lineas alternas):", len(escalera), "jugadores")
    for e in escalera[:40]:
        print("  ", e["jugador"], e["mercado"], e["lado"], e["linea"], "->",
              ", ".join(str(p["linea"]) + " " + str(p["prob"]) + "% (" + str(p["aciertos"]) + "/" + str(p["partidos"]) + ", min " + str(p["momio_minimo"]) + ")" for p in e["pasos"]))


NOTA = ("Edicion del " + EDICION + " (lunes a miercoles): Monday Night Football (Bengals @ Commanders, spread y total), "
        "8 props NBA de hoy, 7 partidos NHL, Brentford-Everton, Monza-Fiorentina y los 18 partidos de la jornada 5 de "
        "Champions (martes y miercoles). Las lineas NFL de la semana 12 ya salieron (spread y total) pero ninguna fuente "
        "publico los momios de cada lado, asi que entran en la edicion del jueves. En los props NBA solo se encontro "
        "un lado del momio: el motor usa la probabilidad con comision, que es mas conservadora. "
        "Solo se publica con 55% o mas, 3% o mas de ventaja y nivel A o B.")

FUENTES = [
    ["ESPN - Bengals @ Commanders (linea DraftKings y lesiones)", "https://www.espn.com/nfl/game/_/gameId/401873078"],
    ["ESPN.in - tabla NFL (puntos a favor y en contra)", "https://www.espn.in/nfl/table/_/sort/pointsfor"],
    ["CBS Sports - lineas NFL semana 12 (DraftKings)", "https://www.cbssports.com/nfl/news/nfl-week-12-early-odds-bills-over-chiefs-thanksgiving-steelers/"],
    ["Covers - props NBA de hoy", "https://www.covers.com/sport/basketball/nba/player-props"],
    ["RotoBaller - props NBA 23 nov", "https://www.rotoballer.com/todays-best-nba-player-prop-bets-11-23-26/2001450"],
    ["Land of Basketball - partidos del 23 nov y ultimos 10", "https://www.landofbasketball.com/nba_daily_summary/20261123.htm"],
    ["NBA.com - reporte de lesiones Pelicans vs Suns", "https://www.nba.com/pelicans/news/pelicans-vs-suns-injury-report-game-preview-11-23-2026"],
    ["ESPN - totales NHL (DraftKings)", "https://www.espn.com/nhl/odds"],
    ["ESPN - tabla NHL (goles a favor y en contra)", "https://www.espn.com/nhl/standings/_/view"],
    ["FOX Sports - calendario y momios Champions League", "https://www.foxsports.com/soccer/champions-league/schedule"],
    ["CBS Sports - momios Champions League", "https://www.cbssports.com/soccer/champions-league/odds/"],
    ["Soccernews - tabla fase de liga Champions", "https://www.soccernews.com/soccer-stats/europe-uefa-champions-league/league-table/"],
    ["FOX Sports - momios y tabla Premier League", "https://www.foxsports.com/soccer/premier-league/standings"],
    ["FOX Sports - momios y tabla Serie A", "https://www.foxsports.com/soccer/serie-a/standings"],
]


if __name__ == "__main__":
    main()
