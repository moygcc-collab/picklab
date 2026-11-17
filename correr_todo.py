# ============================================
# Corre los 3 pasos en orden
# Uso: python correr_todo.py
# ============================================

import json
import os
import jalar_momios
import jalar_stats
import calcular_picks

os.makedirs("datos", exist_ok=True)

# Si habia datos de prueba, ya no
if os.path.exists("datos/es_prueba.txt"):
    os.remove("datos/es_prueba.txt")

print("===== PASO 1: momios =====")
try:
    jalar_momios.main()
except Exception as error:
    print("Fallo el paso 1:", error)
    with open("datos/errores_momios.json", "w", encoding="utf-8") as archivo:
        json.dump(["Paso 1 (momios): " + str(error)], archivo)

print("===== PASO 2: estadisticas =====")
try:
    jalar_stats.main()
except Exception as error:
    print("Fallo el paso 2:", error)
    with open("datos/errores_stats.json", "w", encoding="utf-8") as archivo:
        json.dump(["Paso 2 (estadisticas): " + str(error)], archivo)

print("===== PASO 3: picks =====")
calcular_picks.main()

print("Abre web/index.html para ver la pagina")
