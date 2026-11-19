# ============================================
# MOTOR DE PICKLAB
# Decide la probabilidad de cada pick y POR QUE.
#
# Cada pick pasa por 4 senales:
#  1. Mercado: lo que dicen las casas sin su comision (si hay varias, el consenso).
#  2. Estadisticas: ultimos partidos del jugador o el modelo de la temporada del equipo.
#  3. Contexto: descanso, lesiones, ultimo enfrentamiento, racha (ajustes chicos y con tope).
#  4. Historial: si nuestros picks pasados acertaron menos de lo esperado, bajamos la confianza.
#
# Resultado de cada pick:
#  - prob: probabilidad final
#  - ventaja: prob menos lo que implica el momio
#  - score (0-100) y nivel (A o B): que tan solido es el pick
#  - razones: lista de motivos a favor (+), en contra (-) e informativos (i)
#  - unidades: tamano de la apuesta (Kelly / 16, entre 0.5u y 2u)
#
# Solo se publica si: prob >= 55%, ventaja >= 3% y nivel A o B.
# ============================================

import json
import math
import os
from datetime import datetime
from calcular_picks import prob_implicita, a_decimal

PROB_MINIMA = 0.55
VENTAJA_MINIMA = 0.03
TOPE_CONTEXTO = 0.05      # el contexto mueve como maximo 5 puntos de probabilidad
PESO_MAX_PROPS = 0.6      # peso maximo de los ultimos partidos en props
PESO_MAX_EQUIPOS = 0.5    # peso maximo del modelo de temporada en spreads/totales
MINIMO_CALIBRAR = 30      # picks calificados necesarios para ajustar por historial


def limitar(x, a, b):
    return max(a, min(b, x))


def pct(x):
    return str(round(x * 100, 1)) + "%"


def momio_txt(m):
    return "+" + str(m) if m > 0 else str(m)


# ---------- Modelos de probabilidad ----------

def normal_mayor(x, media, desv):
    # Probabilidad de que un valor normal sea mayor que x
    return 0.5 * (1 - math.erf((x - media) / (desv * math.sqrt(2))))


def poisson_mayor(linea, lam):
    # Probabilidad de que un conteo (goles) sea mayor que la linea
    suma = 0
    for k in range(int(math.floor(linea)) + 1):
        suma += math.exp(-lam) * lam ** k / math.factorial(k)
    return 1 - suma


def sin_comision(momio_a, momio_b):
    pa = prob_implicita(momio_a)
    pb = prob_implicita(momio_b)
    return pa / (pa + pb), pb / (pa + pb)


# ---------- Calibracion con el historial ----------

_calibracion = None


def calibracion():
    # Si los picks pasados pegaron menos de lo que el modelo esperaba,
    # encogemos las probabilidades hacia 50%. Nunca las inflamos.
    global _calibracion
    if _calibracion is not None:
        return _calibracion
    _calibracion = {"factor": 1.0, "picks": 0, "esperado": None, "real": None}
    if not os.path.exists("historial.json"):
        return _calibracion
    with open("historial.json", encoding="utf-8") as f:
        lista = json.load(f)
    hechos = [h for h in lista if h.get("resultado") in ("G", "P")]
    _calibracion["picks"] = len(hechos)
    if not hechos:
        return _calibracion
    esperado = sum(h["prob"] / 100 for h in hechos) / len(hechos)
    real = len([h for h in hechos if h["resultado"] == "G"]) / len(hechos)
    _calibracion["esperado"] = round(esperado * 100, 1)
    _calibracion["real"] = round(real * 100, 1)
    if len(hechos) >= MINIMO_CALIBRAR and esperado > 0.5:
        _calibracion["factor"] = round(limitar((real - 0.5) / (esperado - 0.5), 0.5, 1.0), 2)
    return _calibracion


# ---------- Contexto ----------

def lado_de(c):
    # "Over", "Under" o el nombre del equipo del pick
    if c.get("lado") in ("Over", "Under"):
        return c["lado"]
    return c.get("equipo_pick")


def aplicar_ajustes(c):
    # Cada ajuste dice a quien ayuda ("Over", "Under" o un equipo) y cuanto.
    # Si ayuda al lado contrario del pick, resta.
    total = 0
    razones = []
    lado = lado_de(c)
    contrario = {"Over": "Under", "Under": "Over"}.get(lado, c.get("rival_pick"))
    for a in c.get("ajustes", []):
        if a["efecto"] == lado:
            d = a["delta"]
        elif a["efecto"] == contrario:
            d = -a["delta"]
        else:
            continue
        total += d
        razones.append(("+" if d > 0 else "-", a["texto"]))
    total = limitar(total, -TOPE_CONTEXTO, TOPE_CONTEXTO)
    return total, razones


def ajuste_duelo(c):
    # Ultimo enfrentamiento: solo cuenta (poquito) si fue en el ultimo ano
    d = c.get("duelo")
    if not d or d.get("pego") is None:
        return 0, []
    fecha = (d.get("jugador") or {}).get("fecha") or d.get("fecha")
    reciente = False
    if fecha:
        dias = (datetime.now() - datetime.strptime(fecha, "%Y-%m-%d")).days
        reciente = dias <= 365
    texto = "Ultimo enfrentamiento: " + d.get("resumen", "")
    if not reciente:
        return 0, [("i", texto + " (hace mas de un ano, no cuenta)")]
    if d["pego"]:
        return 0.01, [("+", texto + ": hubiera pegado")]
    return -0.01, [("-", texto + ": no hubiera pegado")]


# ---------- Evaluar un pick ----------

def evaluar(c):
    # c trae: momio, casa, casas, p_mercado, dos_lados, y opcionalmente
    # p_modelo + peso_modelo + modelo_texto, valores + linea + lado (props), ajustes, duelo
    razones = []
    senales = []   # True si la senal apoya el pick

    # 1. Mercado
    pm = c["p_mercado"]
    if c.get("mercado_texto"):
        razones.append(("+" if pm >= 0.5 else "-", c["mercado_texto"]))
    elif c.get("casas", 1) >= 2:
        razones.append(("+" if pm >= 0.5 else "-", str(c["casas"]) + " casas en consenso: " + pct(pm) + " sin su comision"))
    elif c.get("dos_lados"):
        razones.append(("+" if pm >= 0.5 else "-", c["casa"] + " le da " + pct(pm) + " ya sin su comision"))
    else:
        razones.append(("i", "Solo encontramos este lado del momio en " + c["casa"] + "; usamos su probabilidad con comision (" + pct(pm) + "), que es mas conservador"))
    senales.append(pm >= 0.5)

    # 2. Estadisticas
    pe = c.get("p_modelo")
    peso = c.get("peso_modelo", 0)
    valores = c.get("valores")
    if valores:
        n = len(valores)
        if c["lado"] == "Over":
            aciertos = len([v for v in valores if v > c["linea"]])
        else:
            aciertos = len([v for v in valores if v < c["linea"]])
        # Laplace: 9 de 10 cuenta como 83%, no 90% (muestra chica)
        pe = (aciertos + 1) / (n + 2)
        peso = PESO_MAX_PROPS * min(1, n / 10)
        c["aciertos"] = aciertos
        prom = sum(valores) / n
        razones.append(("+" if aciertos / n >= 0.6 else ("-" if aciertos / n < 0.5 else "i"),
                        "Le pego al " + c["lado"] + " " + str(c["linea"]) + " en " + str(aciertos) + " de sus ultimos " + str(n)))
        margen = prom - c["linea"] if c["lado"] == "Over" else c["linea"] - prom
        razones.append(("+" if margen > 0 else "-", "Promedia " + str(round(prom, 1)) + " contra la linea de " + str(c["linea"])))
        if n >= 10:
            ultimos5 = valores[-5:]
            a5 = len([v for v in ultimos5 if (v > c["linea"] if c["lado"] == "Over" else v < c["linea"])])
            if a5 >= 4:
                razones.append(("+", "En racha: " + str(a5) + " de 5 en sus ultimos 5"))
            elif a5 <= 1:
                razones.append(("-", "Viene frio: " + str(a5) + " de 5 en sus ultimos 5"))
            senales.append(a5 >= 3)
        if n < 8:
            razones.append(("-", "Muestra chica: solo " + str(n) + " partidos"))
    elif pe is not None:
        razones.append(("+" if pe >= 0.5 else "-", "Modelo de la temporada: le da " + pct(pe) + " a este pick (" +
                        c.get("modelo_texto", "") + ")"))
    if pe is not None:
        senales.append(pe >= 0.5)
        if (pe >= 0.5) != (pm >= 0.5):
            razones.append(("-", "Las estadisticas y el mercado no coinciden"))
        p = peso * pe + (1 - peso) * pm
    else:
        p = pm

    # 3. Contexto
    d_ctx, r_ctx = aplicar_ajustes(c)
    d_duelo, r_duelo = ajuste_duelo(c)
    razones += r_ctx + r_duelo
    if r_ctx:
        senales.append(d_ctx >= 0)
    if d_duelo != 0:
        senales.append(d_duelo > 0)
    p = p + limitar(d_ctx + d_duelo, -TOPE_CONTEXTO, TOPE_CONTEXTO)

    # 4. Historial
    cal = calibracion()
    if cal["factor"] < 1:
        p = 0.5 + (p - 0.5) * cal["factor"]
        razones.append(("i", "Ajuste por historial: nuestros picks pegaron " + str(cal["real"]) + "% contra " +
                        str(cal["esperado"]) + "% esperado, asi que bajamos la confianza"))
    p = limitar(p, 0.01, 0.97)

    implicita = prob_implicita(c["momio"])
    ventaja = p - implicita
    razones.append(("+" if ventaja > 0 else "-", "El momio " + momio_txt(c["momio"]) + " implica " + pct(implicita) +
                    "; nosotros calculamos " + pct(p) + " (ventaja " + ("+" if ventaja > 0 else "") + pct(ventaja) + ")"))

    # Score de confianza (0-100)
    c1 = limitar((p - 0.5) / 0.25, 0, 1)                    # que tan probable
    c2 = limitar(ventaja / 0.10, 0, 1)                      # cuanto valor
    c3 = len([s for s in senales if s]) / len(senales)      # cuantas senales coinciden
    calidad = [min(c.get("casas", 1), 6) / 6, 1.0 if c.get("dos_lados") or c.get("casas", 1) >= 2 else 0.5]
    if valores:
        calidad.append(min(len(valores), 10) / 10)
    elif pe is not None:
        calidad.append(min(c.get("muestra", 10), 10) / 10)
    else:
        calidad.append(0.3)
    c4 = sum(calidad) / len(calidad)
    score = round(100 * (0.35 * c1 + 0.25 * c2 + 0.25 * c3 + 0.15 * c4))
    nivel = "A" if score >= 70 else ("B" if score >= 55 else "C")

    # Unidades: Kelly / 16 (1u = 1% del banco), entre 0.5u y 2u. Prudente porque el modelo es nuevo
    b = a_decimal(c["momio"]) - 1
    kelly = (b * p - (1 - p)) / b
    unidades = limitar(round(kelly * 100 / 16 * 2) / 2, 0.5, 2) if kelly > 0 else 0

    c["prob"] = p
    c["ventaja"] = ventaja
    c["score"] = score
    c["nivel"] = nivel
    c["senales"] = str(len([s for s in senales if s])) + "/" + str(len(senales))
    c["unidades"] = unidades
    c["razones"] = [{"tipo": t, "texto": x} for t, x in razones]
    c["publicar"] = p >= PROB_MINIMA and ventaja >= VENTAJA_MINIMA and nivel != "C"
    if pe is not None:
        c["p_estadisticas"] = round(pe * 100, 1)
    c["p_mercado_pct"] = round(pm * 100, 1)
    return c


# ---------- Lineas alternas (bajar o subir la linea) ----------
# Casas como Draftea dejan elegir otra linea del mismo jugador (ej. Over 20.5 en vez de 26.5).
# La probabilidad de la linea alterna sale de:
#  - el mercado de la linea principal (sin comision), movido con una curva normal
#    que usa la dispersion de los ultimos partidos del jugador, y
#  - las veces que el jugador paso esa linea alterna en sus ultimos partidos.
# Sin momio real de la linea alterna no es pick: solo decimos el momio minimo para que tenga valor.

PASO_LINEA = {"Puntos": 2, "Rebotes": 1, "Asistencias": 1, "Triples": 1, "Pts + Reb + Ast": 3,
              "Puntos + Asistencias": 2, "Puntos + Rebotes": 2, "Recepciones": 1,
              "Yardas por pase": 15, "Yardas por tierra": 10, "Yardas por recepcion": 10}

ESCALERA_MIN = 0.65   # solo mostramos lineas alternas con 65% o mas
ESCALERA_MAX = 0.93   # arriba de esto el momio ya no vale la pena


def inversa_normal(p):
    # Busqueda binaria: z tal que la normal estandar acumulada da p
    a, b = -6.0, 6.0
    for _ in range(80):
        m = (a + b) / 2
        if 0.5 * (1 + math.erf(m / math.sqrt(2))) < p:
            a = m
        else:
            b = m
    return (a + b) / 2


def desviacion(valores, linea):
    n = len(valores)
    prom = sum(valores) / n
    var = sum((v - prom) ** 2 for v in valores) / max(1, n - 1)
    # Piso: al menos 15% de la linea (muestras chicas engañan)
    return max(math.sqrt(var), 0.15 * linea, 0.8)


def mercado_en_linea(c, nueva):
    # Probabilidad del mercado movida a otra linea, del mismo lado que c["lado"]
    s = desviacion(c["valores"], c["linea"])
    p_over = c["p_mercado"] if c["lado"] == "Over" else 1 - c["p_mercado"]
    p_over = limitar(p_over, 0.03, 0.97)
    media = c["linea"] + s * inversa_normal(p_over)   # la media que implica el mercado
    p = normal_mayor(nueva, media, s)
    return p if c["lado"] == "Over" else 1 - p


def americano_de_prob(p):
    if p >= 0.5:
        return -int(round(100 * p / (1 - p)))
    return int(round(100 * (1 - p) / p))


def alterna(c, nueva, momio=None, casa=None):
    # Arma y evalua un candidato con otra linea del mismo jugador
    alt = dict(c)
    for k in ["razones", "duelo", "aciertos", "prob", "ventaja", "score", "nivel", "publicar"]:
        alt.pop(k, None)
    alt["linea"] = nueva
    alt["pick"] = c["jugador"] + " " + c["lado"] + " " + str(nueva)
    alt["p_mercado"] = mercado_en_linea(c, nueva)
    alt["mercado_texto"] = ("Mercado estimado: la linea principal (" + str(c["linea"]) + ") movida a " + str(nueva) +
                            " con la dispersion de sus ultimos partidos da " + pct(alt["p_mercado"]))
    alt["casas"] = 1
    alt["dos_lados"] = False
    alt["linea_principal"] = c["linea"]
    alt["momio"] = momio if momio is not None else -110
    if casa:
        alt["casa"] = casa
    return evaluar(alt)


def escalera(c):
    # Lineas mas faciles: Over -> bajar la linea; Under -> subirla
    paso = PASO_LINEA.get(c.get("mercado"))
    if not paso or not c.get("valores"):
        return []
    salida = []
    signo = -1 if c["lado"] == "Over" else 1
    for k in range(1, 5):
        nueva = c["linea"] + signo * k * paso
        if nueva <= 0:
            break
        a = alterna(c, nueva)
        p = a["prob"]
        if p > ESCALERA_MAX:
            break
        if p >= ESCALERA_MIN:
            salida.append({"linea": nueva, "pick": a["pick"], "prob": round(p * 100, 1),
                           "aciertos": a["aciertos"], "partidos": len(c["valores"]),
                           "momio_minimo": americano_de_prob(p - VENTAJA_MINIMA)})
    return salida


# ---------- Ayuda para comparar nombres de equipos ----------

def buscar_equipo(nombre, tabla, alias=None):
    # Busca "Kansas City Chiefs" en una tabla que usa "Chiefs" o "KC"
    alias = alias or {}
    if nombre in tabla:
        return tabla[nombre]
    nombre_l = nombre.lower()
    for clave, valor in tabla.items():
        corto = alias.get(clave, clave).lower()
        if corto == nombre_l or nombre_l.endswith(" " + corto) or corto in nombre_l:
            return valor
    return None
