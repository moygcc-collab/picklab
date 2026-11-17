# ============================================
# PASO 3: Calcular los picks
# Lee los archivos de la carpeta datos/
# Guarda: web/picks.js (lo que lee la pagina)
# ============================================

import json
import os
import unicodedata
from datetime import datetime
import config

NOMBRE_MERCADO = {
    "spreads": "Spread",
    "totals": "Total",
    "player_points": "Puntos",
    "player_rebounds": "Rebotes",
    "player_assists": "Asistencias",
    "player_pass_yds": "Yardas por pase",
    "player_rush_yds": "Yardas por tierra",
    "player_reception_yds": "Yardas por recepcion",
    "player_shots_on_goal": "Tiros a gol",
}

CAMPO_STAT = {
    "player_points": "puntos",
    "player_rebounds": "rebotes",
    "player_assists": "asistencias",
}


# ---------- Funciones de momios ----------

def prob_implicita(momio):
    # Probabilidad que te da la casa con su momio (incluye su comision)
    if momio > 0:
        return 100 / (momio + 100)
    return -momio / (-momio + 100)


def a_decimal(momio):
    if momio > 0:
        return 1 + momio / 100
    return 1 + 100 / (-momio)


def a_americano(decimal):
    if decimal >= 2:
        return round((decimal - 1) * 100)
    return round(-100 / (decimal - 1))


# ---------- Funciones de ayuda ----------

def limpiar_nombre(nombre):
    # "Luka Doncic Jr." y "luka doncic" quedan igual
    nombre = unicodedata.normalize("NFKD", nombre)
    nombre = nombre.encode("ascii", "ignore").decode("ascii")
    nombre = nombre.lower().replace(".", "").replace("'", "")
    for final in [" jr", " sr", " iii", " ii"]:
        if nombre.endswith(final):
            nombre = nombre[: -len(final)]
    return nombre.strip()


def mas_comun(lista):
    conteo = {}
    for valor in lista:
        conteo[valor] = conteo.get(valor, 0) + 1
    mejor = None
    for valor in conteo:
        if mejor is None or conteo[valor] > conteo[mejor]:
            mejor = valor
    return mejor


def leer(nombre_archivo, si_no_existe):
    ruta = "datos/" + nombre_archivo
    if not os.path.exists(ruta):
        print("No existe", ruta)
        return si_no_existe
    with open(ruta, encoding="utf-8") as archivo:
        return json.load(archivo)


# ---------- Analizar un mercado juntando todas las casas ----------

def analizar_mercado(evento, clave_mercado, jugador=None):
    # 1. Juntamos las dos opciones que da cada casa
    por_casa = []
    for casa in evento.get("bookmakers", []):
        for mercado in casa["markets"]:
            if mercado["key"] != clave_mercado:
                continue
            opciones = []
            for opcion in mercado["outcomes"]:
                if jugador is None or opcion.get("description") == jugador:
                    opciones.append(opcion)
            if len(opciones) == 2:
                opciones.sort(key=lambda o: o["name"])
                por_casa.append({"casa": casa["title"], "opciones": opciones})

    # Necesitamos al menos 2 casas para comparar
    if len(por_casa) < 2:
        return []

    # 2. La linea que mas casas tienen (linea de consenso)
    lineas = []
    for c in por_casa:
        lineas.append(c["opciones"][0].get("point"))
    linea_consenso = mas_comun(lineas)

    # 3. Probabilidad justa (sin comision) y mejor momio de cada opcion
    resultado = {}
    for c in por_casa:
        if c["opciones"][0].get("point") != linea_consenso:
            continue
        p1 = prob_implicita(c["opciones"][0]["price"])
        p2 = prob_implicita(c["opciones"][1]["price"])
        for i in [0, 1]:
            opcion = c["opciones"][i]
            justa = [p1, p2][i] / (p1 + p2)
            nombre = opcion["name"]
            if nombre not in resultado:
                resultado[nombre] = {
                    "nombre": nombre,
                    "punto": opcion.get("point"),
                    "suma_justa": 0,
                    "casas": 0,
                    "mejor_momio": opcion["price"],
                    "mejor_casa": c["casa"],
                }
            r = resultado[nombre]
            r["suma_justa"] += justa
            r["casas"] += 1
            if opcion["price"] > r["mejor_momio"]:
                r["mejor_momio"] = opcion["price"]
                r["mejor_casa"] = c["casa"]

    lista = []
    for nombre in resultado:
        r = resultado[nombre]
        r["prob_justa"] = r["suma_justa"] / r["casas"]
        lista.append(r)
    return lista


def nombre_partido(evento, clave):
    if clave.startswith("soccer"):
        return evento["home_team"] + " vs " + evento["away_team"]
    return evento["away_team"] + " @ " + evento["home_team"]


def texto_punto(punto):
    # 3.0 -> "3", -3.5 -> "-3.5"
    if punto == int(punto):
        return str(int(punto))
    return str(punto)


# ---------- Picks de spreads y totales ----------

def picks_de_lineas(lineas, ligas):
    picks = []
    partidos = 0
    for clave in lineas:
        for evento in lineas[clave]:
            partidos += 1
            for mercado in ["spreads", "totals"]:
                opciones = analizar_mercado(evento, mercado)
                mejor = None
                for op in opciones:
                    op["ventaja"] = op["prob_justa"] - prob_implicita(op["mejor_momio"])
                    if mejor is None or op["ventaja"] > mejor["ventaja"]:
                        mejor = op
                if mejor is None or mejor["ventaja"] <= 0:
                    continue

                if mercado == "spreads":
                    punto = mejor["punto"]
                    signo = "+" if punto > 0 else ""
                    texto = mejor["nombre"] + " " + signo + texto_punto(punto)
                    tipo = "Spreads"
                else:
                    texto = mejor["nombre"] + " " + texto_punto(mejor["punto"])
                    tipo = "Totales"

                picks.append({
                    "evento": evento["id"],
                    "grupo": ligas[clave]["grupo"],
                    "liga": ligas[clave]["liga"],
                    "partido": nombre_partido(evento, clave),
                    "fecha": evento["commence_time"],
                    "tipo": tipo,
                    "mercado": NOMBRE_MERCADO[mercado],
                    "pick": texto,
                    "momio": mejor["mejor_momio"],
                    "casa": mejor["mejor_casa"],
                    "casas": mejor["casas"],
                    "prob": mejor["prob_justa"],
                    "ventaja": mejor["ventaja"],
                    "base": "Consenso de " + str(mejor["casas"]) + " casas sin comision",
                })
    return picks, partidos


# ---------- Picks de props con estadisticas ----------

def picks_de_props(props, stats, ligas):
    # Buscador de jugadores NBA por nombre limpio
    buscador = {}
    for nombre in stats:
        buscador[limpiar_nombre(nombre)] = stats[nombre]

    picks = []
    for clave in props:
        if clave not in ligas:
            continue
        for evento in props[clave]:
            for mercado in config.PROPS[clave]["mercados"]:
                # Jugadores que tienen este mercado
                jugadores = []
                for casa in evento.get("bookmakers", []):
                    for m in casa["markets"]:
                        if m["key"] == mercado:
                            for o in m["outcomes"]:
                                if o.get("description") and o["description"] not in jugadores:
                                    jugadores.append(o["description"])

                for jugador in jugadores:
                    # Solo NBA tiene estadisticas de API-Sports por ahora
                    valores = []
                    datos = None
                    if clave == "basketball_nba" and mercado in CAMPO_STAT:
                        datos = buscador.get(limpiar_nombre(jugador))
                        if datos is None:
                            continue
                        for partido in datos["partidos"]:
                            valores.append(partido[CAMPO_STAT[mercado]])
                        valores = valores[-config.ULTIMOS_PARTIDOS:]
                        if len(valores) < 5:
                            continue

                    mejor = None
                    for op in analizar_mercado(evento, mercado, jugador):
                        punto = op["punto"]
                        if valores:
                            aciertos = 0
                            for v in valores:
                                if op["nombre"] == "Over" and v > punto:
                                    aciertos += 1
                                if op["nombre"] == "Under" and v < punto:
                                    aciertos += 1
                            # 60% lo que dicen sus numeros, 40% lo que dice el mercado
                            op["prob"] = 0.6 * aciertos / len(valores) + 0.4 * op["prob_justa"]
                            op["aciertos"] = aciertos
                        else:
                            # Sin estadisticas: solo consenso de casas
                            op["prob"] = op["prob_justa"]
                        op["ventaja"] = op["prob"] - prob_implicita(op["mejor_momio"])
                        if mejor is None or op["ventaja"] > mejor["ventaja"]:
                            mejor = op
                    if mejor is None or mejor["ventaja"] <= 0:
                        continue

                    pick = {
                        "evento": evento["id"],
                        "grupo": ligas[clave]["grupo"],
                        "liga": ligas[clave]["liga"],
                        "partido": evento["away_team"] + " @ " + evento["home_team"],
                        "fecha": evento["commence_time"],
                        "tipo": "Props",
                        "mercado": NOMBRE_MERCADO.get(mercado, mercado),
                        "jugador": jugador,
                        "equipo": "",
                        "pick": jugador + " " + mejor["nombre"] + " " + texto_punto(mejor["punto"]),
                        "lado": mejor["nombre"],
                        "linea": mejor["punto"],
                        "momio": mejor["mejor_momio"],
                        "casa": mejor["mejor_casa"],
                        "casas": mejor["casas"],
                        "prob": mejor["prob"],
                        "ventaja": mejor["ventaja"],
                        "base": "Consenso de " + str(mejor["casas"]) + " casas sin comision",
                    }
                    if valores:
                        ordenados = sorted(valores)
                        pick["equipo"] = datos["equipo"]
                        pick["valores"] = valores
                        pick["aciertos"] = mejor["aciertos"]
                        pick["promedio"] = round(sum(valores) / len(valores), 1)
                        pick["mediana"] = ordenados[len(ordenados) // 2]
                        pick["maximo"] = max(valores)
                        pick["minimo"] = min(valores)
                        pick["base"] = "Ultimos " + str(len(valores)) + " partidos + consenso de " + str(mejor["casas"]) + " casas"
                    picks.append(pick)
    return picks


# ---------- Juntar todo ----------

def main():
    ligas = leer("ligas.json", {})
    lineas = leer("lineas.json", {})
    props = leer("props.json", {})
    stats = leer("stats_nba.json", {})

    picks, partidos = picks_de_lineas(lineas, ligas)
    picks = picks + picks_de_props(props, stats, ligas)

    # Lo mas probable de pegar primero
    picks.sort(key=lambda p: p["prob"], reverse=True)

    for i in range(len(picks)):
        p = picks[i]
        p["id"] = i + 1
        p["prob"] = round(p["prob"] * 100, 1)
        p["ventaja"] = round(p["ventaja"] * 100, 1)
        p["implicita"] = round(prob_implicita(p["momio"]) * 100, 1)
        if i == 0:
            p["unidades"] = 2
        elif p["prob"] >= 60:
            p["unidades"] = 1
        else:
            p["unidades"] = 0.5

    # Parlay: los 3 mejores picks de partidos diferentes
    parlay = []
    eventos_usados = []
    for p in picks:
        if p["evento"] not in eventos_usados:
            parlay.append(p["id"])
            eventos_usados.append(p["evento"])
        if len(parlay) == 3:
            break
    decimal = 1
    prob_parlay = 1
    for p in picks:
        if p["id"] in parlay:
            decimal = decimal * a_decimal(p["momio"])
            prob_parlay = prob_parlay * p["prob"] / 100

    # Conteo por deporte
    grupos = {}
    for nombre in config.GRUPOS.values():
        grupos[nombre] = {"picks": 0, "partidos": 0, "ligas": []}
    for clave in ligas:
        grupo = ligas[clave]["grupo"]
        grupos[grupo]["partidos"] += len(lineas.get(clave, []))
        if ligas[clave]["liga"] not in grupos[grupo]["ligas"]:
            grupos[grupo]["ligas"].append(ligas[clave]["liga"])
    for p in picks:
        grupos[p["grupo"]]["picks"] += 1

    salida = {
        "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "prueba": os.path.exists("datos/es_prueba.txt"),
        "partidos_analizados": partidos,
        "picks": picks,
        "parlay": {
            "ids": parlay,
            "momio": a_americano(decimal) if len(parlay) > 0 else 0,
            "prob": round(prob_parlay * 100, 1),
        },
        "grupos": grupos,
    }

    with open("web/picks.js", "w", encoding="utf-8") as archivo:
        archivo.write("window.PICKS = ")
        archivo.write(json.dumps(salida, ensure_ascii=False, indent=1))
        archivo.write(";\n")
    print("Listo:", len(picks), "picks guardados en web/picks.js")


if __name__ == "__main__":
    main()
