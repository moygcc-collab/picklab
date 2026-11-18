# ============================================
# EDICION DE PICKLAB
# Edicion: miercoles 18 de noviembre de 2026
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

EDICION = "miercoles 18 de noviembre"
FECHA_EDICION = "2026-11-18"  # para el historial (AAAA-MM-DD)

sin_comision = motor.sin_comision


def texto_linea(punto):
    if punto == int(punto):
        return str(int(punto))
    return str(punto)

# ---------- NBA: props de esta noche ----------

# Partidos NBA del miercoles 18 nov (horas en UTC)
HOU_IND = ("hou_ind", "Rockets @ Pacers", "2026-11-19T00:00:00Z")
MIL_MIA = ("mil_mia", "Bucks @ Heat", "2026-11-19T00:00:00Z")
PHI_ORL = ("phi_orl", "76ers @ Magic", "2026-11-19T00:00:00Z")
CHI_BKN = ("chi_bkn", "Bulls @ Nets", "2026-11-19T00:30:00Z")
WAS_TOR = ("was_tor", "Wizards @ Raptors", "2026-11-19T00:30:00Z")
ATL_OKC = ("atl_okc", "Hawks @ Thunder", "2026-11-19T01:00:00Z")
DET_NOP = ("det_nop", "Pistons @ Pelicans", "2026-11-19T01:00:00Z")
GSW_DAL = ("gsw_dal", "Warriors @ Mavericks", "2026-11-19T01:00:00Z")
BOS_DEN = ("bos_den", "Celtics @ Nuggets", "2026-11-19T02:30:00Z")
UTA_LAL = ("uta_lal", "Jazz @ Lakers", "2026-11-19T03:00:00Z")

# jugador, equipo, partido, mercado, linea, momio over, momio under, casa, fuente,
# ultimos 10 partidos (del mas viejo al mas nuevo, StatMuse)
PROPS_NBA = [
    ["Bam Adebayo", "Heat", MIL_MIA, "Rebotes", 8.5, None, -138, "FanDuel", "FanDuel Research",
     [9, 9, 9, 10, 10, 8, 8, 14, 5, 1]],
    ["VJ Edgecombe", "76ers", PHI_ORL, "Puntos", 13.5, 102, None, "FanDuel", "FanDuel Research",
     [13, 10, 21, 11, 19, 13, 8, 15, 11, 14]],
    ["Nikola Jokic", "Nuggets", BOS_DEN, "Asistencias", 9.5, 116, None, "FanDuel", "FanDuel Research",
     [11, 10, 10, 8, 11, 8, 9, 8, 10, 7]],
    ["Kyrie Irving", "Mavericks", GSW_DAL, "Puntos", 22.5, -115, None, "BetMGM", "TheLines",
     [24, 18, 15, 35, 29, 14, 21, 35, 10, 34]],
    ["Trae Young", "Wizards", WAS_TOR, "Asistencias", 8.5, -135, None, "BetMGM", "TheLines",
     [9, 9, 6, 10, 3, 7, 4, 14, 8, 12]],
    ["Shai Gilgeous-Alexander", "Thunder", ATL_OKC, "Asistencias", 5.5, None, -115, "bet365", "Covers",
     [2, 3, 8, 8, 4, 9, 3, 2, 5, 2]],
    ["Cade Cunningham", "Pistons", DET_NOP, "Puntos", 24.5, -108, None, "BetRivers", "SportsBettingDime",
     [19, 30, 20, 33, 26, 14, 17, 52, 33, 27]],
    ["Luka Doncic", "Lakers", UTA_LAL, "Puntos", 36.5, -110, None, "Caesars", "SportsBettingDime",
     [41, 37, 45, 42, 40, 53, 32, 32, 43, 36]],
    ["Julius Randle", "Nets", CHI_BKN, "Puntos", 22.5, None, -113, "Caesars", "Covers",
     [24, 15, 20, 21, 22, 19, 13, 17, 22, 33]],
    ["Alperen Sengun", "Rockets", HOU_IND, "Puntos", 20.5, -105, None, "BetMGM", "SportsBettingDime",
     [29, 16, 26, 17, 15, 20, 19, 43, 19, 23]],
]


# ---------- NFL semana 11 ----------
# Equipo: (partidos jugados, puntos a favor, puntos en contra)  ESPN standings
NFL_EQUIPOS = {
    "BUF": ("Bills", 9, 287, 199), "NYJ": ("Jets", 10, 194, 254), "MIA": ("Dolphins", 9, 148, 224),
    "CIN": ("Bengals", 9, 278, 193), "PIT": ("Steelers", 9, 198, 182), "BAL": ("Ravens", 9, 189, 236),
    "JAX": ("Jaguars", 9, 269, 144), "HOU": ("Texans", 9, 233, 219), "IND": ("Colts", 10, 208, 271),
    "TEN": ("Titans", 9, 167, 239), "KC": ("Chiefs", 9, 237, 156), "DEN": ("Broncos", 9, 198, 186),
    "LV": ("Raiders", 10, 251, 289), "LAC": ("Chargers", 8, 121, 219), "NYG": ("Giants", 9, 203, 196),
    "DAL": ("Cowboys", 10, 286, 282), "WSH": ("Commanders", 9, 196, 223), "PHI": ("Eagles", 9, 148, 221),
    "DET": ("Lions", 9, 257, 199), "MIN": ("Vikings", 9, 176, 126), "CHI": ("Bears", 9, 241, 184),
    "CAR": ("Panthers", 9, 219, 236), "TB": ("Buccaneers", 9, 202, 178), "NO": ("Saints", 9, 202, 236),
    "SF": ("49ers", 9, 281, 196), "ARI": ("Cardinals", 10, 184, 289),
}

# visitante, local, spread del local, momio visitante, momio local, total, over, under, hora UTC, neutral
NFL_PARTIDOS = [
    ("IND", "HOU", -12.5, -112, -108, 44.5, -105, -115, "2026-11-20T01:15:00Z", False),
    ("ARI", "KC", -16.5, -115, -105, 41.5, -108, -112, "2026-11-22T18:00:00Z", False),
    ("BAL", "CAR", -2.5, -105, -115, 43.5, -112, -108, "2026-11-22T18:00:00Z", False),
    ("MIA", "BUF", -16.5, -112, -108, 45.5, -110, -110, "2026-11-22T18:00:00Z", False),
    ("NO", "CHI", -11.5, -108, -112, 49.5, -102, -118, "2026-11-22T18:00:00Z", False),
    ("TB", "DET", -6.5, -112, -108, 45.5, -115, -105, "2026-11-22T18:00:00Z", False),
    ("TEN", "DAL", -8.5, -115, -105, 54.5, -120, 100, "2026-11-22T18:00:00Z", False),
    ("PIT", "PHI", 4.5, -105, -115, 38.5, -108, -112, "2026-11-22T18:00:00Z", False),
    ("NYJ", "LAC", -3.5, -118, -102, 40.5, -105, -115, "2026-11-22T21:05:00Z", False),
    ("JAX", "NYG", 6.0, -110, -110, 46.5, -110, -110, "2026-11-22T21:25:00Z", False),
    ("LV", "DEN", -10.0, -108, -112, 40.5, -108, -112, "2026-11-22T21:25:00Z", False),
    ("MIN", "SF", -3.0, -108, -112, 46.5, -108, -112, "2026-11-23T01:20:00Z", True),
    ("CIN", "WSH", 6.5, -102, -118, 52.5, -115, -105, "2026-11-24T01:15:00Z", False),
]


# ---------- NHL de hoy: totales ----------
NHL_EQUIPOS = {
    "BOS": ("Bruins", 21, 72, 55), "DET": ("Red Wings", 21, 57, 64),
    "MTL": ("Canadiens", 21, 69, 64), "NJ": ("Devils", 21, 80, 61),
    "COL": ("Avalanche", 21, 85, 64), "UTA": ("Mammoth", 22, 73, 78),
}

# visitante, local, linea, over, under, hora UTC  (DraftKings via SportsbookReview)
NHL_PARTIDOS = [
    ("BOS", "DET", 5.5, -145, 105, "2026-11-19T00:30:00Z"),
    ("MTL", "NJ", 6.5, 114, -135, "2026-11-19T00:30:00Z"),
    ("COL", "UTA", 6.5, -102, -118, "2026-11-19T03:00:00Z"),
]


# ---------- Premier League (jornada 11): totales ----------
# Equipo: (partidos, goles a favor, goles en contra)  ESPN standings
EPL_EQUIPOS = {
    "Arsenal": (10, 15, 5), "Brighton": (10, 26, 7), "Man City": (10, 21, 13), "Liverpool": (10, 14, 10),
    "Chelsea": (10, 19, 16), "Everton": (10, 12, 10), "Bournemouth": (10, 16, 14), "Brentford": (10, 16, 11),
    "Leeds": (10, 10, 8), "Aston Villa": (10, 14, 17), "Tottenham": (10, 10, 11), "Newcastle": (10, 13, 16),
    "Hull City": (10, 11, 11), "Ipswich": (10, 15, 20), "Fulham": (10, 10, 12), "Nottm Forest": (10, 9, 13),
    "Coventry": (10, 10, 19), "Man United": (10, 14, 19), "Sunderland": (10, 8, 17), "Crystal Palace": (10, 10, 24),
}

# local, visitante, linea, over, under, hora UTC
EPL_PARTIDOS = [
    ("Man City", "Fulham", 3.5, 120, -155, "2026-11-21T12:30:00Z"),
    ("Tottenham", "Ipswich", 2.5, -177, 135, "2026-11-21T15:00:00Z"),
    ("Aston Villa", "Sunderland", 2.5, -130, -100, "2026-11-21T15:00:00Z"),
    ("Coventry", "Crystal Palace", 2.5, -150, 115, "2026-11-21T15:00:00Z"),
    ("Chelsea", "Leeds", 2.5, -139, 109, "2026-11-21T15:00:00Z"),
    ("Bournemouth", "Nottm Forest", 2.5, -119, -105, "2026-11-21T15:00:00Z"),
    ("Newcastle", "Arsenal", 2.5, -143, 115, "2026-11-21T17:30:00Z"),
    ("Hull City", "Brighton", 2.5, -159, 120, "2026-11-22T14:00:00Z"),
]


# ---------- Ultimo enfrentamiento ----------
# Por partido (la misma clave "evento" que usan los picks).
# marcador: [[visitante, puntos], [local, puntos]]  -  los nombres deben ser
# iguales a los que salen en el pick (ej. "Colts +12.5" -> "Colts").
# Solo datos verificados; si no se encuentra, no se pone.
BR = "https://www.basketball-reference.com/boxscores/"
CBS = "https://www.cbssports.com/nfl/gametracker/boxscore/"
ULTIMO_DUELO = {
    "hou_ind": {"fecha": "2026-02-02", "liga": "NBA 2025-26", "marcador": [["Rockets", 118], ["Pacers", 114]],
                "fuente": "https://www.statmuse.com/nba/game/2-2-2026-hou-at-ind-77925"},
    "mil_mia": {"fecha": "2026-03-12", "liga": "NBA 2025-26", "marcador": [["Bucks", 105], ["Heat", 112]],
                "fuente": "https://www.statmuse.com/nba/game/3-12-2026-mil-at-mia-78169"},
    "phi_orl": {"fecha": "2026-04-15", "liga": "NBA 2025-26 (se jugo en Filadelfia)", "marcador": [["Magic", 97], ["76ers", 109]],
                "fuente": "https://www.statmuse.com/nba/game/4-15-2026-orl-at-phi-78457"},
    "chi_bkn": {"fecha": "2026-02-09", "liga": "NBA 2025-26", "marcador": [["Bulls", 115], ["Nets", 123]],
                "fuente": "https://www.statmuse.com/nba/game/2-9-2026-chi-at-bkn-77976"},
    "was_tor": {"fecha": "2026-10-23", "liga": "NBA 2026-27 (se jugo en Washington)", "marcador": [["Raptors", 112], ["Wizards", 102]],
                "fuente": "https://www.statmuse.com/nba/game/10-23-2026-tor-at-was-78656"},
    "atl_okc": {"fecha": "2025-12-29", "liga": "NBA 2025-26", "marcador": [["Hawks", 129], ["Thunder", 140]],
                "fuente": "https://www.statmuse.com/nba/game/12-29-2025-atl-at-okc-77665"},
    "det_nop": {"fecha": "2026-03-26", "liga": "NBA 2025-26 (se jugo en Detroit)", "marcador": [["Pelicans", 108], ["Pistons", 129]],
                "fuente": "https://www.statmuse.com/nba/game/3-26-2026-nop-at-det-78275"},
    "gsw_dal": {"fecha": "2026-03-23", "liga": "NBA 2025-26 (tiempo extra)", "marcador": [["Warriors", 137], ["Mavericks", 131]],
                "fuente": "https://www.statmuse.com/nba/game/3-23-2026-gsw-at-dal-78256"},
    "bos_den": {"fecha": "2026-02-25", "liga": "NBA 2025-26", "marcador": [["Celtics", 84], ["Nuggets", 103]],
                "fuente": "https://www.statmuse.com/nba/game/2-25-2026-bos-at-den-78059"},
    "uta_lal": {"fecha": "2026-10-25", "liga": "NBA 2026-27 (se jugo en Utah)", "marcador": [["Lakers", 132], ["Jazz", 123]],
                "fuente": "https://www.statmuse.com/nba/game/10-25-2026-lal-at-uta-78673"},
    "nhl_BOS_DET": {"fecha": "2026-03-21", "liga": "NHL 2025-26", "marcador": [["Bruins", 4], ["Red Wings", 2]],
                    "anteriores": ["13 ene 2026: Bruins 3 - 0 Red Wings (en Boston)", "2 dic 2025: Red Wings 5 - 4 Bruins (en Detroit)",
                                   "29 nov 2025: Bruins 3 - 2 Red Wings, en penales (en Boston)"],
                    "fuente": "https://www.hockey-reference.com/boxscores/202603210DET.html"},
    "nhl_MTL_NJ": {"fecha": "2026-04-05", "liga": "NHL 2025-26 (se jugo en Montreal)", "marcador": [["Devils", 3], ["Canadiens", 0]],
                   "anteriores": ["4 abr 2026: Canadiens 4 - 3 Devils, en penales (en New Jersey)",
                                  "6 nov 2025: Devils 4 - 3 Canadiens, tiempo extra (en New Jersey)"],
                   "fuente": "https://www.hockey-reference.com/boxscores/202604050MTL.html"},
    "nhl_COL_UTA": {"fecha": "2026-02-25", "liga": "NHL 2025-26", "marcador": [["Avalanche", 4], ["Mammoth", 2]],
                    "anteriores": ["23 dic 2025: Avalanche 1 - 0 Mammoth (en Colorado)", "21 oct 2025: Mammoth 4 - 3 Avalanche, tiempo extra (en Utah)",
                                   "9 oct 2025: Avalanche 2 - 1 Mammoth (en Colorado)"],
                    "fuente": "https://www.hockey-reference.com/boxscores/202602250UTA.html"},
    "nfl_LV_DEN": {"fecha": "2025-12-07", "liga": "NFL 2025, semana 14", "marcador": [["Broncos", 24], ["Raiders", 17]],
                   "detalle": "Bo Nix 212 yds, 0 TD de pase (1 por tierra). Geno Smith 116 yds, 1 TD y salio lesionado; Kenny Pickett 97 yds, 1 TD.",
                   "anteriores": ["6 nov 2025: Broncos 10 - 7 Raiders (en Denver)"],
                   "fuente": CBS + "NFL_20251207_DEN@LV/"},
    "nfl_IND_HOU": {"fecha": "2026-09-27", "liga": "NFL 2026, semana 3", "marcador": [["Texans", 17], ["Colts", 19]],
                    "detalle": "Gano Colts con gol de campo a 16 segundos del final. Daniel Jones 235 yds, 1 TD, 1 INT. C.J. Stroud 167 yds, 1 TD.",
                    "fuente": "https://www.cbssports.com/nfl/gametracker/recap/NFL_20260927_HOU@IND/"},
    "nfl_BAL_CAR": {"fecha": "2022-11-20", "liga": "NFL 2022, semana 11", "marcador": [["Panthers", 3], ["Ravens", 13]],
                    "detalle": "Lamar Jackson 209 yds, 0 TD, 1 INT. Baker Mayfield 196 yds, 0 TD, 2 INT. Hace 4 anos: los equipos cambiaron mucho.",
                    "fuente": CBS + "NFL_20221120_CAR@BAL/"},
    "nfl_MIA_BUF": {"fecha": "2025-11-09", "liga": "NFL 2025, semana 10", "marcador": [["Bills", 13], ["Dolphins", 30]],
                    "detalle": "Tua Tagovailoa 173 yds, 2 TD, 2 INT. Josh Allen 306 yds, 2 TD, 1 INT.",
                    "fuente": CBS + "NFL_20251109_BUF@MIA"},
    "nfl_NYJ_LAC": {"fecha": "2023-11-06", "liga": "NFL 2023, semana 9", "marcador": [["Chargers", 27], ["Jets", 6]],
                    "detalle": "Justin Herbert 136 yds, 0 TD. Zach Wilson 263 yds, 0 TD. Hace 3 anos: otros planteles.",
                    "fuente": CBS + "NFL_20231106_LAC@NYJ/"},
    "nfl_ARI_KC": {"fecha": "2022-09-11", "liga": "NFL 2022, semana 1", "marcador": [["Chiefs", 44], ["Cardinals", 21]],
                   "detalle": "Patrick Mahomes 360 yds, 5 TD. Kyler Murray 193 yds, 2 TD. Hace 4 anos: otros planteles.",
                   "fuente": "https://www.statmuse.com/nfl/ask/chiefs-vs-cardinals-record"},
    "nfl_NO_CHI": {"fecha": "2025-10-19", "liga": "NFL 2025, semana 7", "marcador": [["Saints", 14], ["Bears", 26]],
                   "detalle": "Caleb Williams 172 yds, 0 TD, 1 INT. Spencer Rattler 233 yds, 2 TD, 3 INT.",
                   "fuente": CBS + "NFL_20251019_NO@CHI/"},
    "nfl_TEN_DAL": {"fecha": "2022-12-29", "liga": "NFL 2022, semana 17", "marcador": [["Cowboys", 27], ["Titans", 13]],
                    "detalle": "Dak Prescott 282 yds, 2 TD, 2 INT. Joshua Dobbs 232 yds, 1 TD, 1 INT. Hace casi 4 anos.",
                    "fuente": CBS + "NFL_20221229_DAL@TEN/"},
    "epl_Newcastle_Arsenal": {"fecha": "2026-04-25", "liga": "Premier League 2025-26", "marcador": [["Newcastle", 0], ["Arsenal", 1]],
                              "detalle": "Gol de Eberechi Eze al 9' (asistencia de Havertz). Tiros: Arsenal 11, Newcastle 12-13.",
                              "anteriores": ["28 sep 2025: Newcastle 1 - 2 Arsenal (Premier)",
                                             "18 may 2025: Arsenal 1 - 0 Newcastle (Premier)",
                                             "5 feb 2025: Newcastle 2 - 0 Arsenal (Copa de la Liga)",
                                             "7 ene 2025: Arsenal 0 - 2 Newcastle (Copa de la Liga)"],
                              "fuente": "https://theanalyst.com/articles/arsenal-vs-newcastle-stats-opta-premier-league-04-2026"},
}

# Ultimo partido de cada jugador contra el rival de hoy (puede ser con otro equipo)
# pts, reb, ast, tri (triples metidos), min (minutos)
ULTIMO_DUELO_JUGADOR = {
    "Bam Adebayo": {"fecha": "2026-03-12", "equipo": "Heat", "rival": "Bucks", "pts": 21, "reb": 8, "ast": 2, "tri": 0, "min": 35,
        "fuente": "https://www.statmuse.com/nba/game/3-12-2026-mil-at-mia-78169"},
    "VJ Edgecombe": {"fecha": "2026-04-15", "equipo": "76ers", "rival": "Magic", "pts": 19, "reb": 11, "ast": 1, "tri": 1, "min": 42,
        "fuente": "https://www.statmuse.com/nba/game/4-15-2026-orl-at-phi-78457"},
    "Nikola Jokic": {"fecha": "2026-02-25", "equipo": "Nuggets", "rival": "Celtics", "pts": 30, "reb": 12, "ast": 6, "tri": 4, "min": 33,
        "fuente": "https://www.statmuse.com/nba/game/2-25-2026-bos-at-den-78059"},
    "Kyrie Irving": {"fecha": "2025-02-23", "equipo": "Mavericks", "rival": "Warriors", "pts": 17, "reb": 5, "ast": 4, "tri": 1, "min": 32,
        "fuente": "https://www.statmuse.com/nba/ask/kyrie-irving-last-game-vs-warriors"},
    "Trae Young": {"fecha": "2026-10-23", "equipo": "Wizards", "rival": "Raptors", "pts": 22, "reb": 1, "ast": 12, "tri": 4, "min": 37,
        "fuente": "https://www.statmuse.com/nba/game/10-23-2026-tor-at-was-78656"},
    "Shai Gilgeous-Alexander": {"fecha": "2025-12-29", "equipo": "Thunder", "rival": "Hawks", "pts": 39, "reb": 6, "ast": 6, "tri": 2, "min": 36,
        "fuente": "https://www.statmuse.com/nba/game/12-29-2025-atl-at-okc-77665"},
    "Cade Cunningham": {"fecha": "2025-03-17", "equipo": "Pistons", "rival": "Pelicans", "pts": 24, "reb": 4, "ast": 8, "tri": 1, "min": 30,
        "fuente": "https://www.statmuse.com/nba/ask/cade-cunningham-last-game-vs-pelicans"},
    "Luka Doncic": {"fecha": "2026-10-25", "equipo": "Lakers", "rival": "Jazz", "pts": 52, "reb": 8, "ast": 10, "tri": 8, "min": 38,
        "fuente": "https://www.statmuse.com/nba/game/10-25-2026-lal-at-uta-78673"},
    "Julius Randle": {"fecha": "2026-01-22", "equipo": "Timberwolves", "rival": "Bulls", "pts": 30, "reb": 7, "ast": 6, "tri": 3, "min": 31,
        "fuente": "https://www.statmuse.com/nba/ask/julius-randle-last-game-vs-bulls"},
    "Alperen Sengun": {"fecha": "2026-02-02", "equipo": "Rockets", "rival": "Pacers", "pts": 39, "reb": 16, "ast": 5, "tri": 0, "min": 35,
        "fuente": "https://www.statmuse.com/nba/game/2-2-2026-hou-at-ind-77925"},
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
    "Luka Doncic": [ajuste("Under", 0.02, "Segunda noche seguida: anoche jugo 42 minutos con tiempo extra")],
    "Cade Cunningham": [ajuste("Under", 0.02, "Segunda noche seguida: jugo anoche contra San Antonio")],
    "Bam Adebayo": [ajuste("Under", 0.02, "Llega como probable por molestia en la cadera y jugo solo 16 minutos en su ultimo partido")],
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


def picks_nba():
    salida = []
    for jugador, equipo, partido, mercado, linea, over, under, casa, fuente, valores in PROPS_NBA:
        opciones = []
        if over is not None and under is not None:
            p_over, p_under = sin_comision(over, under)
            opciones = [("Over", over, p_over, True), ("Under", under, p_under, True)]
        elif over is not None:
            opciones = [("Over", over, prob_implicita(over), False)]
        else:
            opciones = [("Under", under, prob_implicita(under), False)]
        mejor = None
        for lado, momio, p_m, dos in opciones:
            c = {
                "evento": partido[0], "grupo": "NBA", "liga": "NBA", "partido": partido[1], "fecha": partido[2],
                "tipo": "Props", "mercado": mercado, "jugador": jugador, "equipo": equipo,
                "pick": jugador + " " + lado + " " + str(linea), "lado": lado, "linea": linea,
                "momio": momio, "casa": casa, "casas": 1, "p_mercado": p_m, "dos_lados": dos,
                "valores": valores, "ajustes": CONTEXTO_JUGADOR.get(jugador, []),
                "base": "Ultimos " + str(len(valores)) + " partidos + momio. Linea via " + fuente + ", partidos via StatMuse",
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
    "Premier League": (EPL_EQUIPOS, EPL_PARTIDOS, "epl", "soccer_epl", "Betwatch"),
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
    if not api_picks.hay_props("basketball_nba"):
        candidatos += picks_nba()
        contar("NBA", "NBA", len(set(x[2][0] for x in PROPS_NBA)))
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
        for k in ["p_mercado", "p_modelo", "peso_modelo", "ajustes", "publicar", "dos_lados", "muestra", "modelo_texto"]:
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


NOTA = ("Edicion del " + EDICION + ": NBA (props de hoy), NHL (hoy), NFL semana 11 y Premier League jornada 11. "
        "Cada pick pasa por el motor de PickLab: mercado + estadisticas + contexto + historial, y solo se publica si tiene "
        "55% o mas de probabilidad, 3% o mas de ventaja y nivel de confianza A o B. MLB esta fuera de temporada; "
        "las demas ligas entran en cuanto este activa la API de momios.")

FUENTES = [
    ["ESPN - momios NFL semana 11 (DraftKings)", "https://www.espn.com/nfl/odds"],
    ["ESPN - tabla NFL (puntos a favor y en contra)", "https://www.espn.com/nfl/standings"],
    ["SportsbookReview - totales NHL 18 nov (DraftKings)", "https://www.sportsbookreview.com/betting-odds/nhl-hockey/totals/full-game/?date=2026-11-18"],
    ["CBS Sports - tabla NHL (goles a favor y en contra)", "https://www.cbssports.com/nhl/standings/"],
    ["Betwatch - momios Premier League", "https://betwatch.io/odds/premier-league"],
    ["ESPN - tabla Premier League", "https://www.espn.com/soccer/standings/_/league/eng.1"],
    ["FanDuel Research - props NBA 18 nov", "https://www.fanduel.com/research/nba-props-today-3-best-nba-player-prop-bets-for-wednesday-nov-18"],
    ["TheLines - props NBA 18 nov", "https://www.thelines.com/nba/player-props/expert-nba-picks-and-player-props-best-nba-bets-today-nov-18/"],
    ["SportsBettingDime - props NBA 18 nov", "https://www.sportsbettingdime.com/news/nba/best-player-prop-picks-today-key-injuries-nov-18/"],
    ["Covers - props NBA", "https://www.covers.com/sport/basketball/nba/player-props"],
    ["StatMuse - ultimos 10 partidos y enfrentamientos NBA", "https://www.statmuse.com/nba"],
    ["Hockey-Reference - ultimos enfrentamientos NHL", "https://www.hockey-reference.com/"],
    ["Ultimos enfrentamientos NFL - CBS Sports y StatMuse", "https://www.statmuse.com/nfl"],
    ["Ultimo Newcastle vs Arsenal - Opta / The Analyst", "https://theanalyst.com/articles/arsenal-vs-newcastle-stats-opta-premier-league-04-2026"],
    ["Resultados NBA 17 nov - CBS Sports y PlainTextSports", "https://plaintextsports.com/nba/2026-11-17/"],
]


if __name__ == "__main__":
    main()
