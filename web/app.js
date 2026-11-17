// ============================================
// PICKLAB - pinta la pagina con los datos de picks.js
// Rutas:  #  (inicio)   #deporte-NBA   #pick-5
// ============================================

var D = window.PICKS || { picks: [], grupos: {}, parlay: { ids: [] }, partidos_analizados: 0 };
var ORDEN_GRUPOS = ["NFL", "NBA", "Futbol", "MLB", "NHL", "UFC", "Tenis"];
var app = document.getElementById("app");

// Lo que el usuario eligio en filtros
var filtro = { liga: "Todas", tipo: "Todos" };

// ---------- Ayudas ----------

function esc(texto) {
  return String(texto).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function momio(m) {
  return m > 0 ? "+" + m : String(m);
}

function fecha(iso) {
  var d = new Date(iso);
  return d.toLocaleString("es-MX", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function barra(prob) {
  return '<div class="prob"><div class="barra"><div style="width:' + prob + '%"></div></div><span class="mono" style="font-size:13px">' + prob + "%</span></div>";
}

function buscarPick(id) {
  for (var i = 0; i < D.picks.length; i++) {
    if (D.picks[i].id === id) return D.picks[i];
  }
  return null;
}

function picksDe(grupo) {
  return D.picks.filter(function (p) { return p.grupo === grupo; });
}

// Un jugador por tarjeta, los que mas veces pasaron su linea
function jugadoresEnRacha(lista, cuantos) {
  var props = lista.filter(function (p) { return p.tipo === "Props" && p.valores; });
  props.sort(function (a, b) { return b.aciertos - a.aciertos || b.prob - a.prob; });
  var vistos = [];
  var salida = [];
  for (var i = 0; i < props.length && salida.length < cuantos; i++) {
    if (vistos.indexOf(props[i].jugador) === -1) {
      vistos.push(props[i].jugador);
      salida.push(props[i]);
    }
  }
  return salida;
}

function irA(id) {
  setTimeout(function () {
    var el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, 150);
}

// ---------- Piezas que se repiten ----------

function tiraDeportes(activo) {
  var html = '<a class="tab' + (activo === "" ? " activo" : "") + '" href="#" style="display:inline-flex;align-items:center">Inicio</a>';
  ORDEN_GRUPOS.forEach(function (g) {
    html += '<a class="tab' + (activo === g ? " activo" : "") + '" href="#deporte-' + g + '" style="display:inline-flex;align-items:center">' + g + "</a>";
  });
  document.getElementById("tira").innerHTML = html;
}

function chispa(p) {
  var maximo = Math.max.apply(null, p.valores.concat([p.linea])) || 1;
  var html = '<div class="chispa" aria-hidden="true">';
  p.valores.forEach(function (v) {
    var paso = p.lado === "Over" ? v > p.linea : v < p.linea;
    html += '<span style="height:' + Math.max(6, (v / maximo) * 100) + "%;background:" + (paso ? "#C6F432" : "#3A4655") + '"></span>';
  });
  return html + "</div>";
}

function tarjetaJugador(p) {
  return '<a class="tarjeta" href="#pick-' + p.id + '">' +
    '<span class="etiqueta">' + esc(p.grupo) + " - " + esc(p.mercado) + "</span>" +
    '<span><b style="font-family:Space Grotesk,sans-serif;font-size:18px">' + esc(p.jugador) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.equipo) + "</span></span>" +
    "<b>" + esc(p.lado) + " " + p.linea + " " + esc(p.mercado.toLowerCase()) + "</b>" +
    chispa(p) +
    '<span style="display:flex;justify-content:space-between;border-top:1px solid #1E2733;padding-top:12px">' +
    '<span class="mono" style="font-size:14px">' + p.aciertos + " de sus ultimos " + p.valores.length + "</span>" +
    '<span class="verde" style="font-weight:600;font-size:14px">Ver estadisticas &rarr;</span></span></a>';
}

function tarjetaPick(p) {
  return '<a class="tarjeta" href="#pick-' + p.id + '">' +
    '<span style="display:flex;justify-content:space-between;gap:8px"><span class="etiqueta">' + esc(p.tipo) + " - " + esc(p.liga) + '</span><span class="gris" style="font-size:13px">' + fecha(p.fecha) + "</span></span>" +
    '<span><span class="gris" style="font-size:14px">' + esc(p.partido) + '</span><br><b style="font-family:Space Grotesk,sans-serif;font-size:22px">' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.mercado) + " - " + esc(p.base) + "</span></span>" +
    barra(p.prob) +
    '<div class="pie_tarjeta"><div><b>' + momio(p.momio) + "</b>Momio</div><div><b>" + esc(p.casa) + "</b>Casa</div><div><b class=\"verde\">+" + p.ventaja + "%</b>Ventaja</div><div><b>" + p.unidades + "u</b>Unidades</div></div></a>";
}

// ---------- INICIO ----------

function pintarInicio() {
  tiraDeportes("");
  var html = "";

  if (D.prueba) {
    html += '<div class="aviso">Estas viendo DATOS DE PRUEBA. Pega tus llaves en config.py y corre: python correr_todo.py</div>';
  }

  if (D.errores && D.errores.length) {
    html += '<div class="aviso" style="background:#3A1A16;border-color:#7A2E24;color:#FFB4A8">Hubo errores al actualizar: ' + esc(D.errores.join(" | ")) + "</div>";
  }

  if (D.nota) {
    html += '<div class="aviso" style="background:#1A2410;border-color:#3A4F1B;color:#E2FF8A">' + esc(D.nota) + "</div>";
  }

  if (D.picks.length === 0) {
    app.innerHTML = html + '<div class="vacio">Todavia no hay picks. Corre: python correr_todo.py</div>';
    return;
  }

  var uno = D.picks[0];
  var top10 = D.picks.slice(0, 10);

  // Hero
  html += '<section><div style="display:flex;flex-direction:column;gap:10px;max-width:760px">' +
    '<span class="mono verde" style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase">Todos los deportes - Basado en datos</span>' +
    '<h1 style="font-size:clamp(36px,5vw,60px);line-height:1.05">Los picks con mas probabilidad de pegar esta semana.</h1>' +
    '<p class="gris" style="font-size:18px">Analizamos cada partido, filtramos lo que tiene ventaja estadistica y lo reducimos hasta el pick mas fuerte.</p></div>' +
    '<div class="fila"><a class="caja destacada grande" href="#pick-' + uno.id + '" style="color:inherit">' +
    '<span style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px"><span class="etiqueta verde_lleno">Pick #1 de la semana</span><span class="gris">' + esc(uno.liga) + " - " + fecha(uno.fecha) + "</span></span>" +
    '<span class="gris">' + esc(uno.partido) + "</span>" +
    '<h2 style="font-size:38px;line-height:1.1">' + esc(uno.pick) + "</h2>" +
    '<span class="mono">' + esc(uno.mercado) + " - Momio " + momio(uno.momio) + " en " + esc(uno.casa) + "</span>" +
    barra(uno.prob) +
    '<div class="mini_stats">' +
    (uno.valores
      ? '<div class="mini"><b>' + uno.aciertos + "/" + uno.valores.length + "</b><span>Veces que paso la linea</span></div>" +
        '<div class="mini"><b>' + uno.promedio + "</b><span>Promedio vs linea " + uno.linea + "</span></div>"
      : '<div class="mini"><b>' + uno.casas + "</b><span>Casas comparadas</span></div>") +
    '<div class="mini"><b class="verde">+' + uno.ventaja + '%</b><span>Ventaja vs el momio</span></div></div></a>' +
    '<div class="caja chica"><h3 style="font-size:22px">Como llegamos al pick</h3><p class="gris" style="font-size:14px">Del total de partidos al mas fuerte.</p>' +
    '<div class="embudo">' +
    '<div style="background:#1E2733"><span>Partidos analizados</span><b class="mono">' + D.partidos_analizados + "</b></div>" +
    '<div style="background:#26331F;width:86%"><span>Con ventaja</span><b class="mono">' + D.picks.length + "</b></div>" +
    '<div style="background:#3A4F1B;width:70%"><span>Top picks</span><b class="mono">' + top10.length + "</b></div>" +
    '<div style="background:#C6F432;color:#0B0F14;width:52%"><b>Pick #1</b><b class="mono">1</b></div></div></div></div></section>';

  // Deportes
  html += '<section id="deportes"><div class="titulo"><h2>Explora por deporte</h2><p>Picale a un deporte para ver todos sus picks.</p></div><div class="rejilla">';
  ORDEN_GRUPOS.forEach(function (g) {
    var info = D.grupos[g] || { picks: 0, partidos: 0, ligas: [] };
    var sin = info.partidos === 0;
    html += '<a class="tarjeta" href="#deporte-' + g + '" style="min-height:170px">' +
      '<span style="display:flex;justify-content:space-between;align-items:center"><b style="font-family:Space Grotesk,sans-serif;font-size:26px">' + g + "</b>" +
      '<span class="etiqueta' + (sin ? " amarilla" : "") + '">' + (sin ? (D.manual ? "Proximamente" : "Sin partidos") : info.partidos + " partidos") + "</span></span>" +
      '<span class="gris" style="font-size:13px">' + esc(info.ligas.join(" - ")) + "</span>" +
      '<span style="margin-top:auto;display:flex;justify-content:space-between;border-top:1px solid #1E2733;padding-top:12px"><span class="mono">' + info.picks + ' picks</span><span class="verde" style="font-weight:600">Ver picks &rarr;</span></span></a>';
  });
  html += "</div></section>";

  // Top 10
  html += '<section id="picks"><div class="titulo"><h2>Top 10 de la semana</h2><p>Ordenados por probabilidad. Solo picks con ventaja contra el momio.</p></div>' +
    '<div class="tabla_caja"><div class="tabla"><div class="renglon encabezado"><span>#</span><span>Deporte</span><span>Partido / pick</span><span>Momio</span><span>Unidades</span><span>Probabilidad</span><span>Ventaja</span></div>';
  top10.forEach(function (p, i) {
    html += '<a class="renglon" href="#pick-' + p.id + '"><span class="mono verde" style="font-weight:700;font-size:18px">' + (i + 1) + "</span>" +
      '<span class="etiqueta">' + esc(p.grupo) + "</span>" +
      '<span><b>' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.partido) + " - " + esc(p.mercado) + "</span></span>" +
      '<span class="mono">' + momio(p.momio) + '</span><span class="mono">' + p.unidades + "u</span>" + barra(p.prob) +
      '<span class="mono verde">+' + p.ventaja + "%</span></a>";
  });
  html += "</div></div></section>";

  // Jugadores en racha
  var racha = jugadoresEnRacha(D.picks, 4);
  if (racha.length > 0) {
    html += '<section id="tendencias"><div class="titulo"><h2>Jugadores en racha</h2><p>Los que mas veces pasaron su linea. Picale para ver su grafica.</p></div><div class="rejilla">';
    racha.forEach(function (p) { html += tarjetaJugador(p); });
    html += "</div></section>";
  }

  // Parlay
  if (D.parlay.ids.length > 1) {
    html += '<section id="parlay" style="flex-direction:row;flex-wrap:wrap"><div class="chica" style="display:flex;flex-direction:column;justify-content:center;gap:10px">' +
      '<h2 style="font-size:34px">Parlay sugerido</h2><p class="gris">Los picks mas probables de partidos diferentes. Menos piernas, mas chance de pegar.</p></div>' +
      '<div class="caja grande">';
    D.parlay.ids.forEach(function (id, i) {
      var p = buscarPick(id);
      html += '<a href="#pick-' + id + '" style="display:flex;align-items:center;gap:14px;padding:14px 16px;background:#0B0F14;border-radius:12px;color:inherit">' +
        '<span class="mono" style="width:32px;height:32px;border-radius:999px;background:#1E2733;display:flex;align-items:center;justify-content:center;flex:none">' + (i + 1) + "</span>" +
        '<span style="flex:1;min-width:0"><b>' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.grupo) + " - " + esc(p.partido) + '</span></span><span class="mono">' + momio(p.momio) + "</span></a>";
    });
    html += '<div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px"><div style="display:flex;gap:28px">' +
      '<div><span class="gris" style="font-size:13px">Momio combinado</span><br><b class="mono" style="font-size:24px">' + momio(D.parlay.momio) + "</b></div>" +
      '<div><span class="gris" style="font-size:13px">Probabilidad combinada</span><br><b class="mono verde" style="font-size:24px">' + D.parlay.prob + "%</b></div></div>" +
      '<a class="boton" href="#" id="ir_calc">Calcular mi pago</a></div></div></section>';
  }

  // Herramientas
  html += '<section id="herramientas"><div class="titulo"><h2>Herramientas</h2><p>Para que sepas cuanto ganas y cuanto arriesgas antes de apostar.</p></div><div class="fila">' +
    '<div class="caja chica" style="flex-basis:420px"><h3 style="font-size:22px">Calculadora de parlay</h3><div class="campos">' +
    '<label for="c_apuesta">Apuesta ($)<input id="c_apuesta" type="number" value="100"></label>' +
    '<label for="c_m1">Momio pierna 1<input id="c_m1" type="number" value="-110"></label>' +
    '<label for="c_m2">Momio pierna 2<input id="c_m2" type="number" value="-110"></label>' +
    '<label for="c_m3">Momio pierna 3 (opcional)<input id="c_m3" type="number" value=""></label></div>' +
    '<div class="mini_stats"><div class="mini"><b id="r_pago">-</b><span>Pago total</span></div><div class="mini"><b class="verde" id="r_ganancia">-</b><span>Ganancia</span></div><div class="mini"><b id="r_prob">-</b><span>Prob. implicita</span></div></div>' +
    '<span class="gris" style="font-size:12px">Momios americanos (ej. -110, +150).</span></div>' +
    '<div class="chica" style="flex-basis:420px;display:flex;flex-direction:column;gap:20px">' +
    '<div class="caja glosario"><h3 style="font-size:22px">Glosario rapido</h3>' +
    "<div><b>Spread</b><span>Ventaja en puntos. -3.5 significa que el equipo tiene que ganar por 4 o mas.</span></div>" +
    "<div><b>Over/Under</b><span>Si el total de puntos o goles queda arriba o abajo de la linea.</span></div>" +
    "<div><b>Prop</b><span>Apuesta sobre un jugador: puntos, rebotes, asistencias, etc.</span></div>" +
    "<div><b>Momio</b><span>-110: apuestas $110 para ganar $100. +150: apuestas $100 para ganar $150.</span></div>" +
    "<div><b>Ventaja</b><span>Nuestra probabilidad menos la que implica el momio. Positiva = valor.</span></div></div>" +
    '<div class="caja"><h3 style="font-size:22px">Como calculamos</h3><p class="gris_claro" style="font-size:14px;color:#C9D1DB">' +
    "Props: 60% cuantas veces el jugador paso la linea en sus ultimos partidos + 40% el consenso de las casas sin su comision. " +
    "Spreads y totales: consenso de varias casas sin comision, comparado contra el mejor momio disponible. " +
    "Solo mostramos picks donde nuestra probabilidad es mayor a la del momio.</p></div></div></div></section>";

  if (D.fuentes) {
    html += '<section><div class="titulo"><h2 style="font-size:26px">Fuentes de esta edicion</h2><p>De aqui salen las lineas, momios y estadisticas.</p></div><div class="caja" style="gap:8px">';
    D.fuentes.forEach(function (f) {
      html += '<a href="' + esc(f[1]) + '" target="_blank" rel="noopener">' + esc(f[0]) + "</a>";
    });
    if (D.descartados && D.descartados.length) {
      html += '<p class="gris" style="font-size:13px;margin-top:8px">Revisados sin ventaja (no se recomiendan): ' + esc(D.descartados.join(", ")) + "</p>";
    }
    html += "</div></section>";
  }

  app.innerHTML = html;
  activarCalculadora();
  var b = document.getElementById("ir_calc");
  if (b) b.onclick = function (e) { e.preventDefault(); irA("herramientas"); };
}

function activarCalculadora() {
  var ids = ["c_apuesta", "c_m1", "c_m2", "c_m3"];
  function calcular() {
    var apuesta = parseFloat(document.getElementById("c_apuesta").value) || 0;
    var decimal = 1;
    for (var i = 1; i < ids.length; i++) {
      var m = parseFloat(document.getElementById(ids[i]).value);
      if (m >= 100) decimal = decimal * (1 + m / 100);
      if (m <= -100) decimal = decimal * (1 + 100 / -m);
    }
    var pago = apuesta * decimal;
    document.getElementById("r_pago").textContent = "$" + pago.toFixed(2);
    document.getElementById("r_ganancia").textContent = "$" + (pago - apuesta).toFixed(2);
    document.getElementById("r_prob").textContent = (100 / decimal).toFixed(1) + "%";
  }
  ids.forEach(function (id) { document.getElementById(id).oninput = calcular; });
  calcular();
}

// ---------- DEPORTE ----------

function pintarDeporte(grupo) {
  tiraDeportes(grupo);
  var info = D.grupos[grupo] || { picks: 0, partidos: 0, ligas: [] };
  var todos = picksDe(grupo);

  var lista = todos.filter(function (p) {
    return (filtro.liga === "Todas" || p.liga === filtro.liga) && (filtro.tipo === "Todos" || p.tipo === filtro.tipo);
  });

  var html = '<div class="migas"><a href="#">&larr; Inicio</a><span>/</span><span style="color:#E8EDF3">' + grupo + "</span></div>";
  html += '<section style="gap:16px"><span class="etiqueta">' + esc(info.ligas.join(" - ")) + "</span>" +
    '<h1 style="font-size:clamp(40px,6vw,64px);line-height:1">Picks de ' + grupo + "</h1>" +
    '<p class="gris">' + info.partidos + " partidos analizados - " + todos.length + " picks con ventaja</p>";

  if (info.partidos === 0) {
    html += '<div class="aviso">' + (D.manual ? grupo + " llega con la version automatica. Esta edicion solo trae NBA." : "No hay partidos de " + grupo + " esta semana (puede estar fuera de temporada).") + "</div>";
  }

  if (info.ligas.length > 1) {
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">';
    ["Todas"].concat(info.ligas).forEach(function (l) {
      html += '<button type="button" class="tab' + (filtro.liga === l ? " activo" : "") + '" data-liga="' + esc(l) + '">' + esc(l) + "</button>";
    });
    html += "</div>";
  }
  html += "</section>";

  if (todos.length > 0) {
    var mejor = todos[0];
    html += '<a class="caja destacada" href="#pick-' + mejor.id + '" style="color:inherit"><span class="etiqueta verde_lleno">Mejor pick de ' + grupo + "</span>" +
      '<span class="gris">' + esc(mejor.partido) + " - " + fecha(mejor.fecha) + '</span><h2 style="font-size:34px">' + esc(mejor.pick) + "</h2>" +
      '<span class="gris" style="font-size:14px">' + esc(mejor.mercado) + " - Momio " + momio(mejor.momio) + " - " + mejor.unidades + "u</span>" + barra(mejor.prob) + "</a>";
  }

  html += '<section><div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:14px"><h2 style="font-size:30px">Todos los picks</h2><div class="segmento">';
  ["Todos", "Spreads", "Totales", "Props"].forEach(function (t) {
    html += '<button type="button" class="tab' + (filtro.tipo === t ? " activo" : "") + '" data-tipo="' + t + '">' + t + "</button>";
  });
  html += '</div></div><div class="rejilla_ancha">';
  lista.forEach(function (p) { html += tarjetaPick(p); });
  html += "</div>";
  if (lista.length === 0) html += '<div class="vacio">No hay picks con este filtro.</div>';
  html += "</section>";

  var racha = jugadoresEnRacha(todos, 8);
  if (racha.length > 0) {
    html += '<section><div class="titulo"><h2 style="font-size:30px">Jugadores en tendencia</h2><p>Picale a un jugador para ver su grafica partido por partido.</p></div><div class="rejilla">';
    racha.forEach(function (p) { html += tarjetaJugador(p); });
    html += "</div></section>";
  }

  app.innerHTML = html;

  app.querySelectorAll("[data-liga]").forEach(function (b) {
    b.onclick = function () { filtro.liga = b.getAttribute("data-liga"); pintarDeporte(grupo); };
  });
  app.querySelectorAll("[data-tipo]").forEach(function (b) {
    b.onclick = function () { filtro.tipo = b.getAttribute("data-tipo"); pintarDeporte(grupo); };
  });
}

// ---------- DETALLE DE UN PICK / JUGADOR ----------

function pintarPick(id) {
  var p = buscarPick(id);
  if (!p) { location.hash = ""; return; }
  tiraDeportes(p.grupo);

  var html = '<div class="migas"><a href="#">Inicio</a><span>/</span><a href="#deporte-' + p.grupo + '">' + p.grupo + '</a><span>/</span><span style="color:#E8EDF3">' + esc(p.jugador || p.partido) + "</span></div>";

  if (p.valores) {
    // Encabezado del jugador
    html += '<section class="caja" style="flex-direction:row;flex-wrap:wrap;align-items:center;gap:28px">' +
      '<div class="grande" style="display:flex;align-items:center;gap:20px;flex-basis:420px">' +
      '<div style="width:88px;height:88px;flex:none;border-radius:999px;background:#1E2733;border:2px solid #C6F432;display:flex;align-items:center;justify-content:center;color:#9AA4B2"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="8" r="4"></circle><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"></path></svg></div>' +
      '<div><span class="verde" style="font-size:12px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase">' + esc(p.grupo) + "</span>" +
      '<h1 style="font-size:clamp(30px,4.5vw,46px);line-height:1.05">' + esc(p.jugador) + '</h1><span class="gris">' + esc(p.equipo || p.liga) + " - " + esc(p.partido) + " - " + fecha(p.fecha) + "</span></div></div>" +
      '<div class="chica mini_stats"><div class="mini"><b>' + p.promedio + "</b><span>Promedio ult. " + p.valores.length + '</span></div><div class="mini"><b>' + p.mediana + '</b><span>Mediana</span></div><div class="mini"><b class="verde">' + p.linea + "</b><span>Linea actual</span></div></div></section>";

    // Otras lineas del mismo jugador
    var otras = D.picks.filter(function (o) { return o.jugador === p.jugador && o.evento === p.evento; });
    if (otras.length > 1) {
      html += '<div style="display:flex;flex-wrap:wrap;gap:8px">';
      otras.forEach(function (o) {
        html += '<a class="tab' + (o.id === p.id ? " activo" : "") + '" href="#pick-' + o.id + '" style="display:inline-flex;align-items:center">' + esc(o.mercado) + "</a>";
      });
      html += "</div>";
    }

    // Grafica de barras
    var maximo = Math.max.apply(null, p.valores.concat([p.linea])) * 1.15;
    var alturaLinea = (p.linea / maximo) * 100;
    html += '<section class="fila" style="align-items:flex-start"><div class="grande" style="display:flex;flex-direction:column;gap:20px">' +
      '<div class="caja"><div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px"><div><h2 style="font-size:22px">' + esc(p.mercado) + " - ultimos " + p.valores.length + ' partidos</h2><span class="gris" style="font-size:13px">Cada barra es un partido (del mas viejo al mas nuevo). La linea punteada es la linea de la casa.</span></div>' +
      '<div class="leyenda"><span><i style="background:#C6F432"></i>Le pego al ' + esc(p.lado) + '</span><span><i style="background:#3A4655"></i>No le pego</span></div></div>' +
      '<div><b class="mono verde" style="font-size:36px">' + p.aciertos + "/" + p.valores.length + '</b> <span class="gris">veces le pego al ' + esc(p.lado) + " " + p.linea + "</span></div>" +
      '<div class="grafica" role="img" aria-label="' + esc(p.mercado) + ": " + p.valores.join(", ") + '">';
    p.valores.forEach(function (v) {
      var paso = p.lado === "Over" ? v > p.linea : v < p.linea;
      html += '<div class="columna"><span>' + v + '</span><div style="height:' + Math.max(2, (v / maximo) * 100) + "%;background:" + (paso ? "#C6F432" : "#3A4655") + '"></div></div>';
    });
    html += '<div class="linea_casa" style="bottom:' + alturaLinea + '%"><b>Linea ' + p.linea + "</b></div></div></div>";

    // Splits
    html += '<div class="caja"><h2 style="font-size:22px">Resumen de ' + esc(p.mercado.toLowerCase()) + '</h2><div class="mini_stats">' +
      '<div class="mini"><b>' + p.promedio + '</b><span>Promedio</span></div><div class="mini"><b>' + p.mediana + "</b><span>Mediana</span></div>" +
      '<div class="mini"><b>' + p.maximo + '</b><span>Maximo</span></div><div class="mini"><b>' + p.minimo + "</b><span>Minimo</span></div>" +
      '<div class="mini"><b>' + (p.promedio - p.linea > 0 ? "+" : "") + (p.promedio - p.linea).toFixed(1) + "</b><span>Promedio vs linea</span></div></div></div></div>";
  } else {
    html += '<section class="fila" style="align-items:flex-start"><div class="grande" style="display:flex;flex-direction:column;gap:20px">' +
      '<div class="caja"><span class="etiqueta">' + esc(p.liga) + " - " + esc(p.tipo) + '</span><h1 style="font-size:clamp(30px,4.5vw,46px)">' + esc(p.partido) + '</h1><span class="gris">' + fecha(p.fecha) + "</span></div>" +
      '<div class="caja"><h2 style="font-size:22px">De donde sale este pick</h2><p style="color:#C9D1DB">Comparamos ' + p.casas + " casas de apuestas. Les quitamos su comision para sacar la probabilidad justa (" + p.prob + "%). " +
      "El mejor momio lo tiene " + esc(p.casa) + " (" + momio(p.momio) + "), que implica " + p.implicita + "%. La diferencia es tu ventaja: +" + p.ventaja + "%.</p></div></div>";
  }

  // Columna derecha: el pick
  html += '<aside class="chica" style="display:flex;flex-direction:column;gap:20px"><div class="caja destacada"><span class="etiqueta verde_lleno">Pick sugerido</span>' +
    '<b style="font-family:Space Grotesk,sans-serif;font-size:26px;line-height:1.15">' + esc(p.pick) + "</b>" +
    '<span class="gris" style="font-size:14px">' + esc(p.mercado) + " - Momio " + momio(p.momio) + " en " + esc(p.casa) + " - " + p.unidades + "u</span>" +
    barra(p.prob) +
    '<div class="mini_stats"><div class="mini"><b class="verde">+' + p.ventaja + '%</b><span>Ventaja</span></div><div class="mini"><b>' + p.implicita + "%</b><span>Prob. del momio</span></div></div>" +
    '<span class="gris" style="font-size:12px">' + esc(p.base) + "</span></div></aside></section>";

  app.innerHTML = html;
}

// ---------- Rutas ----------

function pintar() {
  var ruta = location.hash.replace("#", "");
  document.getElementById("actualizado").textContent = "Actualizado " + (D.actualizado || "-");
  if (ruta.indexOf("deporte-") === 0) {
    pintarDeporte(decodeURIComponent(ruta.split("-")[1]));
  } else if (ruta.indexOf("pick-") === 0) {
    pintarPick(parseInt(ruta.split("-")[1], 10));
  } else {
    pintarInicio();
  }
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", function () {
  filtro = { liga: "Todas", tipo: "Todos" };
  pintar();
});

document.querySelectorAll("[data-ir]").forEach(function (a) {
  a.onclick = function (e) {
    e.preventDefault();
    var destino = a.getAttribute("data-ir");
    if (location.hash !== "" && location.hash !== "#") {
      location.hash = "";
    }
    irA(destino);
  };
});

pintar();
