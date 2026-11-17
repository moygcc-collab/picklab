# ============================================
# Corre los 3 pasos en orden
# Uso: python correr_todo.py
# ============================================

import os

os.makedirs("datos", exist_ok=True)
import jalar_momios
import jalar_stats
import calcular_picks

# Si habia datos de prueba, ya no
if os.path.exists("datos/es_prueba.txt"):
    os.remove("datos/es_prueba.txt")

print("===== PASO 1: momios =====")
jalar_momios.main()

print("===== PASO 2: estadisticas =====")
jalar_stats.main()

print("===== PASO 3: picks =====")
calcular_picks.main()

print("Abre web/index.html para ver la pagina")
