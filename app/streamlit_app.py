"""Kanz | كنز — find the ocean's hidden life before heat takes it.

Run from the project folder:
    streamlit run app/streamlit_app.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
DATA = ROOT / "datasets_csv"
APP = Path(__file__).resolve().parent

st.set_page_config(page_title="Kanz | كنز", page_icon=":material/water:", layout="wide")

# colours (same tokens as style.css)
TEXT, TEXT2, MUTED, LINE = "#EEF6F6", "#B4C9CD", "#86A2A9", "rgba(238,246,246,.08)"
ACCENT, HEAT, NEUTRAL, NEUTRAL_2, CARD = "#34D5C4", "#FF6A4D", "#4E6C77", "#24485A", "#0B2535"
WATER_SCALE = ["#1B4A5C", "#1E6F82", "#2399A3", "#34D5C4", "#8FF0E4", "#E8FFFB"]
HEAT_SCALE = ["#3E7F8C", "#8E8F6E", "#D9A15E", "#FF8A5B", "#FF5A3C", "#FF2E1F"]
TABS = ["Kanz", "Discover", "Danger", "At risk", "Dive"]
SAUDI = ["Jazan, Saudi Arabia", "Al Madinah and Makkah", "Tabuk, Saudi Arabia"]
# deep-sea photos with no text burned into the frame (checked by eye)
# one clean photo per depth band for the dive (checked by eye)
DIVE_PHOTOS = ["Coenocyathus bowersi", "Errinopora", "Spirastrellidae", "Trissopathes pseudotristicha", "Desmophyllum dianthus",
               "Farrea occa", "Primnoidae", "Hyalostylus", "Porifera", "Umbellula"]


# ---------------------------------------------------------------- data (loaded once per server)
@st.cache_data
def load_outputs():
    return {
        "treasure": pd.read_csv(OUT / "treasure_map.csv"),
        "risk": pd.read_csv(OUT / "risk_today.csv"),
        "dive": pd.read_csv(OUT / "dive_finder.csv"),
        "inputs": pd.read_csv(OUT / "station_inputs.csv"),
        "res1": pd.read_csv(OUT / "results_model1.csv"),
        "res2": pd.read_csv(OUT / "results_model2.csv"),
        "future": pd.read_csv(OUT / "results_future_test.csv"),
    }


@st.cache_data
def load_story_data():
    # coral bleaching: one row per sample (the file repeats each sample per seabed type)
    bleaching = pd.read_csv(DATA / "coral_bleaching_surveys.csv.gz", na_values=["nd"], low_memory=False)
    samples = bleaching[bleaching["Percent_Bleaching"].notna()].drop_duplicates("Sample_ID")
    severe = samples["Percent_Bleaching"] >= 20

    heat_groups = pd.cut(samples["TSA_DHW"], [-0.1, 0, 2, 4, 8, 100], labels=["0", "0–2", "2–4", "4–8", "8+"])
    heat_vs_bleach = (severe.groupby(heat_groups, observed=True).mean() * 100).round(1)

    hot = samples["TSA_DHW"] >= 4
    red = samples["Ecoregion_Name"].str.contains("Red Sea|Gulf of Aden", na=False)
    red_sea = {"Red Sea": round(severe[hot & red].mean() * 100, 1), "Rest of the world": round(severe[hot & ~red].mean() * 100, 1)}

    # coral -> fish (Reef Life Survey)
    surveys = pd.read_csv(DATA / "reef_life_surveys.csv")
    coral_groups = pd.cut(surveys["hard_coral_pct"], [-0.1, 0, 10, 30, 50, 100], labels=["0%", "0–10%", "10–30%", "30–50%", "50%+"])
    coral_vs_fish = surveys.groupby(coral_groups, observed=True)["fish_species"].mean().round(1)

    # discovery curve (OBIS)
    animals = pd.read_csv(DATA / "obis_marine_animal_species.csv.gz", low_memory=False)
    species = animals[animals["taxonRank"] == "Species"]
    year = species["scientificNameAuthorship"].str.extract(r"(1[789]\d\d|20\d\d)")[0].astype(float)
    per_decade = (year // 10 * 10).value_counts().sort_index()
    per_decade = per_decade[per_decade.index >= 1750]
    seen_once = round((species["records"] == 1).mean() * 100, 1)

    # NOAA daily heat stress + station places
    heat = pd.read_csv(DATA / "noaa_reef_heat_stress_daily.csv.gz")
    heat["date"] = pd.to_datetime(heat[["year", "month", "day"]])
    stations = pd.read_csv(DATA / "noaa_reef_stations.csv")

    return {"heat_vs_bleach": heat_vs_bleach, "red_sea": red_sea, "coral_vs_fish": coral_vs_fish,
            "per_decade": per_decade, "seen_once": seen_once, "heat": heat.merge(stations, on="station"),
            "threatened": pd.read_csv(DATA / "threatened_species_near_dive_sites.csv"),
            "corals": pd.read_csv(DATA / "deep_sea_corals_species.csv")}


@st.cache_resource
def load_bleaching_model():
    return joblib.load(ROOT / "models" / "model2_bleaching_risk.joblib")


# ---------------------------------------------------------------- small helpers
def html(text):
    st.markdown(text, unsafe_allow_html=True)


def snd(lat, lon):
    # the signature: a place's coordinates, written like a sounding on a chart
    return f'<span class="kz-snd">{abs(lat):.1f}°{"N" if lat >= 0 else "S"} {abs(lon):.1f}°{"E" if lon >= 0 else "W"}</span>'


def head(label, title, text="", first=False):
    html(f'<div class="kz-head {"first" if first else ""}"><div class="label">{label}</div><h2>{title}</h2>'
         + (f"<p>{text}</p>" if text else "") + "</div>")


def stat(label, value, note="", heat=False, tone=""):
    return (f'<div class="kz-card kz-stat"><div class="k">{label}</div><div class="v {"heat" if heat else tone}">{value}</div>'
            + (f'<div class="c">{note}</div>' if note else "") + "</div>")


def bars(rows, top, unit="%", caption=""):
    # an evidence chart drawn as a list with thin bars; only the row that matters gets colour
    out = '<div class="kz-bars">'
    for label, value, tone in rows:
        out += (f'<div class="r"><div class="lab">{label}</div><div class="track"><div class="fill {tone}" '
                f'style="width:{value / top * 100:.1f}%"></div></div><div class="num">{value:.0f}{unit}</div></div>')
    return out + (f'<div class="cap">{caption}</div>' if caption else "") + "</div>"


def go_to(tab):
    st.session_state["tab"] = tab


def send_to_model(place):
    st.session_state["model_place"] = place
    go_to("Danger")


def next_button(label, tab):
    with st.container(key="next"):
        st.button(f"{label}  →", on_click=go_to, args=(tab,), type="primary", key=f"next_{tab}")


def chart(fig, height=420, margin=None, key=None, select=False):
    fig.update_layout(height=height, margin=margin or dict(l=8, r=8, t=24, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Instrument Sans", size=15, color=TEXT2),
                      hoverlabel=dict(font_family="Instrument Sans", font_size=15, bgcolor=CARD, bordercolor="#1E4153", font_color=TEXT),
                      showlegend=False)
    fig.update_xaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(family="IBM Plex Mono", size=13, color=MUTED))
    fig.update_yaxes(gridcolor=LINE, zeroline=False, linecolor=LINE, tickfont=dict(family="IBM Plex Mono", size=13, color=MUTED))
    config = {"displayModeBar": False, "scrollZoom": False}
    if select:
        return st.plotly_chart(fig, width="stretch", config=config, key=key, on_select="rerun", selection_mode="points")
    st.plotly_chart(fig, width="stretch", config=config, key=key)


def style_map(fig, projection="natural earth", rotation=None, bar_title=""):
    fig.update_geos(projection_type=projection, projection_rotation=rotation, showland=True, landcolor="#17323F",
                    showocean=True, oceancolor="#08202D", showcountries=False, coastlinecolor="#2E5363", coastlinewidth=.6,
                    showlakes=False, showframe=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-60, 75])
    fig.update_layout(coloraxis_colorbar=dict(orientation="h", x=.5, xanchor="center", y=-.02, yanchor="top", len=.4,
                                              thickness=6, outlinewidth=0, title=dict(text=bar_title, side="top",
                                              font=dict(size=12, color=TEXT2)),
                                              tickfont=dict(family="IBM Plex Mono", size=11, color=MUTED)))
    return fig


def picked(event, field=0):
    # the first clicked point's custom data, or None
    try:
        points = event.selection["points"]
        return points[0]["customdata"][field] if points else None
    except (AttributeError, KeyError, IndexError, TypeError):
        return None


# ---------------------------------------------------------------- custom pieces (app/components): globe, dive, presenter keys
def _part(name):
    return (APP / "components" / name).read_text(encoding="utf-8")


GLOBE = st.components.v2.component("kanz_globe", js=_part("globe.js"), css=_part("globe.css"))
DIVE = st.components.v2.component("kanz_dive", js=_part("dive.js"), css=_part("dive.css"))
KEYS = st.components.v2.component("kanz_keys", js=_part("keys.js"))


def globe(mode, key, height=580, **data):
    # a 3D globe of our real outputs; returns the reef region the user clicked (risk mode), else None
    result = GLOBE(key=key, data={"mode": mode, "height": height, **data}, height=height, on_picked_change=lambda: None)
    return getattr(result, "picked", None)


def risk_points():
    return [{"name": r.station, "lat": round(r.lat, 2), "lon": round(r.lon, 2), "dhw": round(float(r.dhw), 1),
             "v": round(float(r.treasure_at_risk), 1), "risk": round(float(r.severe_risk), 3), "rank": int(r.rank)}
            for r in risk.itertuples()]


RISK_LEGEND = ('<b>Today on 214 reef regions</b>'
               '<div class="k"><i style="background:#FF6A4D"></i>Colour: heat stress today</div>'
               '<div class="k"><i style="background:#EEF6F6;width:3px;height:12px"></i>Height: treasure at risk</div>'
               '<div class="k"><i style="border:1.5px solid #E88C6E;border-radius:50%"></i>Rings: the 8 regions most at risk</div>'
               '<div class="mono" style="margin-top:6px">Drag to turn the globe</div>')


# ---------------------------------------------------------------- state
st.session_state.setdefault("focus", "Jazan, Saudi Arabia")   # the reef region followed across tabs
# Dive filters: defaults live in session state, and re-saving them keeps them when another tab is open
DIVE_DEFAULTS = {"w_fish": .30, "w_coral": .25, "w_vis": .15, "w_risk": .15, "w_bleach": .15,
                 "countries": [], "min_fish": 0, "only_cr": False}
for k, v in DIVE_DEFAULTS.items():
    st.session_state[k] = st.session_state.get(k, v)

html(f"<style>{(APP / 'style.css').read_text(encoding='utf-8')}</style>")
out = load_outputs()
story = load_story_data()
risk, dive, treasure = out["risk"], out["dive"], out["treasure"]
today = pd.to_datetime(risk["date"]).max()

alert_today = int((risk["dhw"] >= 4).sum())
saudi = risk[risk["station"].isin(SAUDI)].set_index("station")
jazan = saudi.loc["Jazan, Saudi Arabia"]
top_risk = risk.sort_values("treasure_at_risk", ascending=False)
severe_today = int((risk["risk_class"] == 2).sum())

html(f'<div class="kz-brand"><div class="mark">Kanz<span>كنز</span></div>'
     f'<div class="meta">NOAA Coral Reef Watch · {today:%d %b %Y} · ← → to move between tabs</div></div>')
with st.container(key="keys_box"):
    nav = getattr(KEYS(key="kz_keys", on_nav_change=lambda: None), "nav", None)
if nav:  # presenter arrows: must run before the tabs are drawn
    i = TABS.index(st.session_state.get("tab") or "Kanz")
    st.session_state["tab"] = TABS[max(0, min(len(TABS) - 1, i + (1 if nav == "next" else -1)))]
tab_kanz, tab_discover, tab_danger, tab_risk, tab_dive = st.tabs(TABS, key="tab", bind="query-params")



# ================================================================ 1. KANZ — why care?
with tab_kanz:
    if tab_kanz.open:
        red = story["red_sea"]
        first = top_risk.iloc[0]
        arrow = '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
        html(f"""
<section class="kz-hero">
  <div class="copy">
    <div class="label kz-in">Hawksbill turtle, Red Sea · critically endangered</div>
    <h1 class="kz-in d1">Find the ocean's hidden life before heat takes it</h1>
    <p class="sub kz-in d2">Where sea life is still unrecorded, which reefs today's heat will bleach,
    and where to dive or protect. Two machine-learning models on live NOAA data.</p>
    <div class="kz-actions kz-in d3">
      <a class="kz-btn primary" href="?tab=Discover" target="_self">Start the tour {arrow}</a>
      <a class="kz-btn ghost" href="?tab=At+risk" target="_self">See today's risk</a>
    </div>
  </div>
  <div class="kz-readout kz-in d4">
    <div class="top"><div class="t">Today on the world's reefs</div><div class="s">214 NOAA reef regions · {today:%d %b %Y}</div></div>
    <div class="cells">
      <div class="cell"><div class="k">Most treasure at risk</div><div class="v">{first['station']}</div>
        <div class="n">{snd(first['lat'], first['lon'])}</div></div>
      <div class="cell"><div class="k">Regions on bleaching alert</div><div class="v heat">{alert_today}<small> of {len(risk)}</small></div></div>
      <div class="cell"><div class="k">Jazan, Saudi Red Sea</div><div class="v heat">#{int(jazan['rank'])}<small> · DHW {jazan['dhw']:.1f}</small></div></div>
      <div class="cell"><div class="k">Predicted to bleach severely</div><div class="v heat">{severe_today}<small> of {len(risk)}</small></div></div>
    </div>
  </div>
</section>""")

        head("The ocean today", f"Every reef region on {today.day} {today:%B %Y}",
             "Live NOAA heat stress through our bleaching model, combined with our treasure map. "
             "Pick a reef and the globe flies there")
        fly = {"No. 1 at risk": first["station"], "Jazan": "Jazan, Saudi Arabia", "Caribbean": "Southwestern Cuba",
               "Florida Keys": "Florida Keys", "Maldives (calm)": "Maldives"}
        pick = st.pills("Fly to", list(fly), default="No. 1 at risk", key="fly", label_visibility="collapsed") or "No. 1 at risk"
        spot = risk.set_index("station").loc[fly[pick]]
        globe("risk", key="globe_kanz", height=720, points=risk_points(), rings=list(top_risk["station"].head(8)),
              focus=fly[pick], showFocus=True, legend=RISK_LEGEND, view={"lat": 18, "lon": 75, "alt": 2.2})
        html(f"""<div class="kz-card" style="margin-top:16px;padding:28px 32px">
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap">
    <div style="font-family:var(--serif);font-size:40px;line-height:1.1">{fly[pick]}</div>
    <div>{snd(spot['lat'], spot['lon'])} <span class="kz-snd">· rank #{int(spot['rank'])} of {len(risk)}</span></div>
  </div>
  <div class="kz-huge" style="margin-top:8px">
    {stat("Heat stress today", f"{spot['dhw']:.1f}<small> DHW</small>", "4+ bleaching likely · 8+ severe", tone="heat" if spot['dhw'] >= 4 else "life")}
    {stat("Chance of severe bleaching", f"{spot['severe_risk']:.0%}", "Model 2 on today's NOAA data", tone="heat" if spot['severe_risk'] >= .5 else "life")}
    {stat("Hidden species nearby", f"{spot['hidden_species']:,.0f}", "Model 1, species not yet recorded", tone="life")}
  </div>
</div>""".replace("kz-card kz-stat", "kz-stat"))

        head("The tour", "Five stops, one question each",
             "Click a stop, or press the right arrow to move on")
        chain = [("01", "Why should we care?", f"{story['seen_once']}% of known sea animals have been recorded only once", "Kanz"),
                 ("02", "Where is the treasure?", "Model 1 estimates the species nobody has recorded yet, cell by cell", "Discover"),
                 ("03", "What threatens it?", "Severe bleaching rises from 13% to 59% as heat stress builds. Model 2 predicts it", "Danger"),
                 ("04", "Where will we lose it first?", f"{alert_today} reef regions are on alert today. Both models together rank them", "At risk"),
                 ("05", "What can we do?", "Dive the healthy reefs, rest the overheating ones, protect the rare species", "Dive")]
        html('<div class="kz-chain">' + "".join(
            f'<a href="?tab={t.replace(" ", "+")}" target="_self"><span class="i">{i}</span><span class="q">{q}</span>'
            f'<span class="a">{a}</span><span class="go">{"You are here" if t == "Kanz" else f"Open {t} <span>→</span>"}</span></a>'
            for i, q, a, t in chain) + "</div>")
        next_button("Next: where is the treasure", "Discover")


# ================================================================ 2. DISCOVER — where is the treasure?
with tab_discover:
    if tab_discover.open:
        head("Model 1 · treasure map", "Where is the treasure?",
             "We split the ocean into 1,881 cells of 5° by 5°. A Random Forest learns how many species a cell holds from its "
             "depth, temperature and how much scientists searched it. Then we ask what each cell would hold if it were "
             "searched as well as the best ones. The difference is the life we have not found yet", first=True)

        cells = treasure.assign(lat=treasure["cell_lat"] + 2.5, lon=treasure["cell_lon"] + 2.5,
                                hidden=treasure["hidden_species"].clip(lower=0))
        col_map, col_list = st.columns([3, 2], gap="large")
        with col_map:
            pts = [{"lat": r.lat, "lon": r.lon, "h": round(float(r.hidden)), "r": int(r.obis_species),
                    "e": round(float(r.expected_species)), "t": None if pd.isna(r.sst_mean) else round(float(r.sst_mean), 1)} for r in cells.itertuples() if r.hidden > 0]
            globe("treasure", key="globe_treasure", height=600, points=pts, view={"lat": 5, "lon": 100, "alt": 2.6},
                  legend='<b>Hidden species per 5° cell</b><div class="k"><i style="background:#E6F4F7"></i>Taller and lighter: more life not yet recorded</div>'
                         '<div class="mono" style="margin-top:6px">Drag to turn · hover a column</div>')
        with col_list:
            html('<div class="kz-sub">Most hidden life, by cell</div>')
            top_cells = cells.sort_values("hidden", ascending=False).head(7)
            html('<div class="kz-rows">' + "".join(
                f'<div class="kz-row"><span class="i">{i + 1:02d}</span><div><div class="name">{snd(r.lat, r.lon).replace("kz-snd", "kz-snd kz-big")}</div>'
                f'<div class="meta">{int(r.obis_species):,} recorded · {int(r.expected_species):,} expected · {r.sst_mean:.0f} °C</div></div>'
                f'<div class="val accent">+{int(r.hidden):,}</div></div>'
                for i, r in enumerate(top_cells.itertuples())) + "</div>")
            warm = cells.loc[cells["sst_mean"] > 20, "hidden"].median()
            cold = cells.loc[cells["sst_mean"] < 10, "hidden"].median()
            html('<div class="kz-grid kz-g2" style="margin-top:20px">'
                 + stat("Warm cells, above 20 °C", f"{warm:,.0f}", "median hidden species")
                 + stat("Cold cells, below 10 °C", f"{cold:,.0f}", "median hidden species") + "</div>")

        head("Discovery", "Scientists still describe thousands of new sea animals every decade",
             f"Species described per decade, from OBIS. The 2020s are still in progress. {story['seen_once']}% of known species have been recorded only once")
        decade = story["per_decade"]
        latest = decade.index.max()
        fig = go.Figure(go.Bar(x=decade.index.astype(int), y=decade.values, marker_line_width=0,
                               marker_color=[ACCENT if d == latest - 10 else NEUTRAL_2 for d in decade.index],
                               hovertemplate="%{x}s · %{y:,} species<extra></extra>"))
        fig.update_xaxes(dtick=20, ticksuffix="s", showgrid=False)
        fig.update_yaxes(tickformat=",")
        fig.update_layout(bargap=.25)
        chart(fig, 320)

        head("The deep", "Dive from the reef to 6,000 metres",
             "Press dive, or scroll inside the window. The counter shows how many coral and sponge taxa NOAA has "
             "recorded deeper than you are. Almost everything below the reef is still barely explored")
        corals = story["corals"]
        photo = corals.dropna(subset=["ImageURL"]).drop_duplicates("ScientificName").set_index("ScientificName")
        creatures = [{"name": "Hawksbill turtle", "label": "coral reef", "m": 12, "src": "app/static/hero_turtle.jpg"},
                     {"name": "Whitetip reef sharks", "label": "coral reef", "m": 40, "src": "app/static/reef_sharks.jpg"}]
        creatures += [{"name": n, "label": f"recorded to {photo.loc[n, 'max_depth_m']:,.0f} m", "m": float(photo.loc[n, "max_depth_m"]),
                       "src": photo.loc[n, "ImageURL"]} for n in DIVE_PHOTOS if n in photo.index]
        creatures.sort(key=lambda c: c["m"])
        DIVE(key="dive", height="content", data={
            "depths": sorted(corals["max_depth_m"].dropna().astype(int).tolist()),
            "creatures": creatures,
            "notes": [{"m": 0, "html": "<b>Coral reefs live here, in the top 50 metres.</b> This is where the heat bleaches them, "
                                        "and where most of our survey data comes from"},
                      {"m": 200, "html": "Sunlight fades out. Corals that live here feed on what drifts down"},
                      {"m": 1000, "html": "No sunlight at all. Glass sponges and black corals grow here for centuries"},
                      {"m": 4000, "html": f"The abyssal plains. Only <b>{(corals['max_depth_m'] >= 4000).sum()}</b> coral and sponge taxa "
                                           "have ever been recorded this deep"}]})

        st.write("")
        with st.expander("How we know", icon=":material/science:"):
            res1 = out["res1"].rename(columns={"mean": "R² (unseen regions)", "std": "± std"})
            st.dataframe(res1.round(3), hide_index=True, width="stretch")
            st.markdown("* Tested on **whole ocean regions the model never saw** (30° blocks), so neighbouring cells cannot leak.\n"
                        "* **Sanity check:** in the best-searched cells, expected must be close to recorded. Ridge failed it, "
                        "because it keeps adding species forever. Random Forest passed.\n"
                        "* **Limit:** OBIS shows where scientists searched, so hidden species are an estimate, not a count.")
        next_button("Next: what threatens it", "Danger")


# ================================================================ 3. DANGER — what threatens it?
@st.fragment
def predictor():
    # runs on its own, so moving a slider only redraws this block
    model = load_bleaching_model()
    inputs = out["inputs"].merge(risk[["station", "sst", "sst_anomaly", "dhw", "max_monthly_mean_sst"]], on="station",
                                 suffixes=("", "_today"))
    names = sorted(inputs["station"])
    # opens on a reef that is calm today, so each degree of warming shows clearly; At risk can send any reef here
    focus = st.session_state.get("model_place", "Maldives")
    focus = focus if focus in names else "Maldives"
    col_in, col_out = st.columns([2, 3], gap="large")
    with col_in:
        place = st.selectbox("Reef region", names, index=names.index(focus))
        st.session_state["model_place"] = place
        row = inputs[inputs["station"] == place].iloc[0]
        dhw = st.slider("Heat stress now (DHW, °C-weeks)", 0.0, 25.0, float(round(row["dhw"] * 2) / 2), 0.5, key=f"dhw_{place}")
        presets = {"Today": 0.0, "+1 °C": 1.0, "+2 °C": 2.0, "+3 °C": 3.0}
        choice = st.segmented_control("Extra warming", list(presets), default="Today", key=f"warm_{place}",
                                    help="+1 °C adds 4 DHW: it assumes the extra warmth lasts about 4 weeks")
        warmer = presets[choice or "Today"]
        html(f'<div style="margin:8px 0 12px">{snd(row["lat"], row["lon"])}</div>'
             '<div class="kz-grid kz-g2">'
             + stat("Sea temperature", f"{row['sst'] + warmer:.1f}<small> °C</small>", f"today {row['sst']:.1f} °C")
             + stat("Heat stress used", f"{dhw + 4 * warmer:.1f}<small> DHW</small>", "4+ likely · 8+ severe") + "</div>")

    def features(heat_levels):
        # today's NOAA values + the place's site conditions (same 12 columns as training);
        # +1 °C of warming raises temperature, anomaly and TSA by 1 and heat stress by 4 DHW
        return pd.DataFrame([{
            "Temperature_Kelvin": row["sst"] + 273.15 + warmer, "SSTA": row["sst_anomaly"] + warmer,
            "TSA": row["sst"] - row["max_monthly_mean_sst"] + warmer, "SSTA_DHW": h, "TSA_DHW": h,
            "Date_Month": today.month, "ClimSST": row["ClimSST"], "Depth_m": row["Depth_m"],
            "Distance_to_Shore": row["Distance_to_Shore"], "Turbidity": row["Turbidity"],
            "Cyclone_Frequency": row["Cyclone_Frequency"], "Windspeed": row["Windspeed"]} for h in heat_levels])[model.feature_names_in_]

    used = dhw + 4 * warmer
    steps = np.arange(0, 28.5, .5)
    curve = model.predict_proba(features(steps))
    proba = model.predict_proba(features([used]))[0]
    with col_out:
        none, mild, severe = proba * 100
        note = ('<div class="what" style="font-size:16px;margin-top:16px;color:var(--muted)">This reef is already past 12 DHW, '
                "deep in the severe zone. Above that the model's answer levels off, so extra warming barely moves it</div>"
                if dhw >= 12 else "")
        html(f"""<div class="kz-card kz-pred">
  <div class="big {'calm' if severe < 30 else ''}">{severe:.0f}%</div>
  <div class="what">chance of severe bleaching at {place.split(',')[0]}, with {used:.1f} DHW of heat stress</div>
  <div class="kz-share"><div class="none" style="width:{none:.1f}%"></div><div class="mild" style="width:{mild:.1f}%"></div>
    <div class="severe" style="width:{severe:.1f}%"></div></div>
  <div class="kz-legend"><span><i style="background:#2F6D7A"></i>None {none:.0f}%</span><span><i style="background:#C99A5B"></i>Mild {mild:.0f}%</span>
    <span><i style="background:var(--heat)"></i>Severe {severe:.0f}%</span></div>
  {note}
</div>""")
        fig = go.Figure()
        fig.add_vrect(x0=8, x1=28, fillcolor="rgba(255,106,77,.07)", line_width=0)
        fig.add_scatter(x=steps, y=curve[:, 1] * 100, mode="lines", line=dict(color=NEUTRAL, width=1.5, shape="spline"),
                        name="Mild", hovertemplate="DHW %{x} · mild %{y:.0f}%<extra></extra>")
        fig.add_scatter(x=steps, y=curve[:, 2] * 100, mode="lines", line=dict(color=HEAT, width=2.5, shape="spline"),
                        name="Severe", hovertemplate="DHW %{x} · severe %{y:.0f}%<extra></extra>")
        fig.add_scatter(x=[min(used, 28)], y=[severe], mode="markers", marker=dict(size=14, color=HEAT, line=dict(width=3, color=CARD)),
                        hoverinfo="skip")
        fig.add_annotation(x=min(used, 28), y=severe, text="now", showarrow=False, yshift=16, font=dict(family="IBM Plex Mono", size=11, color=HEAT))
        fig.update_xaxes(title=dict(text="Heat stress (DHW)", font=dict(size=15, color=TEXT2)), dtick=4, range=[0, 28], showgrid=False)
        fig.update_yaxes(range=[0, 100], ticksuffix="%", dtick=25)
        fig.update_layout(title=dict(text=f"Severe bleaching risk at {place.split(',')[0]} as heat stress builds",
                                     font=dict(size=17, color=TEXT), x=.01, y=.97))
        chart(fig, 280, margin=dict(l=8, r=28, t=40, b=8))


with tab_danger:
    if tab_danger.open:
        html("""<section class="kz-band" style="background-image:url('app/static/bleaching.jpg')">
  <div class="label">Model 2 · bleaching risk</div>
  <h2>Heat is bleaching the reefs that hold the treasure</h2>
  <p>When the sea stays too warm, corals lose the algae that feed them and turn white. When the coral goes, the fish go too</p>
</section>""")

        col_a, col_b = st.columns(2, gap="large")
        hv, cf = story["heat_vs_bleach"], story["coral_vs_fish"]
        with col_a:
            head("The threat", "More heat, more severe bleaching")
            html(bars([(f"DHW {k}", v, "heat" if k == "8+" else "") for k, v in hv.items()], 70,
                      caption="Share of surveys with severe bleaching (20%+ of coral), by heat stress"))
        with col_b:
            head("Why it matters", "Less coral, fewer fish")
            html(bars([(f"Coral {k}", v, "accent" if k == "30–50%" else "") for k, v in cf.items()], 60, unit="",
                      caption="Average fish species seen per dive, by hard coral cover (Reef Life Survey)"))

        head("Try the model", "Will this reef bleach?",
             "Pick a real reef region. We load today's NOAA heat stress into the bleaching model, then you push the heat up")
        predictor()

        head("Watch it happen", "A year of heat on the world's reefs, in 20 seconds",
             "Press play. Every column is a NOAA reef region. Watch the heat move with the seasons, then settle on the Red Sea")
        heat = story["heat"]
        last_year = heat[heat["date"] >= heat["date"].max() - pd.Timedelta(days=364)]
        weekly = last_year[last_year["date"].dt.day_of_week == heat["date"].max().day_of_week]
        grid = weekly.pivot_table(index="date", columns="station", values="dhw").sort_index().ffill().fillna(0)
        places = heat.drop_duplicates("station").set_index("station").loc[grid.columns]
        globe("time", key="globe_time", height=640, view={"lat": 12, "lon": -20, "alt": 2.3}, spin=0.6, endView={"lat": 20, "lon": 40, "alt": 1.9},
              stations=[{"name": n, "lat": round(r.lat, 2), "lon": round(r.lon, 2)} for n, r in places.iterrows()],
              weeks=[d.strftime("%d %b %Y") for d in grid.index], dhw=grid.round(1).values.tolist(),
              legend='<b>A year of heat stress</b><div class="k"><i style="background:#FF6A4D"></i>Taller and redder: more heat stress</div>'
                     '<div class="k"><i style="border:1.5px solid #E88C6E;border-radius:50%"></i>Rings: 8+ DHW, severe bleaching likely</div>')

        with st.expander("How we know", icon=":material/science:"):
            res2 = out["res2"].rename(columns={"mean": "macro F1 (unseen sites)", "std": "± std"})
            st.dataframe(res2.round(3), hide_index=True, width="stretch")
            st.dataframe(out["future"].rename(columns={"Unnamed: 0": "model"}).round(3), hide_index=True, width="stretch")
            st.markdown("* Tested on **reef sites the model never saw** (GroupKFold by site). Random Forest: macro F1 0.70, "
                        "severe recall 0.72. The NOAA heat rule: 0.43 and 0.31.\n"
                        "* **12 current columns, not 38:** better on future years, and buildable from today's NOAA data.\n"
                        "* **Limit:** on future years the model catches fewer severe events (recall 0.27 vs 0.33 for the heat rule), "
                        "because the survey sources change after 2010.")
        next_button("Next: where will we lose it first", "At risk")


# ================================================================ 4. AT RISK — where first, and is there hope?
with tab_risk:
    if tab_risk.open:
        head("Both models together", "Where will we lose the treasure first?",
             "Treasure at risk combines how much hidden life an area holds (Model 1) with how likely its reefs are to bleach "
             "severely today (Model 2). High on both means we could lose species before anyone finds them. "
             "Click a region on the map to follow it", first=True)
        col_map, col_list = st.columns([3, 2], gap="large")
        with col_map:
            clicked = globe("risk", key="globe_risk", height=640, points=risk_points(), rings=list(top_risk["station"].head(8)),
                            focus=st.session_state["focus"], showFocus=True, clickable=True, flyOnStart=True,
                            legend=RISK_LEGEND.replace("Drag to turn the globe", "Click a column to follow that region"))
            if clicked and clicked != st.session_state["focus"]:
                st.session_state["focus"] = clicked
                st.rerun(scope="app")
        focus = st.session_state["focus"] if st.session_state["focus"] in set(risk["station"]) else "Jazan, Saudi Arabia"
        f = risk.set_index("station").loc[focus]
        with col_list:
            html('<div class="kz-sub">Top 8 today</div>')
            html('<div class="kz-rows">' + "".join(
                f'<div class="kz-row {"on" if r["station"] == focus else ""}"><span class="i">{int(r["rank"]):02d}</span>'
                f'<div><div class="name">{r["station"]}</div><div class="meta">DHW {r["dhw"]:.1f} · severe risk {r["severe_risk"]:.0%} · '
                f'{snd(r["lat"], r["lon"])}</div></div><div class="val heat">{r["treasure_at_risk"]:.0f}</div></div>'
                for _, r in top_risk.head(8).iterrows()) + "</div>")
            html(f"""<div class="kz-card" style="margin-top:20px">
  <div style="font-size:13px;color:var(--text-2)">Following</div>
  <div style="font-family:var(--serif);font-size:28px;line-height:1.15;margin:4px 0 2px">{focus}</div>{snd(f['lat'], f['lon'])}
  <div class="kz-grid kz-g3" style="margin-top:16px;gap:12px">
    <div class="kz-stat"><div class="k">Rank</div><div class="v" style="font-size:24px">#{int(f['rank'])}</div></div>
    <div class="kz-stat"><div class="k">DHW</div><div class="v {'heat' if f['dhw'] >= 8 else ''}" style="font-size:24px">{f['dhw']:.1f}</div></div>
    <div class="kz-stat"><div class="k">Severe risk</div><div class="v {'heat' if f['severe_risk'] >= .5 else ''}" style="font-size:24px">{f['severe_risk']:.0%}</div></div>
  </div>
</div>""")
            st.button(f"Test {focus.split(',')[0]} in the model  →", on_click=send_to_model, args=(focus,), key="test_focus", width="stretch")

        head("Spotlight · Saudi Red Sea", "Jazan is overheating, and Red Sea corals are holding on")
        col_photo, col_text = st.columns([5, 6], gap="large")
        with col_photo:
            html('<div class="kz-photo"><img src="app/static/red_sea_reef.jpg" alt="Soft corals and anthias on a Red Sea reef"></div>')
        with col_text:
            red = story["red_sea"]
            html(f'<p style="font-size:17px;color:var(--text-2);margin:0 0 24px;max-width:36rem">Jazan ranks '
                 f'#{int(jazan["rank"])} of 214 today, the first in Saudi waters. Yet under the same strong heat, only '
                 f'{red["Red Sea"]}% of Red Sea reefs bleached severely, against {red["Rest of the world"]}% in the rest of the world. '
                 f'The Red Sea may be a refuge for the world\'s corals.</p>')
            html('<div class="kz-grid kz-g3">' + "".join(
                stat(s.split(",")[0].replace("Al Madinah and Makkah", "Makkah coast"), f"{saudi.loc[s, 'dhw']:.1f}<small> DHW</small>",
                     f"#{int(saudi.loc[s, 'rank'])} of 214", heat=saudi.loc[s, "dhw"] >= 8) for s in SAUDI) + "</div>")
            html('<div class="kz-card" style="margin-top:16px">'
                 + bars([("Red Sea", red["Red Sea"], "accent"), ("Elsewhere", red["Rest of the world"], "")], 70,
                        caption="Severe bleaching in surveys with strong heat stress (DHW 4+)") + "</div>")

        head("Saudi waters", "Two years of heat on our coast",
             "Daily heat stress for the three Saudi reef regions. Above 4, bleaching is likely. Above 8, severe bleaching is likely")
        saudi_heat = story["heat"][story["heat"]["station"].isin(SAUDI)]
        fig = go.Figure()
        for s, color, width in [("Tabuk, Saudi Arabia", "#4E6C77", 2), ("Al Madinah and Makkah", "#86A2A9", 2), ("Jazan, Saudi Arabia", HEAT, 3.5)]:
            d = saudi_heat[saudi_heat["station"] == s]
            fig.add_scatter(x=d["date"], y=d["dhw"], mode="lines", line=dict(color=color, width=width, shape="spline", smoothing=.6),
                            name=s.split(",")[0], hovertemplate=f"{s.split(',')[0]} · %{{x|%d %b %Y}} · DHW %{{y:.1f}}<extra></extra>")
            fig.add_annotation(x=d["date"].iloc[-1], y=d["dhw"].iloc[-1], text=s.split(",")[0].replace("Al Madinah and Makkah", "Makkah"),
                               showarrow=False, xanchor="left", xshift=8, font=dict(size=15, color=color))
        for level in (4, 8):
            fig.add_hline(y=level, line_dash="dot", line_color="rgba(31,27,22,.25)", line_width=1)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(title=dict(text="DHW", font=dict(size=15, color=TEXT2)))
        chart(fig, 380, margin=dict(l=8, r=72, t=16, b=8))

        with st.expander("How we know", icon=":material/science:"):
            st.markdown(f"* **Risk today** feeds each NOAA region's latest day ({today:%d %b %Y}) into Model 2. Site conditions come "
                        "from bleaching surveys within 300 km (179 of 214 regions), otherwise the world median.\n"
                        "* **Treasure at risk** multiplies two ranks (percentiles), so a place must be high on both.\n"
                        "* **Limits:** NOAA's daily DHW is computed a little differently from the training data, so today's risk "
                        "is an estimate. The Red Sea comparison rests mostly on northern Red Sea surveys.")
        next_button("Next: what can we do", "Dive")


# ================================================================ 5. DIVE — what can we do?
with tab_dive:
    if tab_dive.open:
        html("""<section class="kz-band" style="background-image:url('app/static/reef_sharks.jpg')">
  <div class="label">Reef health index · 2,648 dive sites</div>
  <h2>Dive where reefs thrive, rest the ones that overheat</h2>
  <p>Each site is scored on fish, coral, visibility, today's bleaching risk and past bleaching. Change what matters to you</p>
</section>""")

        st.write("")
        with st.expander("Tune the reef health index", icon=":material/tune:", expanded=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            weights = {"s_fish": c1.slider("Fish species", 0.0, 1.0, step=0.05, key="w_fish"),
                       "s_coral": c2.slider("Hard coral", 0.0, 1.0, step=0.05, key="w_coral"),
                       "s_visibility": c3.slider("Visibility", 0.0, 1.0, step=0.05, key="w_vis"),
                       "s_low_risk": c4.slider("Low risk today", 0.0, 1.0, step=0.05, key="w_risk"),
                       "s_low_bleach": c5.slider("Low past bleaching", 0.0, 1.0, step=0.05, key="w_bleach")}
            f1, f2, f3 = st.columns([2, 1, 1], vertical_alignment="bottom")
            countries = f1.multiselect("Countries", sorted(dive["country"].dropna().unique()), placeholder="All countries", key="countries")
            min_fish = f2.slider("Minimum fish species", 0, 100, step=5, key="min_fish")
            only_cr = f3.toggle("Critically endangered nearby", key="only_cr")

        total = sum(weights.values()) or 1
        sites = dive.assign(score=sum(dive[c] * w for c, w in weights.items()) / total)
        if countries:
            sites = sites[sites["country"].isin(countries)]
        sites = sites[sites["fish_species"] >= min_fish]
        if only_cr:
            sites = sites[sites["CR"] > 0]
        sites = sites.sort_values("score", ascending=False)

        head("Where to dive", "The healthiest reefs for your settings",
             f"{len(sites):,} sites match. The map shows the top 400. Click a site to see who lives near it")
        col_map, col_cards = st.columns([3, 2], gap="large")
        with col_map:
            fig = px.scatter_geo(sites.head(400), lat="latitude", lon="longitude", color="score", hover_name="site_name",
                                 color_continuous_scale=WATER_SCALE, range_color=[30, 90], custom_data=["site_code"],
                                 hover_data={"latitude": False, "longitude": False, "country": True, "fish_species": ":.0f", "score": ":.0f"},
                                 labels={"score": "Health", "fish_species": "Fish species", "country": "Country"})
            fig.update_traces(marker=dict(size=9, line=dict(width=0)))
            style_map(fig, bar_title="Reef health index")
            clicked_site = picked(chart(fig, 520, key="dive_map", select=True))
        with col_cards:
            html('<div class="kz-sub">Top 5</div><div class="kz-rows">' + "".join(
                f'<div class="kz-site"><div class="top"><div class="name">{r["site_name"]}</div>'
                f'<div class="score">{r["score"]:.0f}</div></div>'
                f'<div class="meta">{r["country"]} · {r["fish_species"]:.0f} fish species · {r["visibility"]:.0f} m visibility · '
                f'{snd(r["latitude"], r["longitude"])}</div>'
                f'<div class="track"><div style="width:{r["score"]:.0f}%"></div></div>'
                + "".join(f'<span class="kz-tag {k.lower()}"><b>{k}</b>{int(r[k])}</span>' for k in ["CR", "EN", "VU"] if r[k] > 0)
                + "</div>" for _, r in sites.head(5).iterrows()) + "</div>")

        head("Rare creatures", "Who lives near your dive?",
             "IUCN threatened species recorded within about 25 km of a site. We checked the top 150 sites")
        threatened = story["threatened"]
        checked = sites[sites["site_code"].isin(threatened["site_code"])]
        if clicked_site and clicked_site not in set(threatened["site_code"]):
            st.caption("That site is outside the 150 we checked for threatened species. Pick one of the checked sites below")
        if len(checked) == 0:
            st.info("None of the matching sites were in the 150 checked for threatened species. Widen the filters")
        else:
            labels = dict(zip(checked["site_code"], checked["site_name"] + " · " + checked["country"]))
            codes = list(labels)
            start = codes.index(clicked_site) if clicked_site in labels else 0
            code = st.selectbox("Dive site", codes, index=start, format_func=labels.get, key=f"site_{start}")
            near = threatened[threatened["site_code"] == code]
            counts = near["category"].value_counts()
            col_a, col_b = st.columns([1, 2], gap="large")
            with col_a:
                html('<div class="kz-grid">'
                     + stat("Critically endangered", int(counts.get("CR", 0)), "IUCN CR", heat=True)
                     + stat("Endangered", int(counts.get("EN", 0)), "IUCN EN")
                     + stat("Vulnerable", int(counts.get("VU", 0)), "IUCN VU") + "</div>")
            with col_b:
                order = {"CR": 0, "EN": 1, "VU": 2}
                near = near.sort_values("category", key=lambda s: s.map(order))
                html('<div class="kz-card">' + "".join(
                    f'<span class="kz-tag {c.lower()}"><b>{c}</b><i>{s}</i></span>'
                    for s, c in zip(near["species"].head(48), near["category"].head(48))) + "</div>")

        head("Who it is for", "One map, three kinds of user")
        users = [("Divers and travellers", "Free", "The healthiest reefs to dive today, and the rare animals you might meet there"),
                 ("Dive operators and eco-tourism", "Paid dashboard", "Which sites to promote, and which to rest while they overheat"),
                 ("Researchers and conservation", "Priority list", "Places rich in hidden life that are under heat stress today")]
        html('<div class="kz-users">' + "".join(
            f'<div><div class="k">{k}</div><h3>{t}</h3><p>{d}</p></div>' for t, k, d in users) + "</div>")

        st.write("")
        with st.expander("How we know", icon=":material/science:"):
            equal = sum(dive[c] for c in weights) / len(weights)
            default = (dive["s_fish"] * .30 + dive["s_coral"] * .25 + dive["s_visibility"] * .15 + dive["s_low_risk"] * .15 + dive["s_low_bleach"] * .15)
            st.markdown(f"* **A score, not a model:** there is no 'good dive site' label to learn from, so the index is a clear "
                        f"weighted average of percentiles (0–100). Missing values count as neutral (50).\n"
                        f"* **Stable:** equal weights vs our default weights give a Spearman correlation of "
                        f"{default.corr(equal, method='spearman'):.2f}, so the ranking does not hang on our exact choice.\n"
                        f"* Sites need 3 or more dives, so one lucky dive cannot win.")

# ---------------------------------------------------------------- footer (credits, one line)
credits = json.loads((APP / "static" / "credits.json").read_text(encoding="utf-8"))
photo_line = " · ".join(f'{c["author"].split(" from ")[0]} ({c["license"]})' for c in credits.values())
html(f'<div class="kz-foot">Kanz · Machine Learning project, Tuwaiq Academy · Data: OBIS, Global Coral Bleaching Database, '
     f'NOAA Coral Reef Watch, Reef Life Survey / IMOS, NOAA Deep-Sea Coral &amp; Sponge Database, Our World in Data · '
     f'Photos via Wikimedia Commons: {photo_line}; deep-sea photos NOAA</div>')
