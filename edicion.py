# ============================================
# EDICION SEMANAL DE PICKLAB (datos juntados a mano)
# Edicion: martes 17 de noviembre de 2026
#
# Fuentes:
#  - Lineas NFL y NHL: ESPN Odds (DraftKings)
#  - Lineas Premier League: Betwatch
#  - Props NBA: DraftKings Network, FanDuel Research, Steezanomics
#  - Estadisticas: ESPN (standings y game logs)
#
# Uso: python edicion.py  -> escribe web/picks.js
# ============================================

import json
import math
from datetime import datetime
from calcular_picks import prob_implicita, a_decimal, a_americano

EDICION = "martes 17 de noviembre"

# ---------- Funciones de probabilidad ----------

def normal_mayor(x, media, desv):
    # Probabilidad de que un valor normal sea mayor que x
    return 0.5 * (1 - math.erf((x - media) / (desv * math.sqrt(2))))


def poisson(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_mayor(linea, lam):
    # Probabilidad de que el total de goles sea mayor que la linea (ej. 5.5)
    hasta = int(math.floor(linea))
    suma = 0
    for k in range(hasta + 1):
        suma += poisson(k, lam)
    return 1 - suma


def sin_comision(momio_a, momio_b):
    pa = prob_implicita(momio_a)
    pb = prob_implicita(momio_b)
    return pa / (pa + pb), pb / (pa + pb)


def texto_linea(punto):
    if punto == int(punto):
        return str(int(punto))
    return str(punto)


# ---------- NBA: props de esta noche ----------

KNICKS_RAPTORS = ("nyk_tor", "Knicks @ Raptors", "2026-11-18T00:30:00Z")
PISTONS_SPURS = ("det_sas", "Pistons @ Spurs", "2026-11-18T01:00:00Z")
HORNETS_LAKERS = ("cha_lal", "Hornets @ Lakers", "2026-11-18T04:00:00Z")

PROPS_NBA = [
    ["Luka Doncic", "Lakers", HORNETS_LAKERS, "Triples", 4.5, -124, -106, "DraftKings", "DK Network",
     [8, 6, 6, 8, 6, 6, 5, 3, 5, 5]],
    ["Victor Wembanyama", "Spurs", PISTONS_SPURS, "Puntos + Asistencias", 31.5, -109, -121, "DraftKings", "DK Network",
     [41, 47, 17, 54, 32, 32, 43, 33, 18, 32]],
    ["Jalen Brunson", "Knicks", KNICKS_RAPTORS, "Triples", 2.5, 117, -155, "DraftKings", "DK Network",
     [0, 6, 3, 4, 5, 3, 1, 3, 4, 3]],
    ["Quentin Grimes", "Lakers", HORNETS_LAKERS, "Puntos", 12.5, -124, -103, "DraftKings", "DK Network",
     [3, 2, 23, 3, 7, 7, 6, 2, 12, 22]],
    ["RJ Barrett", "Raptors", KNICKS_RAPTORS, "Puntos", 19.5, -106, None, "FanDuel", "FanDuel Research",
     [25, 9, 22, 26, 22, 27, 19, 12, 31, 14]],
    ["Karl-Anthony Towns", "Knicks", KNICKS_RAPTORS, "Rebotes", 12.5, -105, None, "Bovada", "Steezanomics",
     [20, 13, 12, 16, 12, 13, 16, 11, 15, 17]],
    ["Scottie Barnes", "Raptors", KNICKS_RAPTORS, "Pts + Reb + Ast", 34.5, 105, None, "Bovada", "Steezanomics",
     [34, 47, 6, 38, 51, 40, 45, 29, 43]],
    ["LaMelo Ball", "Hornets", HORNETS_LAKERS, "Puntos", 21.5, None, -120, "FanDuel", "FanDuel Research",
     [8, 24, 10, 34, 20, 22, 24, 22, 19, 6]],
    ["Coby White", "Hornets", HORNETS_LAKERS, "Asistencias", 3.5, None, -106, "NoVig", "Steezanomics",
     [3, 2, 1, 9, 3, 1]],
]


def evaluar_prop(lado, linea, momio, prob_mercado, valores):
    aciertos = 0
    for v in valores:
        if lado == "Over" and v > linea:
            aciertos += 1
        if lado == "Under" and v < linea:
            aciertos += 1
    prob = 0.6 * aciertos / len(valores) + 0.4 * prob_mercado
    return {"lado": lado, "momio": momio, "aciertos": aciertos, "prob": prob,
            "ventaja": prob - prob_implicita(momio)}


def picks_nba():
    picks = []
    descartados = []
    for jugador, equipo, partido, mercado, linea, over, under, casa, fuente, valores in PROPS_NBA:
        opciones = []
        if over is not None and under is not None:
            p_over, p_under = sin_comision(over, under)
            opciones.append(evaluar_prop("Over", linea, over, p_over, valores))
            opciones.append(evaluar_prop("Under", linea, under, p_under, valores))
            base = "Ultimos " + str(len(valores)) + " partidos + momio sin comision"
        else:
            lado = "Over" if over is not None else "Under"
            momio = over if over is not None else under
            opciones.append(evaluar_prop(lado, linea, momio, prob_implicita(momio), valores))
            base = "Ultimos " + str(len(valores)) + " partidos + momio de la casa"
        mejor = max(opciones, key=lambda o: o["ventaja"])
        ordenados = sorted(valores)
        pick = {
            "evento": partido[0], "grupo": "NBA", "liga": "NBA",
            "partido": partido[1], "fecha": partido[2], "tipo": "Props",
            "mercado": mercado, "jugador": jugador, "equipo": equipo,
            "pick": jugador + " " + mejor["lado"] + " " + str(linea),
            "lado": mejor["lado"], "linea": linea, "momio": mejor["momio"],
            "casa": casa, "casas": 1, "prob": mejor["prob"], "ventaja": mejor["ventaja"],
            "valores": valores, "aciertos": mejor["aciertos"],
            "promedio": round(sum(valores) / len(valores), 1),
            "mediana": ordenados[len(ordenados) // 2],
            "maximo": max(valores), "minimo": min(valores),
            "base": base + ". Linea via " + fuente + ", partidos via ESPN",
        }
        if mejor["ventaja"] > 0:
            picks.append(pick)
        else:
            descartados.append(pick["pick"])
    return picks, descartados


# ---------- Modelo para spreads y totales ----------
# Probabilidad final = 50% nuestro modelo + 50% el mercado sin comision.
# Asi no nos vamos a numeros exagerados con muestras chicas.
# Solo publicamos si la ventaja es de al menos 3%.
VENTAJA_MINIMA = 0.03

def elegir(opciones):
    mejor = None
    for op in opciones:
        op["prob"] = 0.5 * op["modelo"] + 0.5 * op["mercado"]
        op["ventaja"] = op["prob"] - prob_implicita(op["momio"])
        if mejor is None or op["ventaja"] > mejor["ventaja"]:
            mejor = op
    return mejor


def armar_pick(evento, grupo, liga, partido, fecha, tipo, mercado, op, casa, explicacion):
    return {
        "evento": evento, "grupo": grupo, "liga": liga, "partido": partido, "fecha": fecha,
        "tipo": tipo, "mercado": mercado, "pick": op["texto"], "momio": op["momio"],
        "casa": casa, "casas": 1, "prob": op["prob"], "ventaja": op["ventaja"],
        "modelo": round(op["modelo"] * 100, 1), "mercado_prob": round(op["mercado"] * 100, 1),
        "explicacion": explicacion,
        "base": "50% modelo con estadisticas de la temporada + 50% momio sin comision",
    }


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


def picks_nfl():
    picks = []
    for vis, loc, spread_loc, m_vis, m_loc, total, m_over, m_under, fecha, neutral in NFL_PARTIDOS:
        nv, gv, pfv, pav = NFL_EQUIPOS[vis]
        nl, gl, pfl, pal = NFL_EQUIPOS[loc]
        ventaja_casa = 0 if neutral else 1.0
        pts_loc = (pfl / gl + pav / gv) / 2 + ventaja_casa
        pts_vis = (pfv / gv + pal / gl) / 2 - ventaja_casa
        proy_total = pts_loc + pts_vis
        proy_margen = pts_loc - pts_vis
        partido = nv + " @ " + nl + (" (Estadio Banorte, CDMX)" if neutral else "")
        evento = "nfl_" + vis + "_" + loc

        # Total
        p_over_m, p_under_m = sin_comision(m_over, m_under)
        p_over = normal_mayor(total, proy_total, 13.5)
        op = elegir([
            {"texto": "Over " + texto_linea(total), "momio": m_over, "modelo": p_over, "mercado": p_over_m},
            {"texto": "Under " + texto_linea(total), "momio": m_under, "modelo": 1 - p_over, "mercado": p_under_m},
        ])
        if op["ventaja"] >= VENTAJA_MINIMA:
            explicacion = ("Con sus puntos a favor y en contra de esta temporada, proyectamos " +
                           nl + " " + str(round(pts_loc, 1)) + " y " + nv + " " + str(round(pts_vis, 1)) +
                           ": total de " + str(round(proy_total, 1)) + " puntos contra una linea de " +
                           texto_linea(total) + ".")
            picks.append(armar_pick(evento, "NFL", "NFL", partido, fecha, "Totales", "Total de puntos",
                                    op, "DraftKings", explicacion))

        # Spread (margen del local mayor a -spread)
        p_vis_m, p_loc_m = sin_comision(m_vis, m_loc)
        p_loc_cubre = normal_mayor(-spread_loc, proy_margen, 13.5)
        signo_loc = "+" if spread_loc > 0 else ""
        signo_vis = "+" if -spread_loc > 0 else ""
        op = elegir([
            {"texto": nl + " " + signo_loc + texto_linea(spread_loc), "momio": m_loc, "modelo": p_loc_cubre, "mercado": p_loc_m},
            {"texto": nv + " " + signo_vis + texto_linea(-spread_loc), "momio": m_vis, "modelo": 1 - p_loc_cubre, "mercado": p_vis_m},
        ])
        if op["ventaja"] >= VENTAJA_MINIMA:
            explicacion = ("Proyectamos que " + nl + " termine con un margen de " +
                           ("+" if proy_margen > 0 else "") + str(round(proy_margen, 1)) +
                           " puntos, contra un spread de " + signo_loc + texto_linea(spread_loc) + " para " + nl + ".")
            picks.append(armar_pick(evento, "NFL", "NFL", partido, fecha, "Spreads", "Spread",
                                    op, "DraftKings", explicacion))
    return picks


# ---------- NHL de hoy: totales ----------
# Equipo: (nombre, partidos, goles a favor, goles en contra)  ESPN standings
NHL_EQUIPOS = {
    "LA": ("Kings", 18, 49, 63), "BOS": ("Bruins", 20, 72, 52), "EDM": ("Oilers", 22, 87, 60),
    "FLA": ("Panthers", 22, 70, 63), "CBJ": ("Blue Jackets", 18, 45, 58), "NYI": ("Islanders", 19, 60, 56),
    "BUF": ("Sabres", 20, 55, 70), "PHI": ("Flyers", 23, 53, 77), "OTT": ("Senators", 21, 68, 61),
    "WPG": ("Jets", 21, 66, 72), "WSH": ("Capitals", 18, 62, 65), "TB": ("Lightning", 20, 74, 59),
    "TOR": ("Maple Leafs", 22, 69, 76), "CHI": ("Blackhawks", 20, 46, 83), "ANA": ("Ducks", 21, 79, 77),
    "STL": ("Blues", 20, 55, 59), "NSH": ("Predators", 21, 64, 59), "MIN": ("Wild", 22, 76, 48),
    "DAL": ("Stars", 20, 56, 50), "VGK": ("Golden Knights", 22, 74, 63), "CGY": ("Flames", 21, 51, 74),
    "SJ": ("Sharks", 23, 63, 81),
}

NHL_PARTIDOS = [
    ("LA", "BOS", 5.5, -135, 114, "2026-11-18T00:00:00Z"),
    ("EDM", "FLA", 6.5, 114, -135, "2026-11-18T00:00:00Z"),
    ("CBJ", "NYI", 5.5, -118, -102, "2026-11-18T00:00:00Z"),
    ("BUF", "PHI", 5.5, -135, 114, "2026-11-18T00:00:00Z"),
    ("OTT", "WPG", 5.5, -130, 110, "2026-11-18T00:00:00Z"),
    ("WSH", "TB", 6.5, -110, -110, "2026-11-18T00:30:00Z"),
    ("TOR", "CHI", 6.5, -105, -115, "2026-11-18T00:30:00Z"),
    ("ANA", "STL", 6.5, -102, -118, "2026-11-18T01:00:00Z"),
    ("NSH", "MIN", 6.5, 114, -135, "2026-11-18T01:00:00Z"),
    ("DAL", "VGK", 5.5, -122, 102, "2026-11-18T03:00:00Z"),
    ("CGY", "SJ", 5.5, -135, 114, "2026-11-18T03:00:00Z"),
]


def picks_nhl():
    picks = []
    for vis, loc, total, m_over, m_under, fecha in NHL_PARTIDOS:
        nv, gv, gfv, gav = NHL_EQUIPOS[vis]
        nl, gl, gfl, gal = NHL_EQUIPOS[loc]
        lam_loc = (gfl / gl + gav / gv) / 2
        lam_vis = (gfv / gv + gal / gl) / 2
        lam = lam_loc + lam_vis
        p_over = poisson_mayor(total, lam)
        p_over_m, p_under_m = sin_comision(m_over, m_under)
        op = elegir([
            {"texto": "Over " + texto_linea(total), "momio": m_over, "modelo": p_over, "mercado": p_over_m},
            {"texto": "Under " + texto_linea(total), "momio": m_under, "modelo": 1 - p_over, "mercado": p_under_m},
        ])
        if op["ventaja"] >= VENTAJA_MINIMA:
            explicacion = ("Con sus goles a favor y en contra de esta temporada, esperamos " +
                           str(round(lam, 2)) + " goles en total (" + nl + " " + str(round(lam_loc, 2)) +
                           ", " + nv + " " + str(round(lam_vis, 2)) + ") contra una linea de " + texto_linea(total) + ".")
            picks.append(armar_pick("nhl_" + vis + "_" + loc, "NHL", "NHL", nv + " @ " + nl, fecha,
                                    "Totales", "Total de goles", op, "DraftKings", explicacion))
    return picks


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


def picks_epl():
    total_goles = 0
    total_partidos = 0
    for eq in EPL_EQUIPOS.values():
        total_goles += eq[1]
        total_partidos += eq[0]
    prom = total_goles / total_partidos  # goles por equipo por partido en la liga

    picks = []
    for loc, vis, total, m_over, m_under, fecha in EPL_PARTIDOS:
        gl, fl, al = EPL_EQUIPOS[loc]
        gv, fv, av = EPL_EQUIPOS[vis]
        # Fuerza de ataque y defensa, jalada 50% hacia el promedio (solo 10 partidos)
        ataque_loc = 0.5 + 0.5 * (fl / gl) / prom
        defensa_loc = 0.5 + 0.5 * (al / gl) / prom
        ataque_vis = 0.5 + 0.5 * (fv / gv) / prom
        defensa_vis = 0.5 + 0.5 * (av / gv) / prom
        lam_loc = prom * 1.1 * ataque_loc * defensa_vis
        lam_vis = prom * 0.9 * ataque_vis * defensa_loc
        lam = lam_loc + lam_vis
        p_over = poisson_mayor(total, lam)
        p_over_m, p_under_m = sin_comision(m_over, m_under)
        op = elegir([
            {"texto": "Over " + texto_linea(total), "momio": m_over, "modelo": p_over, "mercado": p_over_m},
            {"texto": "Under " + texto_linea(total), "momio": m_under, "modelo": 1 - p_over, "mercado": p_under_m},
        ])
        if op["ventaja"] >= VENTAJA_MINIMA:
            explicacion = ("Con sus goles a favor y en contra en la Premier, esperamos " + str(round(lam, 2)) +
                           " goles (" + loc + " " + str(round(lam_loc, 2)) + ", " + vis + " " +
                           str(round(lam_vis, 2)) + ") contra una linea de " + texto_linea(total) + ".")
            picks.append(armar_pick("epl_" + loc + "_" + vis, "Futbol", "Premier League", loc + " vs " + vis,
                                    fecha, "Totales", "Total de goles", op, "Betwatch", explicacion))
    return picks


# ---------- Juntar todo ----------

def main():
    nba, descartados = picks_nba()
    nfl = picks_nfl()
    nhl = picks_nhl()
    epl = picks_epl()
    picks = nba + nfl + nhl + epl

    picks.sort(key=lambda p: p["prob"], reverse=True)
    for i in range(len(picks)):
        p = picks[i]
        p["id"] = i + 1
        p["prob"] = round(p["prob"] * 100, 1)
        p["ventaja"] = round(p["ventaja"] * 100, 1)
        p["implicita"] = round(prob_implicita(p["momio"]) * 100, 1)
        p["unidades"] = 2 if i == 0 else (1 if p["prob"] >= 60 else 0.5)

    # Parlay: los 3 mas probables de partidos y deportes diferentes
    parlay = []
    usados = []
    for p in picks:
        if p["evento"] not in usados:
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

    def contar(grupo):
        return len([p for p in picks if p["grupo"] == grupo])

    grupos = {
        "NFL": {"picks": contar("NFL"), "partidos": len(NFL_PARTIDOS), "ligas": ["NFL semana 11"]},
        "NBA": {"picks": contar("NBA"), "partidos": 5, "ligas": ["NBA"]},
        "Futbol": {"picks": contar("Futbol"), "partidos": len(EPL_PARTIDOS), "ligas": ["Premier League"]},
        "MLB": {"picks": 0, "partidos": 0, "ligas": ["MLB"]},
        "NHL": {"picks": contar("NHL"), "partidos": len(NHL_PARTIDOS), "ligas": ["NHL"]},
        "UFC": {"picks": 0, "partidos": 0, "ligas": ["UFC"]},
        "Tenis": {"picks": 0, "partidos": 0, "ligas": ["ATP / WTA"]},
    }

    salida = {
        "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prueba": False,
        "manual": True,
        "nota": ("Edicion del " + EDICION + ": NBA (props de hoy), NHL (hoy), NFL semana 11 y Premier League "
                 "jornada 11, con lineas y estadisticas reales. MLB esta fuera de temporada; UFC y tenis llegan en la proxima edicion."),
        "fuentes": [
            ["ESPN - momios NFL semana 11 (DraftKings)", "https://www.espn.com/nfl/odds"],
            ["ESPN - tabla NFL (puntos a favor y en contra)", "https://www.espn.com/nfl/standings"],
            ["ESPN - momios NHL (DraftKings)", "https://www.espn.com/nhl/odds"],
            ["ESPN - tabla NHL (goles a favor y en contra)", "https://www.espn.com/nhl/standings"],
            ["Betwatch - momios Premier League", "https://betwatch.io/odds/premier-league"],
            ["ESPN - tabla Premier League", "https://www.espn.com/soccer/standings/_/league/eng.1"],
            ["DraftKings Network - props NBA 17 nov", "https://dknetwork.draftkings.com/2026/11/17/nba-public-betting-trends-tuesday-november-17"],
            ["FanDuel Research - props NBA 17 nov", "https://www.fanduel.com/research/nba-props-today-player-prop-bets-tuesday-nov-17"],
            ["Steezanomics - props NBA 17 nov", "https://steezanomics.com/picks/knicks-vs-raptors-player-props-november-17-2026/"],
            ["ESPN - game logs de jugadores NBA", "https://www.espn.com/nba/"],
        ],
        "partidos_analizados": 5 + len(NFL_PARTIDOS) + len(NHL_PARTIDOS) + len(EPL_PARTIDOS),
        "descartados": descartados,
        "picks": picks,
        "parlay": {"ids": parlay, "momio": a_americano(decimal), "prob": round(prob_parlay * 100, 1)},
        "grupos": grupos,
    }

    with open("web/picks.js", "w", encoding="utf-8") as archivo:
        archivo.write("window.PICKS = ")
        archivo.write(json.dumps(salida, ensure_ascii=False, indent=1))
        archivo.write(";\n")

    for p in picks:
        extra = ""
        if "modelo" in p:
            extra = " | modelo " + str(p["modelo"]) + " mercado " + str(p["mercado_prob"])
        print(p["id"], p["grupo"], "|", p["pick"], "|", p["partido"], "|", p["momio"], "| prob", p["prob"], "| ventaja", p["ventaja"], extra)
    print("Parlay:", salida["parlay"])


if __name__ == "__main__":
    main()
