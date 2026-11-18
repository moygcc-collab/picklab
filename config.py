# ============================================
# CONFIGURACION DE PICKLAB
# ============================================

import os

# La llave se lee del secreto de GitHub ODDS_API_KEY.
# Si lo corres en tu compu, puedes pegarla aqui en lugar del texto PEGA_AQUI.
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "PEGA_AQUI_TU_LLAVE_DE_THE_ODDS_API")
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "PEGA_AQUI_TU_LLAVE_DE_API_SPORTS")

# Grupos de The Odds API -> deporte en la pagina
GRUPOS = {
    "American Football": "NFL",
    "Basketball": "NBA",
    "Ice Hockey": "NHL",
    "Baseball": "MLB",
    "Soccer": "Futbol",
    "Mixed Martial Arts": "UFC",
    "Tennis": "Tenis",
}

# Ligas que revisamos: clave de The Odds API -> (deporte en la pagina, nombre, regiones de casas)
# Regiones: "us" = casas de EU (DraftKings, FanDuel, BetMGM...), "eu" = casas europeas.
# Cada liga cuesta: 2 mercados x numero de regiones (ej. "us,eu" = 4 creditos)
LIGAS = {
    "americanfootball_nfl": ("NFL", "NFL", "us"),
    "americanfootball_ncaaf": ("NFL", "NCAA Futbol Americano", "us"),
    "basketball_nba": ("NBA", "NBA", "us"),
    "basketball_ncaab": ("NBA", "NCAA Basquetbol", "us"),
    "basketball_euroleague": ("NBA", "Euroliga", "eu"),
    "icehockey_nhl": ("NHL", "NHL", "us"),
    "baseball_mlb": ("MLB", "MLB", "us"),
    "soccer_epl": ("Futbol", "Premier League", "us,eu"),
    "soccer_spain_la_liga": ("Futbol", "LaLiga", "us,eu"),
    "soccer_italy_serie_a": ("Futbol", "Serie A", "us,eu"),
    "soccer_germany_bundesliga": ("Futbol", "Bundesliga", "us,eu"),
    "soccer_france_ligue_one": ("Futbol", "Ligue 1", "us,eu"),
    "soccer_uefa_champs_league": ("Futbol", "Champions League", "us,eu"),
    "soccer_uefa_europa_league": ("Futbol", "Europa League", "us,eu"),
    "soccer_mexico_ligamx": ("Futbol", "Liga MX", "us,eu"),
    "mma_mixed_martial_arts": ("UFC", "UFC / MMA", "us"),
}
# Tenis: cualquier torneo ATP o WTA activo se agrega solo (tennis_atp_... y tennis_wta_...)
REGION_TENIS = "us,eu"

# Mercados de lineas (sin moneyline: preferimos spreads y totales)
MERCADOS = "spreads,totals"

# Props: cuantos partidos de los proximos dias y que mercados. 1 credito por mercado por partido.
PROPS = {
    "basketball_nba": {"partidos": 12, "horas": 30,
                       "mercados": ["player_points", "player_rebounds", "player_assists", "player_threes",
                                    "player_points_rebounds_assists"]},
    "americanfootball_nfl": {"partidos": 16, "horas": 100,
                             "mercados": ["player_pass_yds", "player_rush_yds", "player_reception_yds", "player_receptions"]},
    "icehockey_nhl": {"partidos": 8, "horas": 30, "mercados": ["player_shots_on_goal", "player_points"]},
}

# Cuantos dias hacia adelante nos interesan los partidos
DIAS_ADELANTE = 5

# Temporada NBA en API-Sports (2026 = temporada 2026-27)
TEMPORADA_NBA = 2026

# Cuantos partidos para atras revisamos de cada jugador
ULTIMOS_PARTIDOS = 10
