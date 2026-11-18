# ============================================
# PICKS DESDE THE ODDS API
# Lee datos/ligas.json, datos/lineas.json y datos/props.json
# (los baja el workflow "jalar_momios" con la llave ODDS_API_KEY)
# y arma candidatos para el motor, con el mejor momio entre todas las casas.
#
# Si para un equipo o jugador hay estadisticas (las juntan las ediciones),
# se agrega el modelo; si no, el pick se basa solo en el mercado.
# ============================================

import json
import os
from datetime import datetime, timedelta, timezone
from calcular_picks import analizar_mercado
import motor

DIAS_ADELANTE = 5

# Nombre bonito de cada mercado de props
MERCADO_PROP = {
    "player_points": "Puntos", "player_rebounds": "Rebotes", "player_assists": "Asistencias",
    "player_threes": "Triples", "player_points_rebounds_assists": "Pts + Reb + Ast",
    "player_pass_yds": "Yardas por pase", "player_rush_yds": "Yardas por tierra",
    "player_reception_yds": "Yardas por recepcion", "player_receptions": "Recepciones",
    "player_shots_on_goal": "Tiros a gol",
}


def leer(nombre, si_no):
    ruta = "datos/" + nombre
    if not os.path.exists(ruta):
        return si_no
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


LIGAS = leer("ligas.json", {})
LINEAS = leer("lineas.json", {})
PROPS = leer("props.json", {})


def hay_api(clave):
    return len(LINEAS.get(clave) or []) > 0


def hay_props(clave):
    return len(PROPS.get(clave) or []) > 0


def en_ventana(iso):
    ahora = datetime.now(timezone.utc)
    t = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return ahora < t < ahora + timedelta(days=DIAS_ADELANTE)


def texto_linea(punto):
    return str(int(punto)) if punto == int(punto) else str(punto)


def partido_de(ev, clave):
    if clave.startswith("soccer"):
        return ev["home_team"] + " vs " + ev["away_team"]
    return ev["away_team"] + " @ " + ev["home_team"]


# ---------- Modelos por deporte (con estadisticas de la temporada) ----------

def modelo(grupo, liga, mercado, ev, op, tabla, alias):
    # Regresa (probabilidad, texto, muestra) o (None, None, 0)
    loc = motor.buscar_equipo(ev["home_team"], tabla, alias)
    vis = motor.buscar_equipo(ev["away_team"], tabla, alias)
    if loc is None or vis is None:
        return None, None, 0
    gl, fl, al = loc
    gv, fv, av = vis
    muestra = min(gl, gv)
    if grupo in ("NFL", "NBA"):
        casa = 1.5 if grupo == "NFL" else 2.0
        desv_total = 13.5 if grupo == "NFL" else 18
        desv_margen = 13.5 if grupo == "NFL" else 12
        pts_loc = (fl / gl + av / gv) / 2 + casa / 2
        pts_vis = (fv / gv + al / gl) / 2 - casa / 2
        if mercado == "totals":
            p_over = motor.normal_mayor(op["punto"], pts_loc + pts_vis, desv_total)
            p = p_over if op["nombre"] == "Over" else 1 - p_over
            return p, "Proyectamos " + str(round(pts_loc + pts_vis, 1)) + " puntos", muestra
        margen_loc = pts_loc - pts_vis
        if op["nombre"] == ev["home_team"]:
            p = motor.normal_mayor(-op["punto"], margen_loc, desv_margen)
        else:
            p = motor.normal_mayor(-op["punto"], -margen_loc, desv_margen)
        return p, "Proyectamos margen de " + str(round(margen_loc, 1)) + " para " + ev["home_team"], muestra
    if grupo in ("NHL", "Futbol") and mercado == "totals":
        if grupo == "Futbol":
            prom = sum(t[1] for t in tabla.values()) / max(1, sum(t[0] for t in tabla.values()))
            ataque_l = 0.5 + 0.5 * (fl / gl) / prom
            defensa_l = 0.5 + 0.5 * (al / gl) / prom
            ataque_v = 0.5 + 0.5 * (fv / gv) / prom
            defensa_v = 0.5 + 0.5 * (av / gv) / prom
            lam = prom * 1.1 * ataque_l * defensa_v + prom * 0.9 * ataque_v * defensa_l
        else:
            lam = (fl / gl + av / gv) / 2 + (fv / gv + al / gl) / 2
        p_over = motor.poisson_mayor(op["punto"], lam)
        p = p_over if op["nombre"] == "Over" else 1 - p_over
        return p, "Esperamos " + str(round(lam, 2)) + " goles", muestra
    return None, None, 0


# ---------- Candidatos de spreads y totales ----------

def candidatos_lineas(estadisticas, alias, contexto):
    salida = []
    analizados = {}
    for clave, eventos in LINEAS.items():
        info = LIGAS.get(clave)
        if not info:
            continue
        tabla = estadisticas.get(clave, {})
        for ev in eventos or []:
            if not en_ventana(ev["commence_time"]):
                continue
            analizados[info["grupo"]] = analizados.get(info["grupo"], 0) + 1
            for mercado in ["spreads", "totals"]:
                mejor = None
                for op in analizar_mercado(ev, mercado):
                    if op["punto"] is None:
                        continue
                    if mercado == "totals":
                        texto = op["nombre"] + " " + texto_linea(op["punto"])
                    else:
                        texto = op["nombre"] + " " + ("+" if op["punto"] > 0 else "") + texto_linea(op["punto"])
                    c = {
                        "evento": ev["id"], "api_id": ev["id"], "liga_clave": clave,
                        "grupo": info["grupo"], "liga": info["liga"], "partido": partido_de(ev, clave),
                        "fecha": ev["commence_time"], "local": ev["home_team"], "visitante": ev["away_team"],
                        "tipo": "Totales" if mercado == "totals" else "Spreads",
                        "mercado": "Total" if mercado == "totals" else "Spread",
                        "pick": texto, "linea_num": op["punto"],
                        "momio": op["mejor_momio"], "casa": op["mejor_casa"], "casas": op["casas"],
                        "p_mercado": op["prob_justa"], "dos_lados": True,
                        "ajustes": contexto.get(ev["id"], []) + contexto.get(partido_de(ev, clave), []),
                    }
                    if mercado == "totals":
                        c["lado"] = op["nombre"]
                    else:
                        c["equipo_pick"] = op["nombre"]
                        c["rival_pick"] = ev["away_team"] if op["nombre"] == ev["home_team"] else ev["home_team"]
                    p, texto_m, muestra = modelo(info["grupo"], info["liga"], mercado, ev, op, tabla, alias)
                    if p is not None:
                        c["p_modelo"] = p
                        c["peso_modelo"] = motor.PESO_MAX_EQUIPOS * min(1, muestra / 8)
                        c["modelo_texto"] = texto_m
                        c["muestra"] = muestra
                    motor.evaluar(c)
                    if mejor is None or c["ventaja"] > mejor["ventaja"]:
                        mejor = c
                if mejor is not None:
                    salida.append(mejor)
    return salida, analizados


# ---------- Candidatos de props ----------

def candidatos_props(ultimos, contexto):
    # ultimos: {"Jugador": {"player_points": [10 valores del mas viejo al mas nuevo], ...}}
    salida = []
    for clave, eventos in PROPS.items():
        info = LIGAS.get(clave)
        if not info:
            continue
        for ev in eventos or []:
            if not en_ventana(ev["commence_time"]):
                continue
            jugadores = {}
            for casa in ev.get("bookmakers", []):
                for m in casa["markets"]:
                    for o in m["outcomes"]:
                        if o.get("description"):
                            jugadores.setdefault((o["description"], m["key"]), True)
            for jugador, mercado in jugadores:
                mejor = None
                for op in analizar_mercado(ev, mercado, jugador):
                    c = {
                        "evento": ev["id"], "api_id": ev["id"], "liga_clave": clave,
                        "grupo": info["grupo"], "liga": info["liga"], "partido": partido_de(ev, clave),
                        "fecha": ev["commence_time"], "tipo": "Props",
                        "mercado": MERCADO_PROP.get(mercado, mercado), "jugador": jugador, "equipo": "",
                        "pick": jugador + " " + op["nombre"] + " " + texto_linea(op["punto"]),
                        "lado": op["nombre"], "linea": op["punto"],
                        "momio": op["mejor_momio"], "casa": op["mejor_casa"], "casas": op["casas"],
                        "p_mercado": op["prob_justa"], "dos_lados": True,
                        "ajustes": contexto.get(jugador, []),
                    }
                    valores = (ultimos.get(jugador) or {}).get(mercado)
                    if valores:
                        c["valores"] = valores
                    motor.evaluar(c)
                    if mejor is None or c["ventaja"] > mejor["ventaja"]:
                        mejor = c
                # Sin estadisticas del jugador no publicamos props (solo mercado es muy poco)
                if mejor is not None and mejor.get("valores"):
                    salida.append(mejor)
    return salida
