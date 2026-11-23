// ============================================
// PICKLAB - pinta la pagina con los datos de picks.js e historial.js
// Rutas:  #  (inicio)   #deporte-NBA   #pick-5   #historial
// ============================================

var D = window.PICKS || { picks: [], grupos: {}, parlay: { ids: [] }, partidos_analizados: 0 };
var H = window.HISTORIAL || null;
var ORDEN_GRUPOS = ["NFL", "NBA", "Futbol", "MLB", "NHL", "UFC", "Tenis"];
var app = document.getElementById("app");

// Color de cada deporte
var COLORES = {
  NFL: "#FF6B3D", NBA: "#FFA62B", Futbol: "#2BD99F", MLB: "#FF4D6D",
  NHL: "#4CC9F0", UFC: "#E040FB", Tenis: "#D7F25A"
};

// Iconos sencillos de cada deporte (SVG)
var ICONOS = {
  NFL: '<ellipse cx="12" cy="12" rx="9.5" ry="5.5" transform="rotate(-40 12 12)"></ellipse><path d="M9.5 14.5l5-5M10.3 11.3l2.4 2.4M11.8 9.8l2.4 2.4"></path>',
  NBA: '<circle cx="12" cy="12" r="9"></circle><path d="M3 12h18M12 3v18M5.6 5.6c3.2 3.4 3.2 9.4 0 12.8M18.4 5.6c-3.2 3.4-3.2 9.4 0 12.8"></path>',
  Futbol: '<circle cx="12" cy="12" r="9"></circle><path d="M12 8l3.6 2.6-1.4 4.2H9.8L8.4 10.6z"></path><path d="M12 8V3.5M15.6 10.6l4.2-1.4M14.2 14.8l2.6 3.6M9.8 14.8l-2.6 3.6M8.4 10.6L4.2 9.2"></path>',
  MLB: '<circle cx="12" cy="12" r="9"></circle><path d="M6.5 5c2.2 2.4 2.2 11.6 0 14M17.5 5c-2.2 2.4-2.2 11.6 0 14"></path>',
  NHL: '<ellipse cx="12" cy="10" rx="8" ry="3"></ellipse><path d="M4 10v4c0 1.7 3.6 3 8 3s8-1.3 8-3v-4"></path>',
  UFC: '<path d="M13 2L4 14h7l-1 8 9-12h-7z"></path>',
  Tenis: '<circle cx="12" cy="12" r="9"></circle><path d="M3.3 10c4.5.2 8.2-2.6 9-7M20.7 14c-4.5-.2-8.2 2.6-9 7"></path>'
};

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

function color(grupo) {
  return COLORES[grupo] || "#C6F432";
}

function icono(grupo, tam) {
  tam = tam || 22;
  return '<svg class="icono" width="' + tam + '" height="' + tam + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (ICONOS[grupo] || "") + "</svg>";
}

function estiloDeporte(grupo) {
  return ' style="--c:' + color(grupo) + '"';
}

// La barra usa un degradado; mientras mas alta la probabilidad, mas verde se ve el final
function barra(prob) {
  var tam = prob > 0 ? (100 / prob) * 100 : 100;
  return '<div class="prob"><div class="barra"><div style="width:' + prob + "%;background-size:" + tam + '% 100%"></div></div><span class="mono" style="font-size:13px">' + prob + "%</span></div>";
}

function anillo(prob, texto) {
  return '<div class="anillo" style="--p:' + prob + '"><div><b>' + prob + "%</b><span>" + texto + "</span></div></div>";
}

var NOMBRE_GRUPO = { NFL: "Americano", NBA: "Basquet", Futbol: "Futbol", MLB: "Beisbol", NHL: "Hockey", UFC: "UFC", Tenis: "Tenis" };

function nombreGrupo(g) {
  return NOMBRE_GRUPO[g] || g;
}

// Pastilla de confianza: nivel A o B y el score de 0 a 100
function nivel(p) {
  if (!p.nivel) return "";
  return '<span class="nivel n' + p.nivel + '" title="Confianza ' + p.score + ' de 100">Nivel ' + p.nivel + " <b>" + p.score + "</b></span>";
}

function iconoRazon(tipo) {
  if (tipo === "+") return '<i class="r_icono a_favor" aria-label="a favor">&#10003;</i>';
  if (tipo === "-") return '<i class="r_icono en_contra" aria-label="en contra">!</i>';
  return '<i class="r_icono info" aria-label="dato">i</i>';
}

// Las razones mas fuertes: primero a favor, luego en contra
function razonesCortas(p, cuantas) {
  if (!p.razones) return "";
  var favor = p.razones.filter(function (r) { return r.tipo === "+"; });
  var contra = p.razones.filter(function (r) { return r.tipo === "-"; });
  var lista = favor.slice(0, cuantas - (contra.length ? 1 : 0)).concat(contra.slice(0, 1));
  var html = '<ul class="razones cortas">';
  lista.forEach(function (r) { html += "<li>" + iconoRazon(r.tipo) + "<span>" + esc(r.texto) + "</span></li>"; });
  return html + "</ul>";
}

function cajaRazones(p) {
  if (!p.razones) return "";
  var html = '<div class="caja razones_caja"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;align-items:center">' +
    '<div><span class="sobretitulo" style="--c:#22D3EE">Motor PickLab</span><h2 style="font-size:22px">Por que este pick</h2></div>' + nivel(p) + "</div>" +
    '<div class="medidor"><div style="width:' + p.score + '%"></div></div>' +
    '<p class="gris" style="font-size:14px">Confianza ' + p.score + " de 100. Coinciden " + p.senales + " senales (mercado, estadisticas, contexto). " +
    "Apuesta sugerida: " + p.unidades + "u (1u = 1% de tu banco).</p>" + '<ul class="razones">';
  p.razones.forEach(function (r) { html += "<li>" + iconoRazon(r.tipo) + "<span>" + esc(r.texto) + "</span></li>"; });
  return html + "</ul></div>";
}

function unidadesTexto(u) {
  return (u > 0 ? "+" : "") + u.toFixed(2) + "u";
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
  var html = '<a class="tab' + (activo === "" ? " activo" : "") + '" href="#">Inicio</a>';
  ORDEN_GRUPOS.forEach(function (g) {
    html += '<a class="tab' + (activo === g ? " activo" : "") + '" href="#deporte-' + g + '"' + estiloDeporte(g) + ">" + icono(g, 16) + nombreGrupo(g) + "</a>";
  });
  html += '<a class="tab' + (activo === "historial" ? " activo" : "") + '" href="#historial" style="--c:#8B5CF6">Historial</a>';
  document.getElementById("tira").innerHTML = html;
}

function cinta() {
  var el = document.getElementById("cinta");
  if (!el || D.picks.length === 0) { if (el) el.style.display = "none"; return; }
  var piezas = "";
  D.picks.slice(0, 12).forEach(function (p) {
    piezas += '<a href="#pick-' + p.id + '"' + estiloDeporte(p.grupo) + '><span class="punto"></span>' + esc(p.grupo) + " <b>" + esc(p.pick) + '</b><span class="mono">' + momio(p.momio) + "</span><span class=\"mono verde\">" + p.prob + "%</span></a>";
  });
  // Se repite dos veces para que la cinta de la vuelta sin cortes
  el.innerHTML = '<div class="cinta_dentro">' + piezas + piezas + "</div>";
}

function chispa(p) {
  var maximo = Math.max.apply(null, p.valores.concat([p.linea])) || 1;
  var html = '<div class="chispa" aria-hidden="true">';
  p.valores.forEach(function (v) {
    var paso = p.lado === "Over" ? v > p.linea : v < p.linea;
    html += '<span style="height:' + Math.max(6, (v / maximo) * 100) + "%;background:" + (paso ? "var(--c)" : "var(--barra_mal)") + '"></span>';
  });
  return html + "</div>";
}

function tarjetaJugador(p) {
  return '<a class="tarjeta"' + estiloDeporte(p.grupo) + ' href="#pick-' + p.id + '">' +
    '<span class="etiqueta deporte">' + icono(p.grupo, 14) + esc(p.grupo) + " - " + esc(p.mercado) + "</span>" +
    '<span><b style="font-family:Space Grotesk,sans-serif;font-size:19px">' + esc(p.jugador) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.equipo) + "</span></span>" +
    "<b>" + esc(p.lado) + " " + p.linea + " " + esc(p.mercado.toLowerCase()) + "</b>" +
    chispa(p) + selloDuelo(p) +
    '<span style="display:flex;justify-content:space-between;border-top:1px solid var(--borde);padding-top:12px">' +
    '<span class="mono" style="font-size:14px"><b style="color:var(--c)">' + p.aciertos + "</b> de sus ultimos " + p.valores.length + "</span>" +
    '<span style="font-weight:600;font-size:14px;color:var(--c)">Ver &rarr;</span></span></a>';
}

function tarjetaPick(p) {
  return '<a class="tarjeta"' + estiloDeporte(p.grupo) + ' href="#pick-' + p.id + '">' +
    '<span style="display:flex;justify-content:space-between;gap:8px"><span class="etiqueta deporte">' + icono(p.grupo, 14) + esc(p.tipo) + " - " + esc(p.liga) + '</span><span class="gris" style="font-size:13px">' + fecha(p.fecha) + "</span></span>" +
    '<span><span class="gris" style="font-size:14px">' + esc(p.partido) + '</span><br><b style="font-family:Space Grotesk,sans-serif;font-size:22px">' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.mercado) + " - " + esc(p.base) + "</span></span>" +
    nivel(p) + barra(p.prob) + razonesCortas(p, 3) + selloDuelo(p) +
    '<div class="pie_tarjeta"><div><b>' + momio(p.momio) + "</b>Momio</div><div><b>" + esc(p.casa) + "</b>Casa</div><div><b class=\"verde\">+" + p.ventaja + "%</b>Ventaja</div><div><b>" + p.unidades + "u</b>Unidades</div></div></a>";
}


// ---------- BAJA LA LINEA (lineas alternas para Draftea) ----------

function tarjetaEscalera(e) {
  var html = '<div class="tarjeta"' + estiloDeporte(e.grupo) + '>' +
    '<span style="display:flex;justify-content:space-between;gap:8px"><span class="etiqueta deporte">' + icono(e.grupo, 14) + esc(e.grupo) + " - " + esc(e.mercado) + '</span><span class="gris" style="font-size:13px">' + fecha(e.fecha) + "</span></span>" +
    '<span><b style="font-family:Space Grotesk,sans-serif;font-size:19px">' + esc(e.jugador) + '</b><br><span class="gris" style="font-size:13px">' + esc(e.partido) + "</span></span>" +
    '<span class="gris" style="font-size:13px">Linea principal: ' + esc(e.lado) + " " + e.linea + " (" + momio(e.momio) + " en " + esc(e.casa) + ") - promedia " + e.promedio + "</span>" +
    '<div class="escalera">';
  e.pasos.forEach(function (p) {
    html += '<div class="escalon"><b>' + esc(e.lado) + " " + p.linea + "</b>" +
      '<span class="mono" style="color:var(--c)">' + p.prob + "%</span>" +
      '<span class="gris">' + p.aciertos + "/" + p.partidos + "</span>" +
      '<span class="mono">min ' + momio(p.momio_minimo) + "</span></div>";
  });
  return html + "</div></div>";
}

function bloqueEscalera(lista, maximo, titulo) {
  if (!lista || lista.length === 0) return "";
  var html = '<section id="escalera"><div class="titulo"><span class="sobretitulo" style="--c:#C6F432">Para Draftea</span><h2>' + titulo + "</h2>" +
    "<p>Si tu casa te deja bajar (o subir) la linea, aqui esta que tan seguro queda cada jugador. " +
    "La probabilidad sale del mercado de la linea principal + sus ultimos partidos. " +
    "<b>No es pick todavia:</b> solo tiene valor si te pagan el momio minimo (min) o mejor. Ej. si dice min -300, un -250 si vale; un -400 no.</p></div><div class=\"rejilla\">";
  lista.slice(0, maximo).forEach(function (e) { html += tarjetaEscalera(e); });
  return html + "</div></section>";
}


// ---------- ULTIMO ENFRENTAMIENTO ----------

function fechaCorta(iso) {
  var d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("es-MX", { day: "numeric", month: "short", year: "numeric" });
}

// Sello chiquito: si con la linea de hoy hubiera pegado en el ultimo duelo
function selloDuelo(p) {
  if (!p.duelo || p.duelo.pego === undefined) return "";
  var pego = p.duelo.pego;
  var clase = pego === true ? "si" : pego === false ? "no" : "igual";
  var texto = pego === true ? "Pegaba en el ultimo duelo" : pego === false ? "No pegaba en el ultimo duelo" : "Empate en el ultimo duelo";
  return '<span class="sello_duelo ' + clase + '">' + (pego === true ? "&#10003; " : pego === false ? "&#10007; " : "= ") + texto + "</span>";
}

function marcadorDuelo(d, grupo) {
  var v = d.marcador[0], l = d.marcador[1];
  var ganaV = v[1] > l[1], ganaL = l[1] > v[1];
  return '<div class="duelo_marcador"' + estiloDeporte(grupo) + ">" +
    '<div class="duelo_equipo' + (ganaV ? " gano" : "") + '"><span>' + esc(v[0]) + '</span><b class="mono">' + v[1] + "</b><small>Visitante</small></div>" +
    '<div class="duelo_vs">VS</div>' +
    '<div class="duelo_equipo' + (ganaL ? " gano" : "") + '"><span>' + esc(l[0]) + '</span><b class="mono">' + l[1] + "</b><small>Local</small></div></div>";
}

function cajaDuelo(p) {
  var d = p.duelo;
  if (!d) {
    return '<div class="caja"><h2 style="font-size:22px">Ultimo enfrentamiento</h2><p class="gris">No encontramos datos verificados del ultimo partido entre estos rivales.</p></div>';
  }
  var html = '<div class="caja duelo"' + estiloDeporte(p.grupo) + '><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;align-items:center">' +
    '<div><span class="sobretitulo">Head to head</span><h2 style="font-size:22px">Ultimo enfrentamiento</h2></div>' + selloDuelo(p) + "</div>";

  var j = d.jugador;
  if (j) {
    var claves = { pts: "PTS", reb: "REB", ast: "AST", tri: "3PM", min: "MIN" };
    var usados = { "Puntos": ["pts"], "Rebotes": ["reb"], "Asistencias": ["ast"], "Triples": ["tri"], "Puntos + Asistencias": ["pts", "ast"], "Puntos + Rebotes": ["pts", "reb"], "Pts + Reb + Ast": ["pts", "reb", "ast"] }[p.mercado] || [];
    html += '<div class="gris" style="font-size:14px">' + esc(p.jugador) + " vs " + esc(j.rival) + " - " + fechaCorta(j.fecha) + " - jugaba con " + esc(j.equipo) + "</div>";
    html += '<div class="duelo_stats">';
    Object.keys(claves).forEach(function (k) {
      html += '<div class="mini' + (usados.indexOf(k) !== -1 ? " marcada" : "") + '"><b>' + j[k] + "</b><span>" + claves[k] + "</span></div>";
    });
    html += "</div>";
  }
  if (d.marcador) {
    html += '<div class="gris" style="font-size:13px">' + esc(d.liga || "") + " - " + fechaCorta(d.fecha) + (j && j.fecha !== d.fecha ? " (ultimo partido entre los equipos)" : "") + "</div>";
    html += marcadorDuelo(d, p.grupo);
  }
  if (d.resumen) {
    html += '<p style="color:var(--gris_claro)">' + esc(d.resumen) + ".</p>";
  }
  if (d.detalle) {
    html += '<p class="gris" style="font-size:14px">' + esc(d.detalle) + "</p>";
  }
  if (d.anteriores && d.anteriores.length) {
    html += '<div class="duelo_antes"><span class="gris" style="font-size:12px;text-transform:uppercase;letter-spacing:0.08em">Antes de eso</span>';
    d.anteriores.forEach(function (a) { html += "<span>" + esc(a) + "</span>"; });
    html += "</div>";
  }
  var fuente = (j && j.fuente) || d.fuente;
  if (fuente) {
    html += '<a href="' + esc(fuente) + '" target="_blank" rel="noopener" style="font-size:13px">Ver box score &rarr;</a>';
  }
  html += '<span class="gris" style="font-size:12px">Un solo partido pesa poco: mueve la probabilidad maximo 1 punto, y solo si fue en el ultimo ano.</span>';
  return html + "</div>";
}

// ---------- HISTORIAL (pedazos) ----------

// Grafica de linea con las unidades acumuladas
function graficaUnidades(serie) {
  var ancho = 800, alto = 220, margen = 24;
  var valores = [0].concat(serie.map(function (s) { return s.u; }));
  var max = Math.max.apply(null, valores.concat([1]));
  var min = Math.min.apply(null, valores.concat([-1]));
  function x(i) { return margen + (i / Math.max(1, valores.length - 1)) * (ancho - 2 * margen); }
  function y(v) { return margen + ((max - v) / (max - min)) * (alto - 2 * margen); }
  var puntos = valores.map(function (v, i) { return x(i).toFixed(1) + "," + y(v).toFixed(1); });
  var final = valores[valores.length - 1];
  var trazo = final >= 0 ? "#C6F432" : "#FF5C7A";
  return '<svg viewBox="0 0 ' + ancho + " " + alto + '" preserveAspectRatio="none" role="img" aria-label="Unidades acumuladas: ' + final + '">' +
    '<defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="' + trazo + '" stop-opacity="0.35"></stop><stop offset="1" stop-color="' + trazo + '" stop-opacity="0"></stop></linearGradient></defs>' +
    '<line x1="' + margen + '" x2="' + (ancho - margen) + '" y1="' + y(0) + '" y2="' + y(0) + '" stroke="rgba(255,255,255,0.25)" stroke-dasharray="4 6"></line>' +
    '<polygon points="' + x(0) + "," + y(0) + " " + puntos.join(" ") + " " + x(valores.length - 1) + "," + y(0) + '" fill="url(#area)"></polygon>' +
    '<polyline points="' + puntos.join(" ") + '" fill="none" stroke="' + trazo + '" stroke-width="3" stroke-linejoin="round" vector-effect="non-scaling-stroke"></polyline>' +
    "</svg>";
}

function marcadorHistorial(t) {
  var u = t.unidades;
  return '<div class="marcador">' +
    '<div class="caja"><span>Record (G - P - E)</span><b>' + t.ganados + "-" + t.perdidos + "-" + t.empates + "</b></div>" +
    '<div class="caja"><span>% de acierto</span><b class="brillo">' + (t.acierto === null ? "-" : t.acierto + "%") + "</b>" +
    '<span>El modelo esperaba ' + (t.prob_promedio === null ? "-" : t.prob_promedio + "%") + "</span></div>" +
    '<div class="caja"><span>Unidades</span><b class="' + (u >= 0 ? "verde" : "rojo") + '">' + unidadesTexto(u) + "</b></div>" +
    '<div class="caja"><span>ROI</span><b class="' + (t.roi === null || t.roi >= 0 ? "verde" : "rojo") + '">' + (t.roi === null ? "-" : (t.roi > 0 ? "+" : "") + t.roi + "%") + "</b><span>Ganancia / lo apostado</span></div></div>";
}

function renglonResultado(h) {
  return '<div class="resultado"' + estiloDeporte(h.grupo) + '><span class="sello ' + h.resultado + '">' + h.resultado + "</span>" +
    '<span style="min-width:0"><b>' + esc(h.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(h.grupo) + " - " + esc(h.partido) + " - " + momio(h.momio) + " - " + h.unidades + "u</span></span>" +
    '<span class="mono ' + (h.neto > 0 ? "verde" : h.neto < 0 ? "rojo" : "gris") + '">' + unidadesTexto(h.neto) + "</span></div>";
}

function bloqueHistorial(completo) {
  var html = "";
  if (!H) {
    return '<div class="caja"><p class="gris">Todavia no hay historial. Corre: python historial.py</p></div>';
  }
  var t = H.total;
  var hayResultados = t.ganados + t.perdidos + t.empates > 0;

  if (!hayResultados) {
    html += '<div class="caja vacio_historial" style="--c:#8B5CF6"><div style="flex:1 1 320px;display:flex;flex-direction:column;gap:8px">' +
      '<span class="sobretitulo">Empezamos a contar</span><h3 style="font-size:26px">' + H.pendientes + " picks esperando resultado</h3>" +
      '<p class="gris">Cada pick que publicamos se guarda. Cuando terminen los partidos los calificamos y aqui vas a ver el record, las unidades ganadas y si el modelo de verdad le pega.</p></div>' +
      '<div class="puntos_espera" style="flex:1 1 220px" aria-hidden="true">';
    for (var i = 0; i < Math.min(H.pendientes, 40); i++) {
      html += '<i style="animation-delay:' + (i * 0.06).toFixed(2) + 's"></i>';
    }
    return html + "</div></div>";
  }

  html += marcadorHistorial(t);
  html += '<div class="fila"><div class="caja grande linea_tiempo"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px"><h3 style="font-size:20px">Unidades acumuladas</h3><span class="gris" style="font-size:13px">' + H.serie.length + " picks calificados - " + H.pendientes + " pendientes</span></div>" + graficaUnidades(H.serie) + "</div>";

  html += '<div class="caja chica"><h3 style="font-size:20px">Por deporte</h3>';
  var maxAbs = 0.01;
  Object.keys(H.por_grupo).forEach(function (g) { maxAbs = Math.max(maxAbs, Math.abs(H.por_grupo[g].unidades)); });
  Object.keys(H.por_grupo).forEach(function (g) {
    var r = H.por_grupo[g];
    html += '<div class="barra_deporte"' + estiloDeporte(g) + '><span style="display:flex;gap:6px;align-items:center;color:var(--c)">' + icono(g, 16) + g + "</span>" +
      '<div class="barra"><div style="width:' + Math.max(4, (Math.abs(r.unidades) / maxAbs) * 100) + "%;background:" + (r.unidades >= 0 ? "var(--c)" : "var(--rojo)") + '"></div></div>' +
      '<span class="mono" style="font-size:13px;text-align:right">' + r.ganados + "-" + r.perdidos + " " + unidadesTexto(r.unidades) + "</span></div>";
  });
  if (H.clv) {
    var cl = H.clv;
    html += '<h3 style="font-size:20px;margin-top:8px">Contra el cierre</h3>' +
      '<p class="gris" style="font-size:14px">Si seguido conseguimos mejor momio que el que habia justo antes del partido, el modelo le esta ganando al mercado (aunque una semana salga mala).</p>';
    if (cl.picks > 0) {
      html += '<div style="display:flex;justify-content:space-between;font-size:14px"><span>' + cl.picks + " picks medidos</span>" +
        '<span class="mono"><span class="verde">' + cl.a_favor + " a favor</span> - " + '<span class="rojo">' + cl.en_contra + " en contra</span> - CLV promedio " +
        '<span class="' + (cl.promedio >= 0 ? "verde" : "rojo") + '">' + (cl.promedio > 0 ? "+" : "") + cl.promedio + " pts</span></span></div>";
    } else {
      html += '<p class="gris" style="font-size:14px">Empezamos a medirlo con los picks del 23 de noviembre.</p>';
    }
  }
  if (H.por_nivel) {
    html += '<h3 style="font-size:20px;margin-top:8px">Por nivel de confianza</h3>';
    Object.keys(H.por_nivel).forEach(function (n) {
      var r = H.por_nivel[n];
      html += '<div style="display:flex;justify-content:space-between;font-size:14px"><span>' + (n === "-" ? "Antes del motor" : "Nivel " + n) + '</span><span class="mono">' + r.ganados + "-" + r.perdidos + " - " + (r.acierto === null ? "-" : r.acierto + "%") + ' - <span class="' + (r.unidades >= 0 ? "verde" : "rojo") + '">' + unidadesTexto(r.unidades) + "</span></span></div>";
    });
  }
  html += '<h3 style="font-size:20px;margin-top:8px">Por tipo</h3>';
  Object.keys(H.por_tipo).forEach(function (tipo) {
    var r = H.por_tipo[tipo];
    html += '<div style="display:flex;justify-content:space-between;font-size:14px"><span>' + esc(tipo) + '</span><span class="mono">' + r.ganados + "-" + r.perdidos + " - " + (r.acierto === null ? "-" : r.acierto + "%") + ' - <span class="' + (r.unidades >= 0 ? "verde" : "rojo") + '">' + unidadesTexto(r.unidades) + "</span></span></div>";
  });
  html += "</div></div>";

  var lista = completo ? H.calificados : H.calificados.slice(0, 6);
  html += '<div class="caja"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px"><h3 style="font-size:20px">' + (completo ? "Todos los resultados" : "Ultimos resultados") + "</h3>" +
    (completo ? "" : '<a href="#historial" style="font-weight:600">Ver todo &rarr;</a>') + "</div><div>";
  lista.forEach(function (h) { html += renglonResultado(h); });
  html += "</div></div>";
  return html;
}

// ---------- INICIO ----------

function pintarInicio() {
  tiraDeportes("");
  var html = "";

  if (D.prueba) {
    html += '<div class="aviso">Estas viendo DATOS DE PRUEBA. Pega tus llaves en config.py y corre: python correr_todo.py</div>';
  }
  if (D.errores && D.errores.length) {
    html += '<div class="aviso error">Hubo errores al actualizar: ' + esc(D.errores.join(" | ")) + "</div>";
  }
  if (D.nota) {
    html += '<div class="aviso info">' + esc(D.nota) + "</div>";
  }

  if (D.picks.length === 0) {
    var texto = D.candidatos > 0
      ? "Hoy revisamos " + D.candidatos + " apuestas posibles y ninguna paso las reglas (55% o mas de probabilidad, 3% o mas de ventaja y nivel A o B). Mejor no apostar que apostar sin ventaja."
      : "Todavia no hay picks para hoy.";
    html += '<div class="vacio">' + texto + "</div>";
    html += bloqueEscalera(D.escalera, 12, "Baja la linea");
    if (H) {
      html += '<section id="historial_inicio"><div class="titulo"><span class="sobretitulo" style="--c:#8B5CF6">Transparencia</span><h2>Como nos ha ido</h2><p>Todos los picks publicados, ganados y perdidos. Sin borrar nada.</p></div>' + bloqueHistorial(false) + "</section>";
    }
    app.innerHTML = html;
    return;
  }

  var uno = D.picks[0];
  var top10 = D.picks.slice(0, 10);
  var deportesConPicks = ORDEN_GRUPOS.filter(function (g) { return picksDe(g).length > 0; }).length;

  // Hero
  html += '<section class="hero aparece"><div style="display:flex;flex-direction:column;gap:18px">' +
    '<span class="sobretitulo" style="--c:#22D3EE">Todos los deportes - Basado en datos</span>' +
    '<h1>Cada pick con <span class="brillo">numeros y razones</span>, no corazonadas.</h1>' +
    '<p class="gris" style="font-size:18px;max-width:560px">Nuestro motor cruza el mercado, las estadisticas y el contexto de cada partido. Solo publicamos lo que pasa todas las reglas, y te decimos por que.</p>' +
    '<div class="hero_datos">' +
    '<div class="hero_dato"><b class="brillo">' + D.partidos_analizados + "</b><span>Partidos analizados</span></div>" +
    '<div class="hero_dato"><b>' + D.picks.length + "</b><span>Pasaron el filtro</span></div>" +
    '<div class="hero_dato"><b>' + deportesConPicks + "</b><span>Deportes</span></div>" +
    (function () {
      var con = D.picks.filter(function (p) { return p.duelo && p.duelo.pego !== undefined; });
      var si = con.filter(function (p) { return p.duelo.pego === true; }).length;
      return con.length ? '<div class="hero_dato"><b>' + si + "/" + con.length + "</b><span>Pegaban en el ultimo duelo</span></div>" : "";
    })() +
    (H && H.total.acierto !== null ? '<div class="hero_dato"><b class="verde">' + H.total.acierto + '%</b><span>Acierto historico</span></div>' : "") +
    "</div></div>" +

    '<a class="caja destacada" href="#pick-' + uno.id + '" style="color:inherit">' +
    '<span style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px"><span class="etiqueta verde_lleno">Pick mas solido</span>' + nivel(uno) + '<span style="flex:1"></span><span class="etiqueta deporte"' + estiloDeporte(uno.grupo) + ">" + icono(uno.grupo, 14) + esc(uno.liga) + "</span></span>" +
    '<div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap">' + anillo(uno.prob, "probabilidad") +
    '<div style="flex:1;min-width:180px"><span class="gris" style="font-size:14px">' + esc(uno.partido) + " - " + fecha(uno.fecha) + "</span>" +
    '<h2 style="font-size:clamp(26px,3.4vw,36px);line-height:1.1">' + esc(uno.pick) + "</h2>" +
    '<span class="mono gris" style="font-size:14px">' + esc(uno.mercado) + " - " + momio(uno.momio) + " en " + esc(uno.casa) + "</span></div></div>" +
    '<div class="mini_stats">' +
    (uno.valores
      ? '<div class="mini"><b>' + uno.aciertos + "/" + uno.valores.length + "</b><span>Veces que paso la linea</span></div>" +
        '<div class="mini"><b>' + uno.promedio + "</b><span>Promedio vs linea " + uno.linea + "</span></div>"
      : '<div class="mini"><b>' + uno.modelo + "%</b><span>Nuestro modelo</span></div>") +
    '<div class="mini"><b class="verde">+' + uno.ventaja + '%</b><span>Ventaja vs el momio</span></div></div>' + razonesCortas(uno, 3) + "</a></section>";

  // Los mas solidos: nivel A y B, de cualquier deporte
  var solidos = D.picks.slice(0, 6);
  html += '<section id="seguros"><div class="titulo"><span class="sobretitulo" style="--c:#C6F432">Sin importar el deporte</span><h2>Los picks mas solidos</h2>' +
    "<p>Ordenados por confianza: probabilidad, ventaja contra el momio, cuantas senales coinciden y calidad de los datos." +
    (D.candidatos ? " Revisamos " + D.candidatos + " opciones y solo " + D.picks.length + " pasaron." : "") + '</p></div><div class="rejilla_ancha">';
  solidos.forEach(function (p) { html += tarjetaPick(p); });
  html += "</div></section>";

  // Deportes
  html += '<section id="deportes"><div class="titulo"><span class="sobretitulo" style="--c:#F472B6">Elige tu deporte</span><h2>Explora por deporte</h2><p>Picale a un deporte para ver todos sus picks.</p></div><div class="rejilla rejilla_deportes">';
  ORDEN_GRUPOS.forEach(function (g) {
    var info = D.grupos[g] || { picks: 0, partidos: 0, ligas: [] };
    var sin = info.partidos === 0;
    html += '<a class="tarjeta"' + estiloDeporte(g) + ' href="#deporte-' + g + '" style="min-height:190px">' +
      '<span style="display:flex;justify-content:space-between;align-items:center"><span class="icono_deporte">' + icono(g, 26) + "</span>" +
      '<span class="etiqueta' + (sin ? " amarilla" : "") + '">' + (sin ? (D.manual ? "Proximamente" : "Sin partidos") : info.partidos + " partidos") + "</span></span>" +
      '<span><b style="font-family:Space Grotesk,sans-serif;font-size:24px">' + nombreGrupo(g) + '</b><br><span class="gris" style="font-size:13px">' + esc(info.ligas.join(" - ")) + "</span></span>" +
      '<span style="margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end"><span><span class="numero_grande">' + info.picks + '</span> <span class="gris" style="font-size:13px">picks</span></span><span style="font-weight:600;color:var(--c)">Ver &rarr;</span></span></a>';
  });
  html += "</div></section>";

  // Top 10
  html += '<section id="picks"><div class="titulo"><span class="sobretitulo" style="--c:#FBBF24">Ranking</span><h2>Top 10 por confianza</h2><p>Todos pasaron: 55% o mas de probabilidad, 3% o mas de ventaja y nivel A o B.</p></div>' +
    '<div class="tabla_caja"><div class="tabla"><div class="renglon encabezado"><span>#</span><span>Confianza</span><span>Deporte</span><span>Partido / pick</span><span>Momio</span><span>Unidades</span><span>Probabilidad</span><span>Ventaja</span></div>';
  top10.forEach(function (p, i) {
    html += '<a class="renglon"' + estiloDeporte(p.grupo) + ' href="#pick-' + p.id + '"><span class="medalla' + (i < 3 ? " m" + (i + 1) : "") + '">' + (i + 1) + "</span>" + "<span>" + nivel(p) + "</span>" +
      '<span class="etiqueta deporte">' + icono(p.grupo, 14) + esc(p.grupo) + "</span>" +
      '<span><b>' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.partido) + " - " + esc(p.mercado) + "</span>" + (p.duelo && p.duelo.pego !== undefined ? "<br>" + selloDuelo(p) : "") + "</span>" +
      '<span class="mono">' + momio(p.momio) + '</span><span class="mono">' + p.unidades + "u</span>" + barra(p.prob) +
      '<span class="mono verde">+' + p.ventaja + "%</span></a>";
  });
  html += "</div></div></section>";

  // Lineas alternas
  html += bloqueEscalera(D.escalera, 12, "Baja la linea");

  // Historial (resumen)
  html += '<section id="historial_inicio"><div class="titulo"><span class="sobretitulo" style="--c:#8B5CF6">Transparencia</span><h2>Como nos ha ido</h2><p>Todos los picks publicados, ganados y perdidos. Sin borrar nada.</p></div>' + bloqueHistorial(false) + "</section>";

  // Jugadores en racha
  var racha = jugadoresEnRacha(D.picks, 4);
  if (racha.length > 0) {
    html += '<section id="tendencias"><div class="titulo"><span class="sobretitulo" style="--c:#FF6B3D">En fuego</span><h2>Jugadores en racha</h2><p>Los que mas veces pasaron su linea. Picale para ver su grafica.</p></div><div class="rejilla">';
    racha.forEach(function (p) { html += tarjetaJugador(p); });
    html += "</div></section>";
  }

  // Parlay
  if (D.parlay.ids.length > 1) {
    html += '<section id="parlay" class="fila" style="align-items:center"><div class="chica" style="display:flex;flex-direction:column;gap:10px">' +
      '<span class="sobretitulo" style="--c:#22D3EE">Combinada</span><h2 style="font-size:36px">Parlay sugerido</h2><p class="gris">Los picks mas probables de partidos diferentes. Menos piernas, mas chance de pegar.</p></div>' +
      '<div class="boleto grande"><span class="sobretitulo" style="--c:#CBD3E1">Boleto PickLab - ' + D.parlay.ids.length + " piernas</span>";
    D.parlay.ids.forEach(function (id, i) {
      var p = buscarPick(id);
      html += '<a class="pierna"' + estiloDeporte(p.grupo) + ' href="#pick-' + id + '">' +
        '<span class="icono_deporte" style="width:38px;height:38px;flex:none">' + icono(p.grupo, 20) + "</span>" +
        '<span style="flex:1;min-width:0"><b>' + esc(p.pick) + '</b><br><span class="gris" style="font-size:13px">' + esc(p.grupo) + " - " + esc(p.partido) + '</span></span><span class="mono">' + momio(p.momio) + "</span></a>";
    });
    html += '<div class="corte"></div><div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px"><div style="display:flex;gap:28px">' +
      '<div><span class="gris" style="font-size:13px">Momio combinado</span><br><b class="mono" style="font-size:26px">' + momio(D.parlay.momio) + "</b></div>" +
      '<div><span class="gris" style="font-size:13px">Probabilidad combinada</span><br><b class="mono brillo" style="font-size:26px">' + D.parlay.prob + "%</b></div></div>" +
      '<a class="boton" href="#" id="ir_calc">Calcular mi pago</a></div></div></section>';
  }

  // Herramientas
  html += '<section id="herramientas"><div class="titulo"><span class="sobretitulo" style="--c:#2BD99F">Para apostar mejor</span><h2>Herramientas</h2><p>Para que sepas cuanto ganas y cuanto arriesgas antes de apostar.</p></div><div class="fila">' +
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
    "<div><b>Ventaja</b><span>Nuestra probabilidad menos la que implica el momio. Positiva = valor.</span></div>" +
    "<div><b>Confianza</b><span>Score de 0 a 100 del motor. Nivel A: 70 o mas. Nivel B: 55 a 69. Abajo de 55 no se publica.</span></div>" +
    "<div><b>Unidad (u)</b><span>Tu apuesta base. Si 1u = $100, un pick de 2u es de $200.</span></div></div>" +
    '<div class="caja"><h3 style="font-size:22px">Instala PickLab en tu celular</h3><p style="font-size:14px;color:var(--gris_claro)">iPhone: abre la pagina en Safari, toca Compartir y luego Agregar a inicio. Android: abre el menu de Chrome y toca Instalar app.</p></div>' +
    '<div class="caja"><h3 style="font-size:22px">Como decide el motor</h3><p style="font-size:14px;color:var(--gris_claro)">' +
    "1) Mercado: lo que dicen las casas sin su comision; si hay varias, el consenso, y buscamos el mejor precio. " +
    "2) Estadisticas: en props, cuantas veces el jugador paso la linea en sus ultimos 10 (pesa hasta 60%); en spreads y totales, un modelo con lo que anota y recibe cada equipo (pesa hasta 50%). " +
    "3) Contexto: descanso, lesiones, racha y ultimo enfrentamiento, con un tope de 5 puntos. " +
    "4) Historial: si nuestros picks pegan menos de lo esperado, el motor baja su confianza solo. " +
    "Solo publicamos si la probabilidad es 55% o mas, la ventaja 3% o mas y el nivel es A o B. La apuesta sugerida sale de Kelly/16, entre 0.5u y 2u.</p></div></div></div></section>";

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

// ---------- PAGINA DE HISTORIAL ----------

function pintarHistorial() {
  tiraDeportes("historial");
  var html = '<div class="migas"><a href="#">&larr; Inicio</a><span>/</span><span style="color:var(--texto)">Historial</span></div>';
  html += '<section class="aparece" style="gap:12px"><span class="sobretitulo" style="--c:#8B5CF6">Transparencia</span>' +
    '<h1 style="font-size:clamp(40px,6vw,64px);line-height:1">Historial de <span class="brillo">resultados</span></h1>' +
    '<p class="gris" style="max-width:640px">Cada pick que publicamos queda aqui con su resultado. Ganado (G) paga segun su momio, perdido (P) resta sus unidades y empate (E) se devuelve.</p></section>';
  html += '<section>' + bloqueHistorial(true) + "</section>";
  app.innerHTML = html;
}

// ---------- DEPORTE ----------

function pintarDeporte(grupo) {
  tiraDeportes(grupo);
  var info = D.grupos[grupo] || { picks: 0, partidos: 0, ligas: [] };
  var todos = picksDe(grupo);

  var lista = todos.filter(function (p) {
    return (filtro.liga === "Todas" || p.liga === filtro.liga) && (filtro.tipo === "Todos" || p.tipo === filtro.tipo);
  });

  var html = '<div class="migas"><a href="#">&larr; Inicio</a><span>/</span><span style="color:var(--texto)">' + grupo + "</span></div>";
  html += '<section class="aparece"' + estiloDeporte(grupo) + ' style="gap:16px;--c:' + color(grupo) + '"><div style="display:flex;align-items:center;gap:16px"><span class="icono_deporte" style="width:64px;height:64px">' + icono(grupo, 34) + '</span><span class="etiqueta deporte">' + esc(info.ligas.join(" - ")) + "</span></div>" +
    '<h1 style="font-size:clamp(40px,6vw,64px);line-height:1">Picks de <span style="color:var(--c)">' + nombreGrupo(grupo) + "</span></h1>" +
    '<p class="gris">' + info.partidos + " partidos analizados - " + todos.length + " picks con ventaja</p>";

  if (info.partidos === 0) {
    html += '<div class="aviso">' + (D.manual ? grupo + " llega en las proximas ediciones." : "No hay partidos de " + grupo + " esta semana (puede estar fuera de temporada).") + "</div>";
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
      '<div style="display:flex;gap:20px;align-items:center;flex-wrap:wrap">' + anillo(mejor.prob, "probabilidad") +
      '<div style="flex:1;min-width:200px"><span class="gris">' + esc(mejor.partido) + " - " + fecha(mejor.fecha) + '</span><h2 style="font-size:32px">' + esc(mejor.pick) + "</h2>" +
      '<span class="gris" style="font-size:14px">' + esc(mejor.mercado) + " - Momio " + momio(mejor.momio) + " - " + mejor.unidades + "u</span></div></div></a>";
  }

  html += '<section><div style="display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:14px"><h2 style="font-size:30px">Todos los picks</h2><div class="segmento">';
  ["Todos", "Spreads", "Totales", "Props"].forEach(function (t) {
    html += '<button type="button" class="tab' + (filtro.tipo === t ? " activo" : "") + '" data-tipo="' + t + '">' + t + "</button>";
  });
  html += '</div></div><div class="rejilla_ancha">';
  lista.forEach(function (p) { html += tarjetaPick(p); });
  html += "</div>";
  if (lista.length === 0) {
    if (todos.length === 0 && info.partidos > 0) {
      html += '<div class="vacio">Revisamos ' + info.partidos + " partidos de " + grupo + " y ninguno tuvo ventaja suficiente. Mejor no apostar que apostar sin ventaja.</div>";
    } else {
      html += '<div class="vacio">No hay picks con este filtro.</div>';
    }
  }
  html += "</section>";

  html += bloqueEscalera((D.escalera || []).filter(function (e) { return e.grupo === grupo; }), 40, "Baja la linea en " + nombreGrupo(grupo));

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
  var c = color(p.grupo);

  var html = '<div class="migas"><a href="#">Inicio</a><span>/</span><a href="#deporte-' + p.grupo + '">' + p.grupo + '</a><span>/</span><span style="color:var(--texto)">' + esc(p.jugador || p.partido) + "</span></div>";

  if (p.valores) {
    // Encabezado del jugador
    html += '<section class="caja aparece" style="--c:' + c + ';flex-direction:row;flex-wrap:wrap;align-items:center;gap:28px">' +
      '<div class="grande" style="display:flex;align-items:center;gap:20px;flex-basis:420px">' +
      '<div style="width:88px;height:88px;flex:none;border-radius:999px;background:color-mix(in srgb, var(--c) 14%, transparent);border:2px solid var(--c);box-shadow:0 0 30px -6px var(--c);display:flex;align-items:center;justify-content:center;color:var(--c)">' + icono(p.grupo, 40) + "</div>" +
      '<div><span class="sobretitulo">' + esc(p.grupo) + "</span>" +
      '<h1 style="font-size:clamp(30px,4.5vw,46px);line-height:1.05">' + esc(p.jugador) + '</h1><span class="gris">' + esc(p.equipo || p.liga) + " - " + esc(p.partido) + " - " + fecha(p.fecha) + "</span></div></div>" +
      '<div class="chica mini_stats"><div class="mini"><b>' + p.promedio + "</b><span>Promedio ult. " + p.valores.length + '</span></div><div class="mini"><b>' + p.mediana + '</b><span>Mediana</span></div><div class="mini"><b style="color:var(--c)">' + p.linea + "</b><span>Linea actual</span></div></div></section>";

    // Otras lineas del mismo jugador
    var otras = D.picks.filter(function (o) { return o.jugador === p.jugador && o.evento === p.evento; });
    if (otras.length > 1) {
      html += '<div style="display:flex;flex-wrap:wrap;gap:8px">';
      otras.forEach(function (o) {
        html += '<a class="tab' + (o.id === p.id ? " activo" : "") + '" href="#pick-' + o.id + '">' + esc(o.mercado) + "</a>";
      });
      html += "</div>";
    }

    // Grafica de barras
    var maximo = Math.max.apply(null, p.valores.concat([p.linea])) * 1.15;
    var alturaLinea = (p.linea / maximo) * 100;
    html += '<section class="fila" style="align-items:flex-start;--c:' + c + '"><div class="grande" style="display:flex;flex-direction:column;gap:20px">' + cajaRazones(p) +
      '<div class="caja"><div style="display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px"><div><h2 style="font-size:22px">' + esc(p.mercado) + " - ultimos " + p.valores.length + ' partidos</h2><span class="gris" style="font-size:13px">Cada barra es un partido (del mas viejo al mas nuevo). La linea punteada es la linea de la casa.</span></div>' +
      '<div class="leyenda"><span><i style="background:var(--c)"></i>Le pego al ' + esc(p.lado) + '</span><span><i style="background:var(--barra_mal)"></i>No le pego</span></div></div>' +
      '<div><b class="mono" style="font-size:36px;color:var(--c)">' + p.aciertos + "/" + p.valores.length + '</b> <span class="gris">veces le pego al ' + esc(p.lado) + " " + p.linea + "</span></div>" +
      '<div class="grafica" role="img" aria-label="' + esc(p.mercado) + ": " + p.valores.join(", ") + '">';
    p.valores.forEach(function (v) {
      var paso = p.lado === "Over" ? v > p.linea : v < p.linea;
      html += '<div class="columna"><span>' + v + '</span><div style="height:' + Math.max(2, (v / maximo) * 100) + "%;background:" + (paso ? "linear-gradient(180deg, var(--c), color-mix(in srgb, var(--c) 45%, transparent))" : "var(--barra_mal)") + '"></div></div>';
    });
    html += '<div class="linea_casa" style="bottom:' + alturaLinea + '%"><b>Linea ' + p.linea + "</b></div></div></div>";

    // Splits
    html += '<div class="caja"><h2 style="font-size:22px">Resumen de ' + esc(p.mercado.toLowerCase()) + '</h2><div class="mini_stats">' +
      '<div class="mini"><b>' + p.promedio + '</b><span>Promedio</span></div><div class="mini"><b>' + p.mediana + "</b><span>Mediana</span></div>" +
      '<div class="mini"><b>' + p.maximo + '</b><span>Maximo</span></div><div class="mini"><b>' + p.minimo + "</b><span>Minimo</span></div>" +
      '<div class="mini"><b>' + (p.promedio - p.linea > 0 ? "+" : "") + (p.promedio - p.linea).toFixed(1) + "</b><span>Promedio vs linea</span></div></div></div>" + cajaDuelo(p) + "</div>";
  } else {
    html += '<section class="fila" style="align-items:flex-start;--c:' + c + '"><div class="grande" style="display:flex;flex-direction:column;gap:20px">' +
      '<div class="caja aparece"><div style="display:flex;align-items:center;gap:14px"><span class="icono_deporte">' + icono(p.grupo, 26) + '</span><span class="etiqueta deporte">' + esc(p.liga) + " - " + esc(p.tipo) + '</span></div><h1 style="font-size:clamp(30px,4.5vw,46px)">' + esc(p.partido) + '</h1><span class="gris">' + fecha(p.fecha) + "</span></div>" + cajaRazones(p) +
      (p.explicacion
        ? '<div class="caja"><h2 style="font-size:22px">De donde sale este pick</h2><p style="color:var(--gris_claro)">' + esc(p.explicacion) + "</p>" +
          '<div class="mini_stats"><div class="mini"><b>' + p.modelo + '%</b><span>Nuestro modelo</span></div><div class="mini"><b>' + p.mercado_prob + '%</b><span>Mercado sin comision</span></div><div class="mini"><b class="brillo">' + p.prob + "%</b><span>Probabilidad final</span></div></div></div>" + cajaDuelo(p) + "</div>"
        : '<div class="caja"><h2 style="font-size:22px">De donde sale este pick</h2><p style="color:var(--gris_claro)">Comparamos ' + p.casas + " casas de apuestas. Les quitamos su comision para sacar la probabilidad justa (" + p.prob + "%). " +
          "El mejor momio lo tiene " + esc(p.casa) + " (" + momio(p.momio) + "), que implica " + p.implicita + "%. La diferencia es tu ventaja: +" + p.ventaja + "%.</p></div></div>");
  }

  // Columna derecha: el pick
  html += '<aside class="chica" style="display:flex;flex-direction:column;gap:20px"><div class="caja destacada"><span class="etiqueta verde_lleno">Pick sugerido</span>' + nivel(p) +
    '<div style="display:flex;gap:16px;align-items:center">' + anillo(p.prob, "probabilidad") +
    '<b style="font-family:Space Grotesk,sans-serif;font-size:24px;line-height:1.15">' + esc(p.pick) + "</b></div>" +
    '<span class="gris" style="font-size:14px">' + esc(p.mercado) + " - Momio " + momio(p.momio) + " en " + esc(p.casa) + " - " + p.unidades + "u</span>" +
    '<div class="mini_stats"><div class="mini"><b class="verde">+' + p.ventaja + '%</b><span>Ventaja</span></div><div class="mini"><b>' + p.implicita + "%</b><span>Prob. del momio</span></div></div>" +
    '<span class="gris" style="font-size:12px">' + esc(p.base) + "</span></div></aside></section>";

  app.innerHTML = html;
}

// ---------- Instalar como app ----------

var promptInstalar = null;
window.addEventListener("beforeinstallprompt", function (e) {
  e.preventDefault();
  promptInstalar = e;
  var b = document.getElementById("instalar");
  if (b) b.style.display = "inline-flex";
});

function botonInstalar() {
  var b = document.getElementById("instalar");
  if (!b) return;
  b.onclick = function () {
    if (promptInstalar) {
      promptInstalar.prompt();
      promptInstalar = null;
      b.style.display = "none";
    }
  };
}

// ---------- Rutas ----------

function pintar() {
  var ruta = location.hash.replace("#", "");
  document.getElementById("actualizado").textContent = "Actualizado " + (D.actualizado || "-");
  if (ruta.indexOf("deporte-") === 0) {
    pintarDeporte(decodeURIComponent(ruta.split("-")[1]));
  } else if (ruta.indexOf("pick-") === 0) {
    pintarPick(parseInt(ruta.split("-")[1], 10));
  } else if (ruta === "historial") {
    pintarHistorial();
  } else {
    pintarInicio();
  }
  window.scrollTo(0, 0);
}

window.addEventListener("hashchange", function () {
  filtro = { liga: "Todas", tipo: "Todos" };
  botonInstalar();
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

cinta();
botonInstalar();
pintar();
