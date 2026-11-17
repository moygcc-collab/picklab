# PickLab

Página de picks de apuestas basada en estadísticas. Se actualiza sola con GitHub Actions y se publica gratis en GitHub Pages.

## Qué hace cada corrida
1. `jalar_momios.py`: revisa qué ligas están en temporada (gratis) y jala spreads y totales de NFL, NBA, NHL, MLB, Liga MX, Premier, LaLiga, Champions, UFC y los torneos de tenis ATP/WTA activos. También jala props de NBA, NFL y NHL (The Odds API).
2. `jalar_stats.py`: saca los últimos partidos de los jugadores de NBA que tienen props (API-Sports).
3. `calcular_picks.py`: calcula la probabilidad y la ventaja de cada pick, los ordena y escribe `web/picks.js`.

## Configurar GitHub (una sola vez)
1. **Settings → Secrets and variables → Actions → New repository secret**:
   - `ODDS_API_KEY` = tu llave de the-odds-api.com
   - `API_SPORTS_KEY` = tu llave de dashboard.api-football.com
2. **Settings → Pages → Source: GitHub Actions**.
3. **Actions → picks_automaticos → Run workflow** para la primera corrida.

Tu página queda en `https://TU_USUARIO.github.io/picklab/`.

## Cuándo se actualiza
Cada 3 días a las 9:00 am de Monterrey, y cuando le das **Run workflow**.
Cada corrida gasta unos 40–50 créditos de The Odds API. El plan gratis trae 500 al mes, así que no alcanza para diario. Si subes al plan de $30 USD (20,000 créditos), cambia en `.github/workflows/picks.yml` la línea del cron a `"0 15 * * *"` para que sea diario.

## Ajustes en config.py
- `LIGAS`: qué ligas revisar.
- `PROPS`: cuántos partidos y qué props revisar por deporte (menos partidos = menos créditos).
- `TEMPORADA_NBA`: 2026 = temporada 2026-27.

## Probar en tu compu sin llaves
```
pip install requests
python datos_prueba.py
python calcular_picks.py
```
Abre `web/index.html`.

## Cómo se calcula cada pick
- **Props de NBA:** 60% = cuántas veces el jugador pasó la línea en sus últimos 10 partidos. 40% = probabilidad justa por consenso de casas, sin comisión.
- **Props de NFL y NHL, spreads y totales:** probabilidad justa por consenso de casas, sin comisión, comparada contra el mejor momio disponible.
- Solo se muestran picks con ventaja positiva, ordenados de más a menos probable.

## Si algo falla (pestaña Actions → la corrida en rojo)
- `ERROR 401` → la llave de The Odds API está mal en los secretos.
- `ERROR 429` o créditos en 0 → se acabaron los créditos del mes.
- `ERROR: ... plan ...` en estadísticas → tu plan gratis de API-Sports no incluye la temporada actual. Los picks de líneas siguen saliendo; solo faltan las gráficas de jugadores.

## Historial de resultados (record de la pagina)
Cada vez que corres `python edicion.py`, los picks se guardan solos en `historial.json`.
Para calificarlos despues de los partidos:
1. Corre `python historial.py`: te imprime las claves de los picks que ya se jugaron.
2. Pega cada clave en `resultados.py` con `"G"` (gano), `"P"` (perdio) o `"E"` (empate/push).
3. Vuelve a correr `python historial.py`. Eso actualiza `web/historial.js` y la pagina muestra record, % de acierto, unidades, ROI, grafica y resultados por deporte.
4. Haz commit y push.
