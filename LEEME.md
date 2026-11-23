# PickLab

Pagina de picks de apuestas basada en numeros. Se publica en GitHub Pages: https://moygcc-collab.github.io/picklab/

## Como funciona
1. **Momios (automatico, diario 5:10 am Monterrey):** el workflow `jalar_momios` corre `jalar_momios.py` con The Odds API y baja spreads, totales y props de todas las ligas activas (ver `config.py`): NFL, NCAA futbol americano, NBA, NCAA basquetbol, Euroliga, NHL, MLB, Premier, LaLiga, Serie A, Bundesliga, Ligue 1, Champions, Europa League, Liga MX, UFC y tenis ATP/WTA. Tambien baja los marcadores de los ultimos 3 dias para calificar solo los spreads y totales. Despues corre `edicion.py` y publica la pagina.
2. **Estadisticas y contexto (lunes y jueves):** las ediciones programadas juntan a mano lo que la API no trae: ultimos 10 partidos de jugadores, tablas de puntos/goles a favor y en contra, lesiones, descanso y ultimo enfrentamiento. Todo va en `edicion.py`.
3. **Motor (`motor.py`):** decide cada pick.

## El motor
Cada pick pasa por 4 senales:
- **Mercado:** probabilidad sin comision (consenso si hay varias casas) y el mejor precio disponible.
- **Estadisticas:** props = veces que el jugador paso la linea en sus ultimos 10, suavizado (9 de 10 cuenta como 75%) y pesa hasta 40%; spreads/totales = modelo con lo que anota y recibe cada equipo (pesa hasta 40%).
- **Contexto:** ajustes chicos (descanso, lesiones, racha, ultimo enfrentamiento del ultimo ano) con tope de 5 puntos.
- **Historial:** con 30+ picks calificados (mira los ultimos 60), si pegamos menos de lo esperado el motor baja su confianza solo.
- **Tope por partido:** maximo 2 picks del mismo partido, porque estan conectados (si el partido sale bajo, fallan juntos).

Salen: probabilidad, ventaja, **score de confianza 0-100** (probabilidad 35%, ventaja 25%, senales que coinciden 25%, calidad de datos 15%), **nivel A (70+) o B (55-69)**, razones a favor y en contra, y unidades (Kelly/16, entre 0.5u y 2u).
Solo se publica si: probabilidad >= 55%, ventaja >= 3% y nivel A o B.

## Configurar la API (una sola vez)
1. Compra el plan 20K de https://the-odds-api.com (30 USD/mes). Te llega la llave por correo (32 caracteres).
2. En GitHub: **Settings -> Secrets and variables -> Actions -> ODDS_API_KEY -> Update** y pega la llave.
3. **Actions -> jalar_momios -> Run workflow** para la primera corrida.
Cada corrida gasta unos 250 creditos (el plan trae 20,000 al mes).

## Archivos
- `edicion.py`: datos manuales, contexto y armado de la edicion. `python edicion.py` escribe `web/picks.js`.
- `motor.py`: el algoritmo. `api_picks.py`: convierte los momios de la API en candidatos.
- `jalar_momios.py` + `config.py`: descarga de momios y ligas.
- `historial.py` + `resultados.py` + `historial.json`: record de todos los picks.

## Si algo falla (Actions -> la corrida en rojo)
- `401 INVALID_KEY`: la llave de The Odds API esta mal en el secreto.
- `429` o creditos en 0: se acabaron los creditos del mes.

## Historial de resultados (record de la pagina)
Cada vez que corres `python edicion.py`, los picks se guardan solos en `historial.json`.
Para calificarlos despues de los partidos:
1. Corre `python historial.py`: te imprime las claves de los picks que ya se jugaron.
2. Pega cada clave en `resultados.py` con `"G"` (gano), `"P"` (perdio) o `"E"` (empate/push).
3. Vuelve a correr `python historial.py`. Eso actualiza `web/historial.js` y la pagina muestra record, % de acierto, unidades, ROI, grafica y resultados por deporte.
4. Haz commit y push.

## Ultimo enfrentamiento (head to head)
En `edicion.py` hay dos listas:
- `ULTIMO_DUELO`: por partido (la clave es el `evento` del pick, ej. `"cha_lal"` o `"nfl_LV_DEN"`): fecha, liga, marcador `[[visitante, puntos], [local, puntos]]`, detalle, partidos anteriores y fuente.
- `ULTIMO_DUELO_JUGADOR`: por jugador: su ultimo partido contra el rival de hoy (pts, reb, ast, tri, min).
Al correr `python edicion.py` se calcula solo si el pick de hoy hubiera pegado en ese partido y la pagina lo muestra en cada pick. Es informacion extra: no cambia la probabilidad del modelo.

## Props de jugadores y "Baja la linea" (Draftea)
- En `edicion.py` van `PROPS_NBA` y `PROPS_NFL` (yardas por pase, por tierra, por recepcion, recepciones). Se puede poner el momio de varias casas con la misma linea: el motor usa el consenso sin comision y el mejor precio.
- **Baja la linea:** para cada prop, `motor.escalera()` calcula que tan seguro es bajar la linea (Over) o subirla (Under): mercado de la linea principal movido con la dispersion de sus ultimos partidos + cuantas veces la paso. Como no hay momio real de esa linea, la pagina NO lo cuenta como pick: solo muestra el **momio minimo** que tiene que pagar tu casa para que tenga valor (3% de ventaja).
- **Draftea:** si ves una linea alterna con su momio, pegala en `DRAFTEA` como `["Jalen Brunson", "Puntos", "Over", 22.5, -250]`. El motor la evalua con las mismas reglas (55%, 3% de ventaja, nivel A o B) y, si pasa, sale como pick con casa Draftea y entra al historial.

## Ajuste del 23 nov (despues de 19-26)
Los props esperaban 63% y pegaron 40%: las rachas de 10 partidos pesaban demasiado contra el mercado. Cambios en `motor.py`:
PESO_MAX_PROPS 0.6 -> 0.4, PRIOR_PROPS 1 -> 3 (mas suavizado), PESO_MAX_EQUIPOS 0.5 -> 0.4, TOPE_POR_PARTIDO = 2 y calibracion con los ultimos 60 picks.
Las reglas para publicar (55%, 3% de ventaja, nivel A o B) no cambiaron.
