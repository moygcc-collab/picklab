# ============================================
# EDICION DE PICKLAB
# Edicion: jueves 26 de noviembre de 2026 (NFL semana 12 de jueves a lunes, NHL viernes, Premier y LaLiga)
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

EDICION = "jueves 26 de noviembre"
FECHA_EDICION = "2026-11-26"  # para el historial (AAAA-MM-DD)

sin_comision = motor.sin_comision


def texto_linea(punto):
    if punto == int(punto):
        return str(int(punto))
    return str(punto)

# ---------- NBA: props de esta noche ----------

# Jueves 26 nov (Thanksgiving): no hay NBA. Viernes 27: 11 partidos, pero los props todavia no estaban publicados
# (Covers y BettingPros seguian con los del 25 nov), asi que no entran props NBA en esta edicion.
SAO = "ScoresAndOdds"
PROPS_NBA = [
]


# ---------- NFL semana 11: props de jugadores ----------
# Mismo formato. Valores: todos los partidos que jugo en 2026 (NFL.com game logs), del mas viejo al mas nuevo.
# Semana 12: sin props NFL con momio de los dos lados y game logs verificados en esta edicion
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
# Equipo: (partidos jugados, puntos a favor, puntos en contra)  ESPN standings (semana 11 completa, con el MNF)
NFL_EQUIPOS = {
    "BUF": ("Bills", 10, 313, 208), "MIA": ("Dolphins", 10, 157, 250), "NE": ("Patriots", 10, 221, 242),
    "NYJ": ("Jets", 11, 221, 278), "CLE": ("Browns", 10, 188, 220), "PIT": ("Steelers", 10, 214, 201),
    "BAL": ("Ravens", 11, 242, 294), "CIN": ("Bengals", 10, 298, 215), "TEN": ("Titans", 10, 197, 290),
    "IND": ("Colts", 11, 211, 297), "HOU": ("Texans", 10, 259, 222), "JAX": ("Jaguars", 10, 287, 167),
    "LAC": ("Chargers", 10, 168, 266), "DEN": ("Broncos", 10, 236, 210), "KC": ("Chiefs", 10, 271, 163),
    "LV": ("Raiders", 11, 275, 327), "PHI": ("Eagles", 10, 167, 237), "WSH": ("Commanders", 10, 218, 243),
    "NYG": ("Giants", 10, 226, 214), "DAL": ("Cowboys", 11, 337, 312), "MIN": ("Vikings", 10, 186, 161),
    "GB": ("Packers", 11, 239, 247), "CHI": ("Bears", 10, 262, 197), "DET": ("Lions", 10, 288, 220),
    "ATL": ("Falcons", 10, 201, 258), "NO": ("Saints", 10, 215, 257), "TB": ("Buccaneers", 10, 223, 209),
    "CAR": ("Panthers", 10, 254, 269), "ARI": ("Cardinals", 11, 191, 323), "SEA": ("Seahawks", 10, 223, 175),
    "LAR": ("Rams", 11, 274, 200), "SF": ("49ers", 10, 316, 206),
}

# visitante, local, spread del local, momio visitante, momio local, total, over, under, hora UTC, neutral
# Semana 12 (jueves 26 a lunes 30 nov): DraftKings en VegasInsider (actualizado 24 nov; las lineas se pueden mover)
# Panthers @ Buccaneers (MNF) no entra: la pagina lo marcaba raro como "Final"
NFL_PARTIDOS = [
    ("CHI", "DET", 1.5, -104, -115, 56.5, -106, -113, "2026-11-26T18:00:00Z", False),
    ("PHI", "DAL", -8.5, -108, -111, 49.5, -113, -107, "2026-11-26T21:30:00Z", False),
    ("KC", "BUF", -3, -120, 100, 45.5, -113, -107, "2026-11-27T01:20:00Z", False),
    ("DEN", "PIT", 4.5, -109, -110, 36.5, -119, -101, "2026-11-27T20:00:00Z", False),
    ("NYG", "IND", 6, -109, -110, 41.5, -111, -108, "2026-11-29T18:00:00Z", False),
    ("BAL", "HOU", -6.5, -107, -112, 47.5, -106, -113, "2026-11-29T18:00:00Z", False),
    ("ATL", "MIN", -7, -119, -101, 41.5, -109, -110, "2026-11-29T18:00:00Z", False),
    ("NO", "CIN", -10, -113, -106, 49.5, -111, -108, "2026-11-29T18:00:00Z", False),
    ("NYJ", "MIA", 4.5, -105, -115, 40.5, -104, -115, "2026-11-29T18:00:00Z", False),
    ("TEN", "JAX", -14.5, -116, -104, 49.5, -106, -113, "2026-11-29T18:00:00Z", False),
    ("NE", "LAC", 1.5, -102, -118, 35.5, -109, -110, "2026-11-29T21:05:00Z", False),
    ("WSH", "ARI", 6.5, -118, -102, 41.5, -111, -108, "2026-11-29T21:25:00Z", False),
    ("SEA", "SF", -2.5, -101, -119, 44.5, -109, -110, "2026-11-29T21:25:00Z", False),
    ("LV", "CLE", -4.5, -114, -105, 40.5, -103, -117, "2026-11-30T01:20:00Z", False),
]


# ---------- NHL de hoy: totales ----------
# (partidos, goles a favor, goles en contra)  ESPN standings (hasta el 25 nov)
NHL_EQUIPOS = {
    "BOS": ("Bruins", 23, 83, 61), "BUF": ("Sabres", 24, 73, 83), "DET": ("Red Wings", 23, 60, 71),
    "FLA": ("Panthers", 24, 76, 71), "MTL": ("Canadiens", 25, 78, 73), "OTT": ("Senators", 25, 81, 71),
    "TB": ("Lightning", 23, 84, 68), "TOR": ("Maple Leafs", 26, 82, 92), "CAR": ("Hurricanes", 24, 100, 55),
    "CBJ": ("Blue Jackets", 22, 56, 71), "NJ": ("Devils", 24, 91, 75), "NYI": ("Islanders", 23, 73, 67),
    "NYR": ("Rangers", 23, 69, 63), "PHI": ("Flyers", 26, 67, 88), "PIT": ("Penguins", 23, 67, 81),
    "WSH": ("Capitals", 21, 72, 83), "CHI": ("Blackhawks", 24, 64, 96), "COL": ("Avalanche", 23, 90, 68),
    "DAL": ("Stars", 23, 65, 56), "MIN": ("Wild", 26, 95, 58), "NSH": ("Predators", 23, 71, 69),
    "STL": ("Blues", 24, 82, 77), "UTA": ("Mammoth", 25, 82, 85), "WPG": ("Jets", 25, 79, 84),
    "ANA": ("Ducks", 25, 89, 95), "CGY": ("Flames", 25, 61, 86), "EDM": ("Oilers", 27, 104, 82),
    "LA": ("Kings", 22, 60, 71), "SJ": ("Sharks", 26, 71, 94), "SEA": ("Kraken", 21, 70, 73),
    "VAN": ("Canucks", 26, 74, 114), "VGK": ("Golden Knights", 26, 90, 78),
}

# visitante, local, linea, over, under, hora UTC
# Viernes 27 nov: 15 partidos, pero solo Maple Leafs @ Bruins tiene casa con los dos lados (bet365 via Covers)
NHL_PARTIDOS = [
    ("TOR", "BOS", 6.5, -123, 103, "2026-11-27T18:00:00Z"),
]


# ---------- Futbol (27 al 30 nov): totales ----------
# Equipo: (partidos, goles a favor, goles en contra)  Tablas: soccernews.com (26 nov)
# Momios: DraftKings en ESPN. local, visitante, linea, over, under, hora UTC
# Solo entran partidos con los dos lados claros (sin un segundo precio distinto en la pagina)
EPL_EQUIPOS = {
    "Arsenal": (11, 17, 7), "Brighton": (11, 26, 9), "Man City": (11, 22, 14), "Liverpool": (11, 18, 10),
    "Bournemouth": (11, 18, 14), "Brentford": (11, 20, 11), "Leeds": (11, 14, 9), "Chelsea": (11, 20, 20),
    "Everton": (11, 12, 14), "Tottenham": (11, 12, 11), "Hull City": (11, 13, 11), "Aston Villa": (11, 14, 17),
    "Newcastle": (11, 15, 18), "Coventry": (11, 13, 21), "Fulham": (11, 11, 13), "Ipswich": (11, 15, 22),
    "Nottm Forest": (11, 9, 15), "Sunderland": (11, 8, 17), "Man United": (11, 14, 23), "Crystal Palace": (11, 12, 27),
}
EPL_PARTIDOS = [
    ("Arsenal", "Man City", 2.5, -140, 110, "2026-11-29T16:30:00Z"),
    ("Sunderland", "Tottenham", 2.5, -105, -125, "2026-11-29T14:05:00Z"),
]

LALIGA_EQUIPOS = {
    "Barcelona": (13, 51, 15), "Real Madrid": (13, 33, 11), "Atletico Madrid": (13, 26, 10), "Real Betis": (13, 21, 16),
    "Real Sociedad": (13, 23, 23), "Sevilla": (13, 18, 20), "Racing Santander": (13, 20, 32), "Athletic Club": (12, 15, 12),
    "Alaves": (13, 18, 18), "Villarreal": (13, 19, 18), "Espanyol": (13, 14, 14), "Deportivo La Coruna": (13, 16, 17),
    "Osasuna": (13, 13, 23), "Celta": (13, 11, 12), "Levante": (13, 17, 22), "Rayo Vallecano": (12, 15, 22),
    "Valencia": (13, 9, 20), "Getafe": (13, 8, 21), "Elche": (13, 15, 21), "Malaga": (13, 9, 24),
}
LALIGA_PARTIDOS = [
    ("Real Sociedad", "Sevilla", 2.5, -130, 100, "2026-11-29T20:00:00Z"),
]
# Serie A y Bundesliga: no se encontraron momios con los dos lados claros. Liga MX: liguilla sin momios encontrados.


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
    "nfl_NE_LAC": [ajuste("Under", 0.02, "Patriots sin Drake Maye (QB, fuera la semana 12): juega Tommy DeVito"),
                   ajuste("Chargers", 0.01, "Patriots sin su QB titular Drake Maye")],
    "nfl_BAL_HOU": [ajuste("Under", 0.01, "Ravens sin Lamar Jackson (pulgar): juega Jacoby Brissett"),
                    ajuste("Texans", 0.01, "Ravens sin su QB titular Lamar Jackson")],
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
    "Premier League": (EPL_EQUIPOS, EPL_PARTIDOS, "epl", "soccer_epl", "DraftKings"),
    "LaLiga": (LALIGA_EQUIPOS, LALIGA_PARTIDOS, "laliga", "soccer_spain_la_liga", "DraftKings"),
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


NOTA = ("Edicion del " + EDICION + " (Thanksgiving): NFL semana 12 completa de jueves a domingo (14 partidos, spread y total), "
        "Maple Leafs @ Bruins en NHL y futbol del fin de semana (Arsenal-City y Sunderland-Tottenham en Premier, "
        "Real Sociedad-Sevilla en LaLiga). Hoy no hay NBA y los props del viernes todavia no salian. "
        "Contexto: Patriots sin Drake Maye y Ravens sin Lamar Jackson. Lineas NFL de DraftKings del 24 nov: revisa tu casa antes de apostar. "
        "Solo se publica con 55% o mas, 3% o mas de ventaja y nivel A o B.")

FUENTES = [
    ["VegasInsider - momios NFL por casa (DraftKings)", "https://www.vegasinsider.com/nfl/odds/las-vegas/"],
    ["VegasInsider - semana 12 NFL", "https://www.vegasinsider.com/nfl/nfl-week-12-odds-2026/"],
    ["ESPN - tabla NFL", "https://www.espn.com/nfl/standings/_/sort/wins"],
    ["NBC Sports - reporte de lesiones semana 12 (Drake Maye)", "https://www.nbcsports.com/fantasy/football/news/nfl-week-12-injury-report-drake-mayes-updated-timeline-dalton-kincaid-returns-to-practice-and-more"],
    ["SI - Patriots semana 12", "https://www.si.com/nfl/patriots/onsi/patriots-week-12-injury-report-potential-battle-of-the-backup-qbs"],
    ["Blitz Sports - lesiones semana 12", "https://blitzsportsmedia.com/week-12-injury-report-herbert-purdy-playing/"],
    ["Covers - Maple Leafs @ Bruins", "https://www.covers.com/sport/hockey/nhl/matchup/382676/picks"],
    ["ESPN - tabla NHL", "https://www.espn.com/nhl/standings/_/view"],
    ["Daily Faceoff - calendario NHL 27 nov", "https://www.dailyfaceoff.com/nhl-daily-schedule/2026-11-27"],
    ["ESPN - Arsenal vs Man City momios", "https://www.espn.com/soccer/odds/_/gameId/401878753"],
    ["ESPN - Sunderland vs Tottenham momios", "https://www.espn.com/soccer/odds/_/gameId/401879224"],
    ["ESPN - Real Sociedad vs Sevilla momios", "https://www.espn.com/soccer/odds/_/gameId/401882788"],
    ["Soccernews - tabla Premier League", "https://www.soccernews.com/soccer-stats/english-premier-league/league-table/2026-27/"],
    ["Soccernews - tabla LaLiga", "https://www.soccernews.com/soccer-stats/la-liga/league-table/2026-27/"],
]

if __name__ == "__main__":
    main()
