# ============================================
# EDICION DE PICKLAB
# Edicion: sabado 21 de noviembre de 2026
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

EDICION = "sabado 21 de noviembre"
FECHA_EDICION = "2026-11-21"  # para el historial (AAAA-MM-DD)

sin_comision = motor.sin_comision


def texto_linea(punto):
    if punto == int(punto):
        return str(int(punto))
    return str(punto)

# ---------- NBA: props de esta noche ----------

# Partidos NBA del sabado 21 nov (horas en UTC)
POR_NYK = ("por_nyk", "Trail Blazers @ Knicks", "2026-11-22T00:30:00Z")
LAC_DAL = ("lac_dal", "Clippers @ Mavericks", "2026-11-22T01:00:00Z")
MEM_MIN = ("mem_min", "Grizzlies @ Timberwolves", "2026-11-22T01:00:00Z")
NOP_SAS = ("nop_sas", "Pelicans @ Spurs", "2026-11-22T01:00:00Z")
BOS_SAC = ("bos_sac", "Celtics @ Kings", "2026-11-22T03:00:00Z")

# jugador, equipo, partido, mercado, linea, momio over, momio under, casa, fuente,
# ultimos 10 partidos (del mas viejo al mas nuevo, Land of Basketball),
# y opcional: otras casas con la misma linea [(casa, over, under), ...] -> consenso y mejor precio
# Momios de bet365 via ScoresAndOdds (la unica columna con casa confirmada)
SAO = "ScoresAndOdds"
B365 = "bet365"
PROPS_NBA = [
    ["Jalen Brunson", "Knicks", POR_NYK, "Puntos", 28.5, -105, -120, B365, SAO,
     [24, 19, 33, 31, 23, 27, 33, 28, 31, 21]],
    ["Damian Lillard", "Trail Blazers", POR_NYK, "Triples", 3.5, 105, -135, B365, SAO,
     [1, 2, 4, 2, 4, 2, 6, 2, 5, 5]],
    ["Donovan Clingan", "Trail Blazers", POR_NYK, "Rebotes", 10.5, -115, -110, B365, SAO,
     [18, 11, 11, 5, 13, 12, 11, 10, 12, 13]],
    ["Josh Hart", "Knicks", POR_NYK, "Rebotes", 6.5, -115, -110, B365, SAO,
     [8, 4, 8, 6, 6, 4, 5, 5, 4, 6]],
    ["Cooper Flagg", "Mavericks", LAC_DAL, "Pts + Reb + Ast", 39.5, -112, -112, B365, SAO,
     [48, 27, 34, 38, 42, 59, 22, 31, 24, 47]],
    ["Daniel Gafford", "Mavericks", LAC_DAL, "Rebotes", 6.5, 100, -125, B365, SAO,
     [7, 7, 4, 1, 5, 2, 3, 3, 4, 6]],
    ["Brook Lopez", "Clippers", LAC_DAL, "Puntos", 13.5, -110, -115, B365, SAO,
     [13, 7, 12, 20, 20, 8, 26, 7, 23, 23]],
    ["Max Strus", "Clippers", LAC_DAL, "Triples", 2.5, -105, -120, B365, SAO,
     [3, 3, 1, 2, 0, 4, 1, 5]],
    ["Rudy Gobert", "Timberwolves", MEM_MIN, "Rebotes", 10.5, 105, -135, B365, SAO,
     [13, 10, 11, 11, 15, 6, 10, 15, 4, 7]],
    ["Jaden McDaniels", "Timberwolves", MEM_MIN, "Puntos", 17.5, -105, -120, B365, SAO,
     [19, 13, 14, 23, 16, 16, 18, 13, 22, 17]],
    ["Zach Edey", "Grizzlies", MEM_MIN, "Rebotes", 7.5, -105, -120, B365, SAO,
     [3, 7, 6, 9, 13, 6, 9, 5, 10, 2]],
    ["Cedric Coward", "Grizzlies", MEM_MIN, "Pts + Reb + Ast", 28.5, -120, -105, B365, SAO,
     [22, 36, 19, 13, 30, 27, 39, 32, 28, 27]],
    ["Zion Williamson", "Pelicans", NOP_SAS, "Puntos", 20.5, -110, -115, B365, SAO,
     [25, 23, 13, 25, 29, 22, 24, 16, 24, 22]],
    ["Jeremiah Fears", "Pelicans", NOP_SAS, "Asistencias", 5.5, -112, -112, B365, SAO,
     [7, 2, 5, 5, 8, 5, 7, 7, 10, 4]],
    ["Keldon Johnson", "Spurs", NOP_SAS, "Puntos", 11.5, -105, -120, B365, SAO,
     [15, 4, 3, 10, 4, 10, 18, 11, 4, 10]],
    ["Paul George", "Celtics", BOS_SAC, "Triples", 3.5, -105, -120, B365, SAO,
     [1, 2, 3, 5, 2, 5, 6, 1, 5, 1]],
    ["Neemias Queta", "Celtics", BOS_SAC, "Rebotes", 6.5, -145, 115, B365, SAO,
     [6, 8, 6, 12, 3, 8, 6, 13, 6, 10]],
    ["Domantas Sabonis", "Kings", BOS_SAC, "Rebotes", 11.5, -135, 105, B365, SAO,
     [15, 14, 7, 17, 12, 2, 12, 13, 13, 16]],
    ["Darius Acuff Jr.", "Kings", BOS_SAC, "Asistencias", 6.5, 102, -130, B365, SAO,
     [5, 6, 12, 8, 10, 6, 6, 6, 6, 12]],
    ["Zach LaVine", "Kings", BOS_SAC, "Puntos", 17.5, -110, -115, B365, SAO,
     [21, 11, 23, 21, 14, 15, 31, 12, 18, 19]],
]

# ---------- NFL semana 11: props de jugadores ----------
# Mismo formato. Valores: todos los partidos que jugo en 2026 (NFL.com game logs), del mas viejo al mas nuevo.
ARI_KC = ("nfl_ARI_KC", "Cardinals @ Chiefs", "2026-11-22T18:00:00Z")
BAL_CAR = ("nfl_BAL_CAR", "Ravens @ Panthers", "2026-11-22T18:00:00Z")
NO_CHI = ("nfl_NO_CHI", "Saints @ Bears", "2026-11-22T18:00:00Z")
TEN_DAL = ("nfl_TEN_DAL", "Titans @ Cowboys", "2026-11-22T18:00:00Z")
JAX_NYG = ("nfl_JAX_NYG", "Jaguars @ Giants", "2026-11-22T21:25:00Z")
MIN_SF = ("nfl_MIN_SF", "Vikings @ 49ers (Estadio Banorte, CDMX)", "2026-11-23T01:20:00Z")
CIN_WSH = ("nfl_CIN_WSH", "Bengals @ Commanders", "2026-11-24T01:15:00Z")
SFA = "Sharp Football Analysis"
COV = "Covers"
PROPS_NFL = [
    ["Trey McBride", "Cardinals", ARI_KC, "Yardas por recepcion", 48.5, -135, None, "Fanatics", COV,
     [95, 41, 75, 31, 66, 53, 111, 72, 54, 37]],
    ["Derrick Henry", "Ravens", BAL_CAR, "Yardas por tierra", 65.5, -115, None, "BetMGM", COV,
     [144, 68, 89, 73, 102, 58, 45, 53, 57, 10]],
    ["Chris Olave", "Saints", NO_CHI, "Yardas por recepcion", 69.5, -120, None, "Fanatics", COV,
     [182, 86, 107, 116, 46, 43, 56, 98, 30]],
    ["Caleb Williams", "Bears", NO_CHI, "Yardas por pase", 249.5, None, -114, "FanDuel", COV,
     [269, 138, 305, 308, 247, 279]],
    ["Dak Prescott", "Cowboys", TEN_DAL, "Yardas por pase", 278.5, -120, None, "Fanatics", COV,
     [175, 279, 276, 335, 316, 258, 212, 195, 335, 343]],
    ["Cam Skattebo", "Giants", JAX_NYG, "Yardas por tierra", 54.5, -125, None, "Fanatics", COV,
     [81, 36, 60, 58, 59, 0, 124, 78]],
    ["Justin Jefferson", "Vikings", MIN_SF, "Yardas por recepcion", 82.5, -114, -114, "DraftKings", SFA,
     [92, 55, 32, 79, 44, 33, 58, 74]],
    ["Joe Burrow", "Bengals", CIN_WSH, "Yardas por pase", 300.5, -114, -114, "FanDuel (over) / DraftKings (under)", SFA,
     [254, 207, 282, 428, 190, 292, 462, 271, 409]],
    ["Ja'Marr Chase", "Bengals", CIN_WSH, "Yardas por recepcion", 93.5, -114, -114, "FanDuel (over) / DraftKings (under)", SFA,
     [12, 75, 98, 27, 77, 62, 141, 155, 231]],
]

# ---------- Draftea (o cualquier casa con lineas alternas) ----------
# Si en Draftea ves otra linea para un jugador de arriba, pegala aqui con su momio:
#   [jugador, mercado, lado, linea, momio]   ej. ["Jalen Brunson", "Puntos", "Over", 22.5, -250]
# El motor la evalua con la linea principal del mercado + sus ultimos partidos y,
# si pasa las reglas (55%, 3% de ventaja, nivel A o B), sale como pick.
DRAFTEA = [
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
# (partidos, goles a favor, goles en contra)  ESPN standings (hasta el 20 nov)
NHL_EQUIPOS = {
    "VGK": ("Golden Knights", 24, 80, 71), "WPG": ("Jets", 23, 71, 77),
    "NJ": ("Devils", 22, 82, 64), "STL": ("Blues", 22, 68, 67),
    "NYI": ("Islanders", 21, 68, 61), "DET": ("Red Wings", 22, 58, 68),
    "LA": ("Kings", 20, 56, 66), "OTT": ("Senators", 23, 75, 68),
    "PHI": ("Flyers", 25, 63, 85), "MTL": ("Canadiens", 23, 74, 67),
    "CBJ": ("Blue Jackets", 20, 50, 65), "TOR": ("Maple Leafs", 24, 75, 86),
    "WSH": ("Capitals", 20, 67, 76), "BOS": ("Bruins", 22, 76, 56),
    "ANA": ("Ducks", 23, 85, 89), "UTA": ("Mammoth", 23, 77, 79),
    "SEA": ("Kraken", 19, 64, 67), "SJ": ("Sharks", 24, 65, 86),
    "MIN": ("Wild", 24, 87, 52), "VAN": ("Canucks", 24, 67, 105),
}

# visitante, local, linea, over, under, hora UTC  (PickDawgz; coincide con ScoresAndOdds)
NHL_PARTIDOS = [
    ("VGK", "WPG", 6.5, -105, -115, "2026-11-22T00:00:00Z"),
    ("NJ", "STL", 6.5, 114, -135, "2026-11-22T00:00:00Z"),
    ("NYI", "DET", 5.5, -135, 114, "2026-11-22T00:00:00Z"),
    ("LA", "OTT", 5.5, -122, 102, "2026-11-22T00:00:00Z"),
    ("PHI", "MTL", 5.5, -125, 105, "2026-11-22T00:00:00Z"),
    ("CBJ", "TOR", 6.5, 105, -125, "2026-11-22T00:00:00Z"),
    ("WSH", "BOS", 6.5, -115, -105, "2026-11-22T00:00:00Z"),
    ("ANA", "UTA", 6.5, -142, 120, "2026-11-22T02:00:00Z"),
    ("SEA", "SJ", 6.5, -108, -112, "2026-11-22T03:00:00Z"),
    ("MIN", "VAN", 6.5, -102, -118, "2026-11-22T03:00:00Z"),
]


# ---------- Futbol (20 al 23 nov): totales ----------
# Equipo: (partidos, goles a favor, goles en contra)  FOX Sports standings
# Momios: FOX Sports (casa no indicada). local, visitante, linea, over, under, hora UTC
EPL_EQUIPOS = {
    "Arsenal": (10, 15, 5), "Brighton": (10, 26, 7), "Man City": (10, 21, 13), "Liverpool": (10, 14, 10),
    "Chelsea": (10, 19, 16), "Everton": (10, 12, 10), "Bournemouth": (10, 16, 14), "Brentford": (10, 16, 11),
    "Leeds": (10, 10, 8), "Aston Villa": (10, 14, 17), "Tottenham": (10, 10, 11), "Newcastle": (10, 13, 16),
    "Hull City": (10, 11, 11), "Ipswich": (10, 15, 20), "Fulham": (10, 10, 12), "Nottm Forest": (10, 9, 13),
    "Coventry": (10, 10, 19), "Man United": (10, 14, 19), "Sunderland": (10, 8, 17), "Crystal Palace": (10, 10, 24),
}
EPL_PARTIDOS = [
    ("Man City", "Fulham", 3.5, 119, -157, "2026-11-21T12:30:00Z"),
    ("Aston Villa", "Sunderland", 2.5, -140, 105, "2026-11-21T15:00:00Z"),
    ("Bournemouth", "Nottm Forest", 2.5, -124, -103, "2026-11-21T15:00:00Z"),
    ("Chelsea", "Leeds", 2.5, -136, 105, "2026-11-21T15:00:00Z"),
    ("Tottenham", "Ipswich", 2.5, -173, 133, "2026-11-21T15:00:00Z"),
    ("Newcastle", "Arsenal", 2.5, -142, 112, "2026-11-21T17:30:00Z"),
    ("Hull City", "Brighton", 2.5, -157, 121, "2026-11-22T14:00:00Z"),
    ("Liverpool", "Man United", 3.5, 123, -159, "2026-11-22T16:30:00Z"),
    ("Brentford", "Everton", 2.5, -145, 105, "2026-11-23T20:00:00Z"),
]

LALIGA_EQUIPOS = {
    "Barcelona": (12, 48, 13), "Real Madrid": (12, 31, 10), "Atletico": (12, 23, 10), "Betis": (12, 20, 15),
    "Real Sociedad": (12, 21, 20), "Sevilla": (12, 17, 19), "Athletic": (11, 15, 11), "Villarreal": (12, 17, 15),
    "Deportivo": (12, 15, 14), "Racing Santander": (12, 17, 30), "Celta": (12, 10, 10), "Alaves": (12, 15, 17),
    "Espanyol": (12, 13, 14), "Rayo": (11, 15, 21), "Getafe": (12, 8, 18), "Osasuna": (12, 12, 23),
    "Levante": (12, 16, 21), "Elche": (12, 14, 20), "Valencia": (12, 8, 20), "Malaga": (12, 9, 23),
}
LALIGA_PARTIDOS = [
    ("Athletic", "Espanyol", 2.5, -127, -100, "2026-11-20T20:00:00Z"),
    ("Alaves", "Deportivo", 2.5, 114, -147, "2026-11-21T13:00:00Z"),
    ("Rayo", "Valencia", 2.5, 101, -129, "2026-11-21T15:15:00Z"),
    ("Sevilla", "Betis", 2.5, -135, 106, "2026-11-21T17:30:00Z"),
    ("Real Madrid", "Celta", 3.5, -103, -125, "2026-11-21T20:00:00Z"),
    ("Barcelona", "Villarreal", 4.5, 108, -139, "2026-11-22T13:00:00Z"),
    ("Racing Santander", "Real Sociedad", 3.5, -116, -109, "2026-11-22T15:15:00Z"),
    ("Osasuna", "Malaga", 2.5, -103, -125, "2026-11-22T17:30:00Z"),
    ("Getafe", "Atletico", 2.5, 100, -130, "2026-11-22T20:00:00Z"),
]

SERIEA_EQUIPOS = {
    "Lazio": (11, 25, 9), "Inter": (11, 28, 13), "Roma": (11, 31, 10), "Milan": (11, 23, 13), "Como": (11, 18, 10),
    "Frosinone": (11, 24, 15), "Juventus": (11, 15, 12), "Bologna": (11, 16, 14), "Cagliari": (11, 10, 15),
    "Napoli": (11, 18, 14), "Torino": (11, 15, 17), "Atalanta": (11, 17, 20), "Genoa": (11, 11, 16),
    "Lecce": (11, 12, 22), "Fiorentina": (11, 17, 25), "Parma": (11, 9, 17), "Sassuolo": (11, 16, 29),
    "Monza": (11, 17, 25), "Venezia": (11, 8, 21), "Udinese": (11, 12, 25),
}
SERIEA_PARTIDOS = [
    ("Como", "Cagliari", 2.5, -192, 150, "2026-11-21T14:00:00Z"),
    ("Lazio", "Lecce", 2.5, -175, 136, "2026-11-21T14:00:00Z"),
    ("Parma", "Roma", 2.5, -189, 142, "2026-11-21T17:00:00Z"),
    ("Napoli", "Torino", 2.5, -151, 114, "2026-11-21T19:45:00Z"),
    ("Juventus", "Venezia", 2.5, -168, 127, "2026-11-22T11:30:00Z"),
    ("Bologna", "Udinese", 2.5, -112, -115, "2026-11-22T14:00:00Z"),
    ("Sassuolo", "Genoa", 2.5, -112, -114, "2026-11-22T14:00:00Z"),
    ("Milan", "Frosinone", 3.5, -115, -113, "2026-11-22T17:00:00Z"),
    ("Atalanta", "Inter", 3.5, -101, -130, "2026-11-22T19:45:00Z"),
    ("Monza", "Fiorentina", 2.5, -174, 132, "2026-11-23T19:45:00Z"),
]

BUNDES_EQUIPOS = {
    "Bayern": (9, 29, 9), "Dortmund": (9, 16, 7), "Freiburg": (9, 20, 10), "Leipzig": (9, 27, 13),
    "Leverkusen": (9, 20, 17), "Werder": (9, 17, 15), "Elversberg": (9, 17, 18), "Stuttgart": (9, 15, 15),
    "Hoffenheim": (9, 16, 17), "Frankfurt": (9, 15, 20), "Hamburg": (9, 10, 20), "Mainz": (9, 18, 19),
    "Paderborn": (9, 8, 11), "Augsburg": (9, 20, 20), "Koln": (9, 10, 14), "Union Berlin": (9, 7, 21),
    "Schalke": (9, 5, 11), "Gladbach": (9, 12, 25),
}
BUNDES_PARTIDOS = [
    ("Bayern", "Koln", 4.5, -109, -117, "2026-11-20T19:30:00Z"),
    ("Leverkusen", "Paderborn", 3.5, -115, -111, "2026-11-21T14:30:00Z"),
    ("Frankfurt", "Hoffenheim", 3.5, -114, -112, "2026-11-21T14:30:00Z"),
    ("Union Berlin", "Leipzig", 3.5, 109, -143, "2026-11-21T14:30:00Z"),
    ("Gladbach", "Dortmund", 3.5, 117, -152, "2026-11-21T14:30:00Z"),
    ("Elversberg", "Freiburg", 2.5, -185, 140, "2026-11-21T14:30:00Z"),
    ("Schalke", "Stuttgart", 3.5, 113, -149, "2026-11-21T17:30:00Z"),
    ("Augsburg", "Mainz", 3.5, 105, -137, "2026-11-22T14:30:00Z"),
    ("Werder", "Hamburg", 3.5, 126, -168, "2026-11-22T16:30:00Z"),
]

LIGAMX_EQUIPOS = {
    "Cruz Azul": (16, 37, 26), "America": (16, 38, 23), "Guadalajara": (16, 26, 15), "Toluca": (16, 35, 21),
    "Atlas": (16, 27, 30), "Santos": (16, 23, 20), "Monterrey": (16, 27, 25), "Leon": (16, 23, 21),
    "Pachuca": (16, 29, 20), "Tijuana": (16, 25, 22), "Pumas": (16, 24, 26), "Queretaro": (16, 18, 24),
    "Puebla": (16, 19, 23), "San Luis": (16, 19, 24), "Tigres": (16, 17, 25), "Atlante": (16, 16, 26),
    "Necaxa": (16, 17, 28), "Juarez": (16, 13, 34),
}
LIGAMX_PARTIDOS = [
    ("Puebla", "San Luis", 2.5, -147, 110, "2026-11-21T01:00:00Z"),
    ("Juarez", "Atlas", 2.5, -148, 111, "2026-11-21T03:00:00Z"),
    ("Tijuana", "Atlante", 2.5, -156, 116, "2026-11-21T03:00:00Z"),
    ("Pachuca", "Toluca", 3.5, 108, -145, "2026-11-21T22:50:00Z"),
    ("Santos", "Leon", 3.5, 123, -168, "2026-11-21T23:00:00Z"),
    ("Pumas", "Monterrey", 2.5, -164, 123, "2026-11-22T01:00:00Z"),
    ("Queretaro", "Necaxa", 2.5, -177, 130, "2026-11-23T01:10:00Z"),
]


# ---------- Ultimo enfrentamiento ----------
# Por partido (la misma clave "evento" que usan los picks).
# marcador: [[visitante, puntos], [local, puntos]]  -  los nombres deben ser
# iguales a los que salen en el pick (ej. "Colts +12.5" -> "Colts").
# Solo datos verificados; si no se encuentra, no se pone.
BR = "https://www.basketball-reference.com/boxscores/"
CBS = "https://www.cbssports.com/nfl/gametracker/boxscore/"
LOB_H2H = "https://www.landofbasketball.com/head_to_head_games/last_3/"
ULTIMO_DUELO = {
    "por_nyk": {"fecha": "2026-01-30", "liga": "NBA 2025-26", "marcador": [["Trail Blazers", 97], ["Knicks", 127]],
                "fuente": LOB_H2H + "knicks_vs_trail_blazers_all.htm"},
    "lac_dal": {"fecha": "2026-04-07", "liga": "NBA 2025-26 (se jugo en Los Angeles)", "marcador": [["Mavericks", 103], ["Clippers", 116]],
                "fuente": LOB_H2H + "clippers_vs_mavericks_all.htm"},
    "mem_min": {"fecha": "2026-03-03", "liga": "NBA 2025-26", "marcador": [["Grizzlies", 110], ["Timberwolves", 117]],
                "fuente": LOB_H2H + "grizzlies_vs_timberwolves_all.htm"},
    "nop_sas": {"fecha": "2026-01-25", "liga": "NBA 2025-26", "marcador": [["Pelicans", 104], ["Spurs", 95]],
                "fuente": LOB_H2H + "pelicans_vs_spurs_all.htm"},
    "bos_sac": {"fecha": "2026-01-30", "liga": "NBA 2025-26 (se jugo en Boston)", "marcador": [["Kings", 93], ["Celtics", 112]],
                "fuente": LOB_H2H + "celtics_vs_kings_all.htm"},
    "nhl_LA_OTT": {"fecha": "2026-10-29", "liga": "NHL 2026-27 (se jugo en Los Angeles, tiempo extra)", "marcador": [["Senators", 5], ["Kings", 6]],
                   "fuente": "https://www.ksl.com/article/51642470/kings-beat-senators-6-5-in-ot-after-blowing-a-4-goal-lead-in-the-3rd-period"},
    "nhl_CBJ_TOR": {"fecha": "2026-10-20", "liga": "NHL 2026-27 (se jugo en Columbus)", "marcador": [["Maple Leafs", 6], ["Blue Jackets", 2]],
                    "fuente": "https://bvmsports.com/2026/10/21/maple-leafs-rout-blue-jackets-6-2-as-marchenko-cowan-shine/"},
    "nhl_NJ_STL": {"fecha": "2026-11-05", "liga": "NHL 2026-27 (se jugo en New Jersey, tiempo extra)", "marcador": [["Blues", 4], ["Devils", 5]],
                   "fuente": "https://fieldlevelmedia.com/news/devils-blow-three-goal-lead-hang-on-for-ot-win-over-blues/"},
    "nhl_MIN_VAN": {"fecha": "2026-10-25", "liga": "NHL 2026-27", "marcador": [["Wild", 4], ["Canucks", 2]],
                    "fuente": "https://www.nhl.com/wild/news/minnesota-wild-vancouver-canucks-game-recap-october-25-2026-x2730"},
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
                              "fuente": "https://www.sportsmole.co.uk/football/premier-league/newcastle-united-vs-arsenal_game_263178.html"},
}

# Ultimo partido de cada jugador contra el rival de hoy (puede ser con otro equipo)
# pts, reb, ast, tri (triples metidos), min (minutos)
ULTIMO_DUELO_JUGADOR = {
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
    "Zion Williamson": [ajuste("Under", 0.02, "Segunda noche seguida: Pelicans jugaron anoche en Oklahoma City")],
    "Jeremiah Fears": [ajuste("Under", 0.02, "Segunda noche seguida: Pelicans jugaron anoche en Oklahoma City")],
    "Domantas Sabonis": [ajuste("Under", 0.02, "Segunda noche seguida: Kings jugaron anoche en Los Angeles")],
    "Darius Acuff Jr.": [ajuste("Under", 0.02, "Segunda noche seguida: Kings jugaron anoche en Los Angeles")],
    "Zach LaVine": [ajuste("Under", 0.02, "Segunda noche seguida: Kings jugaron anoche en Los Angeles")],
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
    "LaLiga": (LALIGA_EQUIPOS, LALIGA_PARTIDOS, "laliga", "soccer_spain_la_liga", "FOX Sports"),
    "Serie A": (SERIEA_EQUIPOS, SERIEA_PARTIDOS, "seriea", "soccer_italy_serie_a", "FOX Sports"),
    "Bundesliga": (BUNDES_EQUIPOS, BUNDES_PARTIDOS, "bundes", "soccer_germany_bundesliga", "FOX Sports"),
    "Liga MX": (LIGAMX_EQUIPOS, LIGAMX_PARTIDOS, "ligamx", "soccer_mexico_ligamx", "FOX Sports"),
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


NOTA = ("Edicion del " + EDICION + ": 20 props NBA de esta noche (5 partidos), 10 partidos NHL de la noche, props y lineas "
        "NFL semana 11 (domingo y lunes), seccion 'Baja la linea' para lineas alternas tipo Draftea y futbol del fin de semana "
        "(Premier, LaLiga, Serie A, Bundesliga y Liga MX). Cada pick pasa por el motor de PickLab y solo se publica con 55% o mas "
        "de probabilidad, 3% o mas de ventaja y nivel A o B. Edicion a mano (sin API de momios).")

FUENTES = [
    ["ScoresAndOdds - props NBA 21 nov (bet365)", "https://www.scoresandodds.com/nba/props"],
    ["Land of Basketball - ultimos 10 y enfrentamientos NBA", "https://www.landofbasketball.com/head_to_head_games/"],
    ["Champs or Chumps - head to head NBA", "https://champsorchumps.us/"],
    ["ESPN - lesiones NBA", "https://www.espn.com/nba/injuries"],
    ["PickDawgz - totales NHL 21 nov", "https://www.pickdawgz.com/nhl-picks/"],
    ["ScoresAndOdds - totales NHL", "https://www.scoresandodds.com/nhl"],
    ["ESPN - tabla NHL (goles a favor y en contra)", "https://www.espn.com/nhl/standings/_/view"],
    ["Resultados 20 nov - ESPN (Rockets @ Nuggets)", "https://www.espn.com/nba/recap?gameId=401909312"],
    ["Resultados 20 nov - ESPN (Wizards @ Bulls)", "https://www.espn.com/nba/boxscore/_/gameId/401909309"],
    ["ESPN - momios NFL semana 11 (DraftKings)", "https://www.espn.com/nfl/odds"],
    ["ESPN - tabla NFL (puntos a favor y en contra)", "https://www.espn.com/nfl/standings"],
    ["FOX Sports - momios y tabla Premier League", "https://www.foxsports.com/soccer/premier-league/standings"],
    ["FOX Sports - momios y tabla LaLiga", "https://www.foxsports.com/soccer/la-liga/standings"],
    ["FOX Sports - momios y tabla Serie A", "https://www.foxsports.com/soccer/serie-a/standings"],
    ["FOX Sports - momios y tabla Bundesliga", "https://www.foxsports.com/soccer/bundesliga/standings"],
    ["FOX Sports - momios y tabla Liga MX", "https://www.foxsports.com/soccer/liga-mx/standings"],
    ["Sharp Football Analysis - props NFL semana 11", "https://www.sharpfootballanalysis.com/betting/nfl-player-props-odds-picks-predictions/"],
    ["Covers - props NFL", "https://www.covers.com/sport/football/nfl/player-props"],
    ["NFL.com - game logs 2026 de jugadores", "https://www.nfl.com/players/"],
    ["Rotowire - alineaciones y lesiones NBA", "https://www.rotowire.com/basketball/nba-lineups.php"],
    ["Land of Basketball - ultimos 10 partidos NBA", "https://www.landofbasketball.com/"],
    ["Ultimos enfrentamientos NFL - CBS Sports y StatMuse", "https://www.statmuse.com/nfl"],
]


if __name__ == "__main__":
    main()
