// Kanz living globe: one WebGL globe (globe.gl, vendored in app/static/vendor) drawn from our real outputs.
// Modes: "risk"     reef regions today, column = treasure at risk, colour = heat stress, rings = top regions
//        "treasure" 5° ocean cells, column = hidden species (Model 1)
//        "time"     a year of weekly heat stress you can play like a film
const LIB = "app/static/vendor/globe.gl.min.js";
const LAND = "app/static/vendor/countries.geojson";
const HEAT = ["#3E7F8C", "#8E8F6E", "#D9A15E", "#FF8A5B", "#FF5A3C", "#FF2E1F"];
const WATER = ["#1B4A5C", "#1E6F82", "#2399A3", "#34D5C4", "#8FF0E4", "#E8FFFB"];
const REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function loadLib() {
  if (window.Globe) return Promise.resolve(window.Globe);
  if (!window.__kzGlobeLib) {
    window.__kzGlobeLib = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = new URL(LIB, document.baseURI).href;
      s.onload = () => resolve(window.Globe);
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }
  return window.__kzGlobeLib;
}
function loadLand() {
  if (!window.__kzLand) window.__kzLand = fetch(new URL(LAND, document.baseURI).href).then((r) => r.json());
  return window.__kzLand;
}
function mix(scale, t) {
  t = Math.max(0, Math.min(1, t)) * (scale.length - 1);
  const i = Math.floor(t), f = t - i, a = scale[i], b = scale[Math.min(i + 1, scale.length - 1)];
  const c = (h, k) => parseInt(h.slice(1 + 2 * k, 3 + 2 * k), 16);
  return "#" + [0, 1, 2].map((k) => Math.round(c(a, k) + (c(b, k) - c(a, k)) * f).toString(16).padStart(2, "0")).join("");
}
const fmt = (n) => Math.round(n).toLocaleString("en-US");
const snd = (lat, lon) => `${Math.abs(lat).toFixed(1)}°${lat >= 0 ? "N" : "S"} ${Math.abs(lon).toFixed(1)}°${lon >= 0 ? "E" : "W"}`;

function tip(title, rows, lat, lon) {
  return `<div class="kg-tip"><b>${title}</b><span class="snd">${snd(lat, lon)}</span>` +
    rows.map(([k, v]) => `<div class="r"><span>${k}</span><span>${v}</span></div>`).join("") + "</div>";
}

function riskLayer(g, d, state) {
  const pts = d.points;
  g.pointsData(pts).pointLat("lat").pointLng("lon")
    .pointAltitude((p) => 0.01 + (p.v / 100) * 0.32)
    .pointRadius((p) => (p.name === d.focus ? 0.75 : 0.42))
    .pointColor((p) => (p.name === d.focus ? "#34D5C4" : mix(HEAT, p.dhw / 16)))
    .pointLabel((p) => tip(p.name, [["Treasure at risk", fmt(p.v)], ["Heat stress", p.dhw.toFixed(1) + " DHW"], ["Severe risk", Math.round(p.risk * 100) + "%"], ["Rank", "#" + p.rank + " of 214"]], p.lat, p.lon))
    .ringsData(REDUCED ? [] : pts.filter((p) => d.rings.includes(p.name))).ringLat("lat").ringLng("lon")
    .ringColor(() => (t) => `rgba(232,140,110,${(1 - t) * 0.9})`).ringMaxRadius(3.2).ringPropagationSpeed(1.4).ringRepeatPeriod(1600);
  if (d.clickable) {
    g.onPointClick((p) => { state.stopSpin(); state.setTriggerValue("picked", p.name); }).pointsTransitionDuration(400);
  }
  const f = pts.find((p) => p.name === d.focus);
  g.htmlElementsData(f && d.showFocus ? [f] : []).htmlLat("lat").htmlLng("lon").htmlAltitude((p) => 0.02 + (p.v / 100) * 0.32)
    .htmlElement((p) => {
      const el = document.createElement("div");
      el.className = "kg-pin";
      el.innerHTML = `<b>${p.name}</b><span>DHW ${p.dhw.toFixed(1)} · #${p.rank}</span>`;
      return el;
    });
  if (f && d.showFocus && state.focus !== d.focus) {
    if (state.focus !== undefined || d.flyOnStart) { state.stopSpin(); g.pointOfView({ lat: f.lat, lng: f.lon, altitude: 1.65 }, 1400); }
    state.focus = d.focus;
  }
}

function treasureLayer(g, d) {
  const top = Math.max(...d.points.map((p) => p.h)) || 1;
  g.pointsData(d.points).pointLat("lat").pointLng("lon").pointsMerge(false)
    .pointAltitude((p) => 0.003 + Math.pow(p.h / top, 1.8) * 0.3).pointRadius(1.15)
    .pointColor((p) => mix(WATER, Math.sqrt(p.h / top)))
    .pointLabel((p) => tip(`+${fmt(p.h)} hidden species`, [["Recorded", fmt(p.r)], ["Expected", fmt(p.e)], ["Sea temperature", p.t == null ? "no data" : p.t.toFixed(0) + " °C"]], p.lat, p.lon));
}

function timeLayer(g, d, state, root) {
  const n = d.weeks.length;
  const ui = document.createElement("div");
  ui.className = "kg-film";
  ui.innerHTML = `<button class="play" aria-label="Play a year of heat stress"><svg viewBox="0 0 24 24"><path d="M7 5v14l11-7z"/></svg></button>
    <div class="info"><div class="date"></div><div class="count"></div></div>
    <input class="scrub" type="range" min="0" max="${n - 1}" step="1" value="0" aria-label="Week">`;
  root.appendChild(ui);
  const btn = ui.querySelector(".play"), scrub = ui.querySelector(".scrub");
  const date = ui.querySelector(".date"), count = ui.querySelector(".count");
  let frame = 0, timer = null;
  g.pointLat("lat").pointLng("lon").pointRadius(0.5).pointsTransitionDuration(REDUCED ? 0 : 260)
    .pointAltitude((p) => 0.008 + Math.min(p.dhw, 20) / 20 * 0.3).pointColor((p) => mix(HEAT, p.dhw / 16))
    .pointLabel((p) => tip(p.name, [["Week of", d.weeks[frame]], ["Heat stress", p.dhw.toFixed(1) + " DHW"]], p.lat, p.lon))
    .ringLat("lat").ringLng("lon").ringColor(() => (t) => `rgba(232,140,110,${(1 - t) * 0.8})`)
    .ringMaxRadius(2.6).ringPropagationSpeed(1.6).ringRepeatPeriod(1200);
  const show = (i) => {
    frame = i;
    const pts = d.stations.map((s, k) => ({ ...s, dhw: d.dhw[i][k] }));
    g.pointsData(pts);
    g.ringsData(REDUCED ? [] : pts.filter((p) => p.dhw >= 8));
    const alert = pts.filter((p) => p.dhw >= 4).length;
    date.textContent = "Week of " + d.weeks[i];
    count.innerHTML = `<b>${alert}</b> of ${pts.length} reef regions on bleaching alert`;
    scrub.value = i;
  };
  const stop = () => { clearInterval(timer); timer = null; btn.classList.remove("on");
    btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M7 5v14l11-7z"/></svg>'; };
  const play = () => {
    if (frame >= n - 1) show(0);
    btn.classList.add("on"); btn.innerHTML = '<svg viewBox="0 0 24 24"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>';
    timer = setInterval(() => {
      if (frame >= n - 1) {                      // the year ends: turn to where the heat is today
        stop(); state.stopSpin();
        if (d.endView) g.pointOfView({ lat: d.endView.lat, lng: d.endView.lon, altitude: d.endView.alt || 1.9 }, 1800);
        return;
      }
      show(frame + 1);
    }, REDUCED ? 600 : 320);
  };
  btn.onclick = () => (timer ? stop() : play());
  scrub.oninput = () => { stop(); show(+scrub.value); };
  show(0);
  state.cleanups.push(stop);
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let root = parentElement.querySelector(".kg");
  if (!root) {
    root = document.createElement("div");
    root.className = "kg";
    parentElement.appendChild(root);
  }
  root.style.height = (data.height || 560) + "px";
  let state = root.__kz;
  if (state && state.mode === data.mode && state.g) {
    state.setTriggerValue = setTriggerValue;
    if (data.mode === "risk") riskLayer(state.g, data, state);
    return;
  }
  state = root.__kz = { mode: data.mode, cleanups: [], setTriggerValue, focus: undefined };
  Promise.all([loadLib(), loadLand()]).then(([Globe, land]) => {
    if (!root.isConnected) return;
    const g = Globe({ animateIn: !REDUCED })(root)
      .width(root.clientWidth).height(data.height || 560)
      .backgroundColor("rgba(0,0,0,0)")
      .showAtmosphere(true).atmosphereColor("#34D5C4").atmosphereAltitude(0.14)
      .polygonsData(land.features).polygonAltitude(0.005)
      .polygonCapColor(() => "#D8CBAF").polygonSideColor(() => "rgba(0,0,0,0)").polygonStrokeColor(() => "rgba(31,27,22,.18)")
      .polygonsTransitionDuration(0);
    g.globeMaterial().color.set("#0B3A52");
    g.globeMaterial().shininess = 4;
    const c = g.controls();
    c.enableZoom = false;              // never steal the page scroll
    c.autoRotate = !REDUCED;
    c.autoRotateSpeed = data.spin ?? 0.45;
    state.stopSpin = () => { c.autoRotate = false; };
    root.addEventListener("pointerdown", state.stopSpin, { once: true });
    g.pointOfView({ lat: data.view?.lat ?? 15, lng: data.view?.lon ?? 40, altitude: data.view?.alt ?? 2.3 }, 0);
    state.g = g;
    const legend = document.createElement("div");   // added after init: the globe empties its container
    legend.className = "kg-legend";
    legend.innerHTML = data.legend || "";
    root.appendChild(legend);
    if (data.mode === "risk") riskLayer(g, data, state);
    if (data.mode === "treasure") treasureLayer(g, data);
    if (data.mode === "time") timeLayer(g, data, state, root);
    const ro = new ResizeObserver(() => g.width(root.clientWidth));
    ro.observe(root);
    state.cleanups.push(() => ro.disconnect(), () => { try { g.pauseAnimation(); g._destructor && g._destructor(); } catch (e) {} });
  });

  return () => {
    // the component left the page (another tab opened): free the WebGL context
    if (!root.isConnected) { state.cleanups.forEach((f) => f()); root.__kz = null; }
  };
}
