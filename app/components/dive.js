// Kanz descent: a window you dive through, from the reef to 6,400 m.
// The depth meter reads the scroll; the count is real (NOAA coral and sponge taxa recorded deeper than you are).
const STOPS = [0, 200, 1000, 4000, 6400];          // depth (m)
const AT = [0, 0.22, 0.42, 0.70, 1.0];             // share of the column height
const ZONES = [[0, "Sunlight zone"], [200, "Twilight zone"], [1000, "Midnight zone"], [4000, "Abyss"]];
const REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const toY = (m) => {
  for (let i = 1; i < STOPS.length; i++) if (m <= STOPS[i]) return AT[i - 1] + (AT[i] - AT[i - 1]) * (m - STOPS[i - 1]) / (STOPS[i] - STOPS[i - 1]);
  return 1;
};
const toM = (y) => {
  for (let i = 1; i < AT.length; i++) if (y <= AT[i]) return STOPS[i - 1] + (STOPS[i] - STOPS[i - 1]) * (y - AT[i - 1]) / (AT[i] - AT[i - 1]);
  return STOPS[STOPS.length - 1];
};
const fmt = (n) => Math.round(n).toLocaleString("en-US");

export default function (component) {
  const { data, parentElement } = component;
  if (parentElement.querySelector(".dvw")) return;
  const H = data.column || 4600;
  const depths = data.depths;                         // sorted ascending
  const deeper = (m) => { let lo = 0, hi = depths.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (depths[mid] < m) lo = mid + 1; else hi = mid; } return depths.length - lo; };

  const outer = document.createElement("div");
  outer.className = "dvw";
  outer.innerHTML = `
    <div class="dv"><div class="col" style="height:${H}px"></div></div>
    <div class="hud">
      <button class="go"><svg viewBox="0 0 24 24"><path d="M12 4v16M6 14l6 6 6-6"/></svg><span>Dive to 6,000 m</span></button>
      <div class="meter"><div class="m"><span class="num">0</span> m</div><div class="z">Sunlight zone</div>
        <div class="c"><b class="cnt">${fmt(depths.length)}</b> coral and sponge taxa recorded deeper than you</div></div>
    </div>`;
  parentElement.appendChild(outer);
  const wrap = outer.querySelector(".dv");
  const col = wrap.querySelector(".col");
  const VIEW = wrap.clientHeight || 680;
  // depth m sits in the middle of the window exactly when the meter reads m
  const y = (m) => toY(m) * (H - VIEW) + VIEW / 2;

  ZONES.forEach(([m, name]) => {
    const z = document.createElement("div");
    z.className = "zone"; z.style.top = y(m) + "px";
    z.innerHTML = `<span class="d">${fmt(m)} m</span><span class="n">${name}</span>`;
    col.appendChild(z);
  });
  data.notes.forEach((n) => {
    const el = document.createElement("div");
    el.className = "note"; el.style.top = y(n.m) + "px";
    el.innerHTML = n.html;
    col.appendChild(el);
  });
  data.creatures.forEach((c, i) => {
    const el = document.createElement("figure");
    el.className = "cr " + (i % 2 ? "r" : "l");
    el.style.top = (y(c.m) - 70) + "px";
    el.innerHTML = `<img src="${c.src}" alt="${c.name}" loading="lazy"><figcaption><b>${c.name}</b><span>${c.label}</span></figcaption>`;
    col.appendChild(el);
  });

  const num = outer.querySelector(".num"), zone = outer.querySelector(".z"), cnt = outer.querySelector(".cnt");
  const update = () => {
    const max = wrap.scrollHeight - wrap.clientHeight;
    const m = toM(max > 0 ? Math.min(1, Math.max(0, wrap.scrollTop / max)) : 0);
    num.textContent = fmt(m);
    zone.textContent = [...ZONES].reverse().find(([d]) => m >= d)[1];
    cnt.textContent = fmt(deeper(m));
  };
  wrap.addEventListener("scroll", update, { passive: true });
  update();

  // the dive: an eased descent over ~14 s; any wheel or touch hands control back
  const btn = outer.querySelector(".go");
  let raf = null;
  const stop = () => { if (raf) cancelAnimationFrame(raf); raf = null; btn.classList.remove("on"); btn.querySelector("span").textContent = "Dive to 6,000 m"; };
  btn.onclick = () => {
    if (raf) return stop();
    const from = wrap.scrollTop >= wrap.scrollHeight - wrap.clientHeight - 4 ? 0 : wrap.scrollTop;
    const to = wrap.scrollHeight - wrap.clientHeight, dur = REDUCED ? 1 : 14000 * (1 - from / to);
    const t0 = performance.now();
    btn.classList.add("on"); btn.querySelector("span").textContent = "Pause";
    const ease = (t) => (t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
    const step = (now) => {
      const t = Math.min(1, (now - t0) / dur);
      wrap.scrollTop = from + (to - from) * ease(t);
      if (t < 1) raf = requestAnimationFrame(step); else stop();
    };
    raf = requestAnimationFrame(step);
  };
  ["wheel", "touchstart"].forEach((e) => wrap.addEventListener(e, () => raf && stop(), { passive: true }));
  return () => stop();
}
