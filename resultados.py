# ============================================
# RESULTADOS DE LOS PICKS
# Despues de que se jueguen los partidos:
#  1. Corre: python historial.py   (te imprime las claves pendientes)
#  2. Pega aqui cada clave con su resultado:
#       "G" = gano    "P" = perdio    "E" = empate / push (se devuelve la apuesta)
#  3. Vuelve a correr: python historial.py   (actualiza la pagina)
#
# Ejemplo:
#   "2026-11-18 | Hornets @ Lakers | Luka Doncic Over 4.5": "G",
# ============================================

RESULTADOS = {
    # Martes 17 nov (box scores: CBS Sports y PlainTextSports)
    "2026-11-18 | Hornets @ Lakers | Luka Doncic Over 4.5": "G",        # 5 triples
    "2026-11-18 | Hornets @ Lakers | Coby White Under 3.5": "P",        # 4 asistencias
    "2026-11-18 | Hornets @ Lakers | Quentin Grimes Under 12.5": "P",   # 47 puntos
    "2026-11-18 | Pistons @ Spurs | Victor Wembanyama Over 31.5": "P",  # 25 pts + 4 ast = 29
    "2026-11-18 | Knicks @ Raptors | Jalen Brunson Over 2.5": "G",      # 4 triples
    "2026-11-18 | Knicks @ Raptors | Karl-Anthony Towns Over 12.5": "G",  # 16 rebotes
    "2026-11-18 | Knicks @ Raptors | Scottie Barnes Over 34.5": "P",    # 20+4+2 = 26
    "2026-11-18 | Knicks @ Raptors | RJ Barrett Over 19.5": "G",        # 22 puntos
}
