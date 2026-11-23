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
    # Miercoles 18 nov (ESPN, Land of Basketball, CBS Sports, Bleacher Report)
    "2026-11-19 | Bulls @ Nets | Julius Randle Under 22.5": "G",        # 17 puntos
    "2026-11-19 | Hawks @ Thunder | Shai Gilgeous-Alexander Under 5.5": "G",  # 3 asistencias
    "2026-11-19 | Jazz @ Lakers | Luka Doncic Over 36.5": "P",          # 29 puntos
    # Jueves 19 nov (ESPN, CBS Sports, NBA.com, AP, Yahoo)
    "2026-11-20 | Clippers @ Spurs | Stephon Castle Under 17.5": "P",          # 21 puntos
    "2026-11-20 | Knicks @ Timberwolves | Ayo Dosunmu Over 17.5": "P",         # 6 puntos
    "2026-11-20 | Knicks @ Timberwolves | Jalen Brunson Over 26.5": "P",       # 21 puntos
    "2026-11-20 | Knicks @ Timberwolves | Karl-Anthony Towns Over 12.5": "P",  # 12 rebotes
    "2026-11-20 | Knicks @ Timberwolves | LaMelo Ball Over 18.5": "P",         # 15 puntos
    "2026-11-20 | Colts @ Texans | Colts +12.5": "P",                          # Texans 26 - 3
    "2026-11-20 | Colts @ Texans | Jonathan Taylor Over 49.5": "P",            # 21 yardas
    "2026-11-20 | Colts @ Texans | Over 44.5": "P",                            # 29 puntos
    # Viernes 20 y sabado 21 nov (ESPN, NBA.com, CBS Sports, SI, Yahoo, beIN)
    "2026-11-21 | Pacers @ Cavaliers | Pascal Siakam Under 6.5": "P",          # 7 rebotes
    "2026-11-21 | Wizards @ Bulls | Josh Giddey Under 13.5": "G",              # 2 puntos
    "2026-11-21 | Wizards @ Bulls | Trae Young Under 9.5": "G",                # 5 asistencias
    "2026-11-21 | Rockets @ Nuggets | Jamal Murray Over 22.5": "P",            # 14 puntos
    "2026-11-21 | Rockets @ Nuggets | Kevin Durant Over 20.5": "P",            # 16 puntos
    "2026-11-20 | Bayern vs Koln | Under 4.5": "G",                            # 1-1
    "2026-11-21 | Schalke vs Stuttgart | Under 3.5": "G",                      # 0-0
    "2026-11-21 | Newcastle vs Arsenal | Under 2.5": "P",                      # 2-2
    # Sabado 21 nov (CBS Sports, NBA.com, ESPN, FOX Sports, realmadrid.com, Flashscore)
    "2026-11-21 | Real Madrid vs Celta | Under 3.5": "G",                      # 2-1
    "2026-11-22 | Trail Blazers @ Knicks | Donovan Clingan Over 10.5": "G",    # 13 rebotes
    "2026-11-22 | Trail Blazers @ Knicks | Josh Hart Under 6.5": "P",          # 8 rebotes
    "2026-11-22 | Clippers @ Mavericks | Daniel Gafford Under 6.5": "P",       # 10 rebotes
    "2026-11-22 | Pelicans @ Spurs | Keldon Johnson Under 11.5": "G",          # 10 puntos
    "2026-11-22 | Pelicans @ Spurs | Zion Williamson Over 20.5": "E",          # no jugo (golpe en el muslo)
    "2026-11-22 | Celtics @ Kings | Domantas Sabonis Over 11.5": "G",          # 17 rebotes
    # NFL semana 11, domingo 22 nov (ESPN, CBS Sports, Yahoo, sitios oficiales)
    "2026-11-22 | Cardinals @ Chiefs | Cardinals +16.5": "P",                  # Chiefs 34 - 7
    "2026-11-22 | Cardinals @ Chiefs | Over 41.5": "P",                        # 41 puntos
    "2026-11-22 | Cardinals @ Chiefs | Trey McBride Over 48.5": "G",           # 54 yardas
    "2026-11-22 | Dolphins @ Bills | Dolphins +16.5": "P",                     # Bills 26 - 9
    "2026-11-22 | Ravens @ Panthers | Over 43.5": "G",                         # Panthers 35 - 33
    "2026-11-22 | Saints @ Bears | Saints +11.5": "G",                         # Bears 21 - 13
    "2026-11-22 | Titans @ Cowboys | Under 54.5": "P",                         # Cowboys 51 - 30
    "2026-11-22 | Jets @ Chargers | Jets +3.5": "G",                           # Jets 27 - 24
    "2026-11-22 | Jaguars @ Giants | Cam Skattebo Over 54.5": "P",             # 34 yardas
    "2026-11-22 | Raiders @ Broncos | Over 40.5": "G",                         # Broncos 38 - 24
    "2026-11-22 | Raiders @ Broncos | Raiders +10": "P",                       # perdieron por 14
    "2026-11-23 | Vikings @ 49ers (Estadio Banorte, CDMX) | Justin Jefferson Under 82.5": "P",  # 86 yardas
}

# ============================================
# MOMIOS DE CIERRE (opcional): el momio justo antes de que empiece el partido,
# del mismo lado y la misma linea del pick. Sirve para saber si le ganamos al mercado:
# si seguido conseguimos mejor precio que el cierre, el modelo va bien aunque una semana salga mala.
#   "2026-11-24 | Bengals @ Commanders | Under 52.5": -120,
# (Si corres edicion.py otra vez antes del partido, el ultimo momio se guarda solo.)
# ============================================
CIERRE = {
}
