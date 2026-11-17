# ============================================
# Picks con datos REALES juntados a mano (martes 17 nov 2026)
# Lineas: DraftKings Network, FanDuel Research, Steezanomics
# Partidos de cada jugador: ESPN game logs
# Uso: python datos_reales.py  -> escribe web/picks.js
# ============================================

import json
from datetime import datetime
from calcular_picks import prob_implicita, a_decimal, a_americano

# Horarios en UTC (Monterrey = UTC-6)
KNICKS_RAPTORS = ("nyk_tor", "Knicks @ Raptors", "2026-11-18T00:30:00Z")
PISTONS_SPURS = ("det_sas", "Pistons @ Spurs", "2026-11-18T01:00:00Z")
HORNETS_LAKERS = ("cha_lal", "Hornets @ Lakers", "2026-11-18T04:00:00Z")

# Cada prop: jugador, equipo, partido, mercado, linea,
# momio over, momio under (None si la fuente solo dio un lado), casa, fuente,
# valores de sus ultimos partidos (del mas viejo al mas nuevo)
PROPS = [
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


def evaluar(lado, linea, momio, prob_mercado, valores):
    aciertos = 0
    for v in valores:
        if lado == "Over" and v > linea:
            aciertos += 1
        if lado == "Under" and v < linea:
            aciertos += 1
    hit_rate = aciertos / len(valores)
    prob = 0.6 * hit_rate + 0.4 * prob_mercado
    return {"lado": lado, "momio": momio, "aciertos": aciertos, "prob": prob,
            "ventaja": prob - prob_implicita(momio), "mercado_prob": prob_mercado}


picks = []
descartados = []
for jugador, equipo, partido, mercado, linea, over, under, casa, fuente, valores in PROPS:
    opciones = []
    if over is not None and under is not None:
        # Las dos caras: quitamos la comision de la casa
        p_over = prob_implicita(over)
        p_under = prob_implicita(under)
        opciones.append(evaluar("Over", linea, over, p_over / (p_over + p_under), valores))
        opciones.append(evaluar("Under", linea, under, p_under / (p_over + p_under), valores))
        base = "Ultimos " + str(len(valores)) + " partidos + momio sin comision"
    else:
        # Solo un lado: usamos la probabilidad del momio tal cual (mas conservador)
        lado = "Over" if over is not None else "Under"
        momio = over if over is not None else under
        opciones.append(evaluar(lado, linea, momio, prob_implicita(momio), valores))
        base = "Ultimos " + str(len(valores)) + " partidos + momio de la casa"

    mejor = max(opciones, key=lambda o: o["ventaja"])
    ordenados = sorted(valores)
    pick = {
        "evento": partido[0],
        "grupo": "NBA",
        "liga": "NBA",
        "partido": partido[1],
        "fecha": partido[2],
        "tipo": "Props",
        "mercado": mercado,
        "jugador": jugador,
        "equipo": equipo,
        "pick": jugador + " " + mejor["lado"] + " " + str(linea),
        "lado": mejor["lado"],
        "linea": linea,
        "momio": mejor["momio"],
        "casa": casa,
        "casas": 1,
        "prob": mejor["prob"],
        "ventaja": mejor["ventaja"],
        "valores": valores,
        "aciertos": mejor["aciertos"],
        "promedio": round(sum(valores) / len(valores), 1),
        "mediana": ordenados[len(ordenados) // 2],
        "maximo": max(valores),
        "minimo": min(valores),
        "base": base + ". Linea via " + fuente + ", partidos via ESPN",
    }
    if mejor["ventaja"] > 0:
        picks.append(pick)
    else:
        descartados.append(pick["pick"])

picks.sort(key=lambda p: p["prob"], reverse=True)
for i in range(len(picks)):
    p = picks[i]
    p["id"] = i + 1
    p["prob"] = round(p["prob"] * 100, 1)
    p["ventaja"] = round(p["ventaja"] * 100, 1)
    p["implicita"] = round(prob_implicita(p["momio"]) * 100, 1)
    p["unidades"] = 2 if i == 0 else (1 if p["prob"] >= 60 else 0.5)

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

grupos = {
    "NFL": {"picks": 0, "partidos": 0, "ligas": ["NFL"]},
    "NBA": {"picks": len(picks), "partidos": 5, "ligas": ["NBA"]},
    "Futbol": {"picks": 0, "partidos": 0, "ligas": ["Liga MX", "Premier League", "LaLiga", "Champions"]},
    "MLB": {"picks": 0, "partidos": 0, "ligas": ["MLB"]},
    "NHL": {"picks": 0, "partidos": 0, "ligas": ["NHL"]},
    "UFC": {"picks": 0, "partidos": 0, "ligas": ["UFC"]},
}

salida = {
    "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "prueba": False,
    "manual": True,
    "nota": "Edicion del martes 17 de noviembre: props de NBA de esta noche con lineas y estadisticas reales. Los demas deportes llegan con la version automatica.",
    "fuentes": [
        ["DraftKings Network - NBA betting trends 17 nov", "https://dknetwork.draftkings.com/2026/11/17/nba-public-betting-trends-tuesday-november-17"],
        ["FanDuel Research - NBA props 17 nov", "https://www.fanduel.com/research/nba-props-today-player-prop-bets-tuesday-nov-17"],
        ["Steezanomics - Knicks vs Raptors props", "https://steezanomics.com/picks/knicks-vs-raptors-player-props-november-17-2026/"],
        ["Steezanomics - Hornets vs Lakers props", "https://steezanomics.com/picks/hornets-vs-lakers-player-props-november-17-2026/"],
        ["Steezanomics - rebounds props", "https://steezanomics.com/picks/best-rebounds-props-tuesday-november-17-2026/"],
        ["ESPN - game logs de cada jugador", "https://www.espn.com/nba/"],
        ["StatMuse - horarios del 17 nov", "https://www.statmuse.com/nba/ask/play"],
    ],
    "partidos_analizados": 5,
    "props_analizados": len(PROPS),
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
    print(p["id"], p["pick"], p["mercado"], p["momio"], "prob", p["prob"], "ventaja", p["ventaja"], "hits", p["aciertos"], "/", len(p["valores"]))
print("Descartados:", descartados)
print("Parlay:", parlay, salida["parlay"])
