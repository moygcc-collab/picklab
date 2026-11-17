# ============================================
# CONFIGURACION DE PICKLAB
# ============================================

import os

# Las llaves se leen de los secretos de GitHub.
# Si lo corres en tu compu, puedes pegarlas aqui en lugar del texto PEGA_AQUI.
ODDS_API_KEY = os.environ.get("ODDS_API_KEY", "PEGA_AQUI_TU_LLAVE_DE_THE_ODDS_API")
API_SPORTS_KEY = os.environ.get("API_SPORTS_KEY", "PEGA_AQUI_TU_LLAVE_DE_API_SPORTS")

# Grupos de The Odds API -> nombre en la pagina
# Cualquier liga activa de estos grupos se revisa sola
GRUPOS = {
    "American Football": "NFL",
    "Basketball": "NBA",
    "Ice Hockey": "NHL",
    "Baseball": "MLB",
    "Soccer": "Futbol",
    "Mixed Martial Arts": "UFC",
    "Tennis": "Tenis",
}

# Ligas que si queremos (para no gastar creditos en ligas raras)
# Tenis se agrega solo: cualquier torneo ATP o WTA activo
LIGAS = {
    "americanfootball_nfl": "NFL",
    "basketball_nba": "NBA",
    "icehockey_nhl": "NHL",
    "baseball_mlb": "MLB",
    "soccer_mexico_ligamx": "Liga MX",
    "soccer_epl": "Premier League",
    "soccer_spain_la_liga": "LaLiga",
    "soccer_uefa_champs_league": "Champions",
    "mma_mixed_martial_arts": "UFC",
}

# Region de casas de apuestas
REGION = "us"

# Props por deporte: cuantos partidos revisar y que mercados
# Cada partido gasta 1 credito por mercado
PROPS = {
    "basketball_nba": {"partidos": 4, "mercados": ["player_points", "player_rebounds", "player_assists"]},
    "americanfootball_nfl": {"partidos": 3, "mercados": ["player_pass_yds", "player_rush_yds", "player_reception_yds"]},
    "icehockey_nhl": {"partidos": 2, "mercados": ["player_shots_on_goal", "player_points"]},
}

# Temporada NBA en API-Sports (2025 = temporada 2025-26, 2026 = 2026-27)
TEMPORADA_NBA = 2026

# Cuantos partidos para atras revisamos de cada jugador
ULTIMOS_PARTIDOS = 10
