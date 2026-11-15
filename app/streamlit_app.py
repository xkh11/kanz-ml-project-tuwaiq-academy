"""Kanz | كنز — find the ocean's hidden life before heat takes it.

Run from the project folder:
    streamlit run app/streamlit_app.py

A 3-minute demo, three screens:
  1. Treasure  where unknown sea life is hiding
  2. Risk      which reefs heat will bleach (try it, then the world map)
  3. Act       where to dive, and who lives there

Heat data is the saved NOAA Coral Reef Watch file (outputs/risk_today.csv); its date is shown in the header.
Header videos: put hero_turtle.mp4, bleaching.mp4, reef_sharks.mp4 in app/static. Missing ones fall back to the photo.
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
STATIC = APP / "static"

st.set_page_config(page_title="Kanz | كنز", page_icon=":material/water:", layout="wide")

# colours (same tokens as style.css)
TEXT, TEXT2, MUTED, LINE = "#EEF6F6", "#B4C9CD", "#86A2A9", "rgba(238,246,246,.08)"
ACCENT, HEAT, NEUTRAL, CARD = "#34D5C4", "#FF6A4D", "#4E6C77", "#0B2535"
WATER_SCALE = ["#1B4A5C", "#1E6F82", "#2399A3", "#34D5C4", "#8FF0E4", "#E8FFFB"]
TABS = ["Treasure", "Risk", "Act"]
JAZAN = "Jazan, Saudi Arabia"
SAUDI = ["Jazan, Saudi Arabia", "Al Madinah and Makkah", "Tabuk, Saudi Arabia"]
# one clean photo per depth band for the deep-sea dive (checked by eye, no text burned into the frame)
DIVE_PHOTOS = ["Coenocyathus bowersi", "Errinopora", "Spirastrellidae", "Trissopathes pseudotristicha", "Desmophyllum dianthus",
               "Farrea occa", "Primnoidae", "Hyalostylus", "Porifera", "Umbellula"]


# ---------------------------------------------------------------- data (loaded once per server)
@st.cache_data(show_spinner=False)
def load_outputs():
    risk = pd.read_csv(OUT / "risk_today.csv", parse_dates=["date"])
    return {"treasure": pd.read_csv(OUT / "treasure_map.csv"), "risk": risk,
            "dive": pd.read_csv(OUT / "dive_finder.csv"), "inputs": pd.read_csv(OUT / "station_inputs.csv")}


@st.cache_data(show_spinner=False)
def load_facts():
    # two numbers for the story: sea animals seen only once, and the Red Sea under strong heat
    animals = pd.read_csv(DATA / "obis_marine_animal_species.csv.gz", low_memory=False)
    species = animals[animals["taxonRank"] == "Species"]
    seen_once = round((species["records"] == 1).mean() * 100, 1)
    year = species["scientificNameAuthorship"].str.extract(r"(1[789]\d\d|20\d\d)")[0].astype(float)
    per_decade = (year // 10 * 10).value_counts().sort_index()
    per_decade = per_decade[per_decade.index >= 1750]

    bleaching = pd.read_csv(DATA / "coral_bleaching_surveys.csv.gz", na_values=["nd"], low_memory=False)
    samples = bleaching[bleaching["Percent_Bleaching"].notna()].drop_duplicates("Sample_ID")
    severe = samples["Percent_Bleaching"] >= 20
    hot = samples["TSA_DHW"] >= 4
    red = samples["Ecoregion_Name"].str.contains("Red Sea|Gulf of Aden", na=False)
    heat_groups = pd.cut(samples["TSA_DHW"], [-0.1, 0, 2, 4, 8, 100], labels=["0", "0–2", "2–4", "4–8", "8+"])
    heat_vs_bleach = (severe.groupby(heat_groups, observed=True).mean() * 100).round(1)

    # coral -> fish (Reef Life Survey)
    surveys = pd.read_csv(DATA / "reef_life_surveys.csv")
    coral_groups = pd.cut(surveys["hard_coral_pct"], [-0.1, 0, 10, 30, 50, 100], labels=["0%", "0–10%", "10–30%", "30–50%", "50%+"])
    coral_vs_fish = surveys.groupby(coral_groups, observed=True)["fish_species"].mean().round(1)

    # daily heat stress on the Saudi coast (saved NOAA history)
    heat = pd.read_csv(DATA / "noaa_reef_heat_stress_daily.csv.gz")
    heat = heat[heat["station"].isin(SAUDI)].assign(date=lambda d: pd.to_datetime(d[["year", "month", "day"]]))

    return {"seen_once": seen_once, "per_decade": per_decade, "red_sea": round(severe[hot & red].mean() * 100),
            "elsewhere": round(severe[hot & ~red].mean() * 100),
            "heat_vs_bleach": heat_vs_bleach, "coral_vs_fish": coral_vs_fish, "saudi_heat": heat,
            "corals": pd.read_csv(DATA / "deep_sea_corals_species.csv"),
            "threatened": pd.read_csv(DATA / "threatened_species_near_dive_sites.csv")}


@st.cache_resource(show_spinner=False)
def load_bleaching_model():
    return joblib.load(ROOT / "models" / "model2_bleaching_risk.joblib")


# ---------------------------------------------------------------- small helpers
def html(text):
    st.markdown(text, unsafe_allow_html=True)


def snd(lat, lon):
    # a place's coordinates, written like a sounding on a chart
    return f'<span class="kz-snd">{abs(lat):.1f}°{"N" if lat >= 0 else "S"} {abs(lon):.1f}°{"E" if lon >= 0 else "W"}</span>'


def head(label, title, text=""):
    html(f'<div class="kz-head"><div class="label">{label}</div><h2>{title}</h2>' + (f"<p>{text}</p>" if text else "") + "</div>")


def sub(text):
    html(f'<div class="kz-sub">{text}</div>')


def stat(label, value, note="", tone=""):
    return (f'<div class="kz-card kz-stat"><div class="k">{label}</div><div class="v {tone}">{value}</div>'
            + (f'<div class="c">{note}</div>' if note else "") + "</div>")


def bars(rows, top, unit="%", caption=""):
    # an evidence chart drawn as a list with thin bars; only the row that matters gets colour
    out = '<div class="kz-bars">'
    for label, value, tone in rows:
        out += (f'<div class="r"><div class="lab">{label}</div><div class="track"><div class="fill {tone}" '
                f'style="width:{value / top * 100:.1f}%"></div></div><div class="num">{value:.0f}{unit}</div></div>')
    return out + (f'<div class="cap">{caption}</div>' if caption else "") + "</div>"


def media(name):
    # a muted looping video if app/static/<name>.mp4 exists, otherwise the photo
    if (STATIC / f"{name}.mp4").exists():
        return (f'<video class="kz-media" src="app/static/{name}.mp4" poster="app/static/{name}.jpg" '
                'autoplay muted loop playsinline></video>')
    return f'<img class="kz-media" src="app/static/{name}.jpg" alt="">'


def band(name, label, title, text=""):
    html(f'<section class="kz-band">{media(name)}<div class="label">{label}</div><h2>{title}</h2>'
         + (f"<p>{text}</p>" if text else "") + "</section>")


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


def picked(event, field=0):
    # the first clicked point's custom data, or None
    try:
        points = event.selection["points"]
        return points[0]["customdata"][field] if points else None
    except (AttributeError, KeyError, IndexError, TypeError):
        return None


# ---------------------------------------------------------------- custom pieces (app/components): globe, presenter keys
def _part(name):
    return (APP / "components" / name).read_text(encoding="utf-8")


GLOBE = st.components.v2.component("kanz_globe", js=_part("globe.js"), css=_part("globe.css"))
KEYS = st.components.v2.component("kanz_keys", js=_part("keys.js"))
DIVE = st.components.v2.component("kanz_dive", js=_part("dive.js"), css=_part("dive.css"))


def globe(mode, key, height=560, **data):
    GLOBE(key=key, data={"mode": mode, "height": height, **data}, height=height, on_picked_change=lambda: None)


# ---------------------------------------------------------------- page
html(f"<style>{(APP / 'style.css').read_text(encoding='utf-8')}</style>")
# demo layout: shorter headers, tighter sections, photo or video behind the header text
html("""<style>
.kz-hero { height: 440px; min-height: 0; max-height: none; background: #062A50; isolation: isolate; }
.kz-hero .copy { padding: 56px 64px 0; }
.kz-hero h1 { font-size: 68px !important; }
.kz-band { height: 300px; background: #062A50; isolation: isolate; }
.kz-media { position: absolute !important; inset: 0; width: 100%; height: 100%; max-width: none !important;
  object-fit: cover !important; z-index: -1; margin: 0 !important; }
.kz-hero .kz-media { object-position: 62% center !important; }
.kz-hero::before, .kz-band::before { z-index: 0; }
.kz-hero .copy, .kz-band > :not(.kz-media) { z-index: 1; }
.kz-head { margin: 56px 0 24px; }
.kz-callout { border-left: 3px solid var(--life); }
.kz-callout p { font-size: 17px; color: var(--text-2); margin: 10px 0 0; line-height: 1.5; }
@media (max-width: 760px) { .kz-hero { height: auto; } .kz-hero h1 { font-size: 42px !important; } .kz-band { height: 240px; } }
</style>""")

out = load_outputs()
facts = load_facts()
risk, treasure, dive = out["risk"], out["treasure"], out["dive"]
day = risk["date"].max()                       # NOAA's day in the saved data
top_risk = risk.sort_values("treasure_at_risk", ascending=False)
jazan = risk.set_index("station").loc[JAZAN]

html(f'<div class="kz-brand"><div class="mark">Kanz<span>كنز</span></div>'
     f'<div class="meta">NOAA Coral Reef Watch · {day:%d %b %Y}</div></div>')
with st.container(key="keys_box"):
    nav = getattr(KEYS(key="kz_keys", on_nav_change=lambda: None), "nav", None)
if nav:  # presenter arrows: must run before the tabs are drawn
    i = TABS.index(st.session_state.get("tab") or TABS[0])
    st.session_state["tab"] = TABS[max(0, min(len(TABS) - 1, i + (1 if nav == "next" else -1)))]
tab_treasure, tab_risk, tab_act = st.tabs(TABS, key="tab", bind="query-params")


# ================================================================ 1. TREASURE — where is unknown sea life hiding?
with tab_treasure:
    if tab_treasure.open:
        html(f"""<section class="kz-hero">{media("hero_turtle")}
  <div class="copy">
    <div class="label kz-in">Hawksbill turtle · critically endangered</div>
    <h1 class="kz-in d1">Find the ocean's hidden life before heat takes it</h1>
    <p class="sub kz-in d2">{facts['seen_once']}% of known sea animals have been seen only once.
    Most sea life is still unrecorded. Here is where it hides.</p>
  </div>
</section>""")

        head("Treasure map", "Where is the treasure?",
             "Each column is a patch of ocean. Its height is the sea life that likely lives there but nobody has recorded yet")
        cells = treasure.assign(lat=treasure["cell_lat"] + 2.5, lon=treasure["cell_lon"] + 2.5,
                                hidden=treasure["hidden_species"].clip(lower=0))
        col_map, col_list = st.columns([3, 2], gap="large")
        with col_map:
            pts = [{"lat": r.lat, "lon": r.lon, "h": round(float(r.hidden)), "r": int(r.obis_species),
                    "e": round(float(r.expected_species)), "t": None if pd.isna(r.sst_mean) else round(float(r.sst_mean), 1)}
                   for r in cells.itertuples() if r.hidden > 0]
            globe("treasure", key="globe_treasure", height=560, points=pts, view={"lat": 5, "lon": 100, "alt": 2.6},
                  legend='<b>Hidden species per cell</b><div class="k"><i style="background:#E6F4F7"></i>Taller: more unrecorded life</div>')
        with col_list:
            sub("Most hidden life")
            top_cells = cells.sort_values("hidden", ascending=False).head(5)
            html('<div class="kz-rows">' + "".join(
                f'<div class="kz-row"><span class="i">{i + 1:02d}</span><div><div class="name">{snd(r.lat, r.lon).replace("kz-snd", "kz-snd kz-big")}</div>'
                f'<div class="meta">{int(r.obis_species):,} recorded · {int(r.expected_species):,} expected</div></div>'
                f'<div class="val accent">+{int(r.hidden):,}</div></div>'
                for i, r in enumerate(top_cells.itertuples())) + "</div>")
            warm = cells.loc[cells["sst_mean"] > 20, "hidden"].median()
            cold = cells.loc[cells["sst_mean"] < 10, "hidden"].median()
            st.caption(f"Warm seas hide the most: a median of {warm:,.0f} unrecorded species per cell above 20 °C, "
                       f"{cold:,.0f} below 10 °C. Warm seas are also where reefs bleach")

        head("Discovery", "Scientists still describe thousands of new sea animals every decade",
             "Species described per decade, from OBIS. The 2020s are still in progress")
        decade = facts["per_decade"]
        latest = decade.index.max()
        fig = go.Figure(go.Bar(x=decade.index.astype(int), y=decade.values, marker_line_width=0,
                               marker_color=[ACCENT if d == latest - 10 else "#24485A" for d in decade.index],
                               hovertemplate="%{x}s · %{y:,} species<extra></extra>"))
        fig.update_xaxes(dtick=20, ticksuffix="s", showgrid=False)
        fig.update_yaxes(tickformat=",")
        fig.update_layout(bargap=.25)
        chart(fig, 300)

        head("The deep", "Dive from the reef to 6,000 metres",
             "Press dive. The counter shows how many coral and sponge species live deeper than you. "
             "Almost everything below the reef is still barely explored")
        corals = facts["corals"]
        photo = corals.dropna(subset=["ImageURL"]).drop_duplicates("ScientificName").set_index("ScientificName")
        creatures = [{"name": "Hawksbill turtle", "label": "coral reef", "m": 12, "src": "app/static/hero_turtle.jpg"},
                     {"name": "Whitetip reef sharks", "label": "coral reef", "m": 40, "src": "app/static/reef_sharks.jpg"}]
        creatures += [{"name": n, "label": f"recorded to {photo.loc[n, 'max_depth_m']:,.0f} m", "m": float(photo.loc[n, "max_depth_m"]),
                       "src": photo.loc[n, "ImageURL"]} for n in DIVE_PHOTOS if n in photo.index]
        creatures.sort(key=lambda c: c["m"])
        DIVE(key="dive", height="content", data={
            "depths": sorted(corals["max_depth_m"].dropna().astype(int).tolist()),
            "creatures": creatures,
            "notes": [{"m": 0, "html": "<b>Coral reefs live in the top 50 metres.</b> This is where the heat bleaches them"},
                      {"m": 200, "html": "Sunlight fades out. Corals that live here feed on what drifts down"},
                      {"m": 1000, "html": "No sunlight at all. Glass sponges and black corals grow here for centuries"},
                      {"m": 4000, "html": f"The abyssal plains. Only <b>{(corals['max_depth_m'] >= 4000).sum()}</b> coral and sponge "
                                           "species have ever been recorded this deep"}]})


# ================================================================ 2. RISK — which reefs will heat bleach?
@st.fragment
def predictor():
    # runs on its own, so moving a slider only redraws this block
    model = load_bleaching_model()
    inputs = out["inputs"].merge(risk[["station", "sst", "sst_anomaly", "dhw"]], on="station")
    names = sorted(inputs["station"])
    # opens on a calm reef, so each degree of warming shows clearly
    col_in, col_out = st.columns([2, 3], gap="large")
    with col_in:
        place = st.selectbox("Reef region", names, index=names.index("Maldives"))
        row = inputs[inputs["station"] == place].iloc[0]
        dhw = st.slider("Heat stress (DHW, °C-weeks)", 0.0, 25.0, float(round(row["dhw"] * 2) / 2), 0.5, key=f"dhw_{place}")
        presets = {"Now": 0.0, "+1 °C": 1.0, "+2 °C": 2.0, "+3 °C": 3.0}
        choice = st.segmented_control("Extra warming", list(presets), default="Now", key=f"warm_{place}",
                                      help="+1 °C adds 4 DHW: it assumes the extra warmth lasts about 4 weeks")
        warmer = presets[choice or "Now"]
        st.caption(f"Sea {row['sst'] + warmer:.1f} °C · heat stress {dhw + 4 * warmer:.1f} DHW · 4+ bleaching likely, 8+ severe")

    def features(heat_levels):
        # NOAA values for the place + its site conditions (same 12 columns as training);
        # +1 °C of warming raises temperature, anomaly and TSA by 1 and heat stress by 4 DHW
        return pd.DataFrame([{
            "Temperature_Kelvin": row["sst"] + 273.15 + warmer, "SSTA": row["sst_anomaly"] + warmer,
            "TSA": row["sst"] - row["max_monthly_mean_sst"] + warmer, "SSTA_DHW": h, "TSA_DHW": h,
            "Date_Month": day.month, "ClimSST": row["ClimSST"], "Depth_m": row["Depth_m"],
            "Distance_to_Shore": row["Distance_to_Shore"], "Turbidity": row["Turbidity"],
            "Cyclone_Frequency": row["Cyclone_Frequency"], "Windspeed": row["Windspeed"]} for h in heat_levels])[model.feature_names_in_]

    used = dhw + 4 * warmer
    steps = np.arange(0, 28.5, .5)
    curve = model.predict_proba(features(steps))
    none, mild, severe = model.predict_proba(features([used]))[0] * 100
    with col_out:
        html(f"""<div class="kz-card kz-pred">
  <div class="big {'calm' if severe < 30 else ''}">{severe:.0f}%</div>
  <div class="what">chance of severe bleaching at {place.split(',')[0]}</div>
  <div class="kz-share"><div class="none" style="width:{none:.1f}%"></div><div class="mild" style="width:{mild:.1f}%"></div>
    <div class="severe" style="width:{severe:.1f}%"></div></div>
  <div class="kz-legend"><span><i style="background:#2F6D7A"></i>None {none:.0f}%</span><span><i style="background:#C99A5B"></i>Mild {mild:.0f}%</span>
    <span><i style="background:var(--heat)"></i>Severe {severe:.0f}%</span></div>
</div>""")
        fig = go.Figure()
        fig.add_vrect(x0=8, x1=28, fillcolor="rgba(255,106,77,.07)", line_width=0)
        fig.add_scatter(x=steps, y=curve[:, 1] * 100, mode="lines", line=dict(color=NEUTRAL, width=1.5, shape="spline"),
                        hovertemplate="DHW %{x} · mild %{y:.0f}%<extra></extra>")
        fig.add_scatter(x=steps, y=curve[:, 2] * 100, mode="lines", line=dict(color=HEAT, width=2.5, shape="spline"),
                        hovertemplate="DHW %{x} · severe %{y:.0f}%<extra></extra>")
        fig.add_scatter(x=[min(used, 28)], y=[severe], mode="markers", marker=dict(size=14, color=HEAT, line=dict(width=3, color=CARD)),
                        hoverinfo="skip")
        fig.update_xaxes(title=dict(text="Heat stress (DHW)", font=dict(size=15, color=TEXT2)), dtick=4, range=[0, 28], showgrid=False)
        fig.update_yaxes(range=[0, 100], ticksuffix="%", dtick=25)
        chart(fig, 220, margin=dict(l=8, r=28, t=12, b=8))


with tab_risk:
    if tab_risk.open:
        band("bleaching", f"Bleaching risk · NOAA {day:%d %b %Y}", "Heat is bleaching the reefs that hold the treasure",
             "Too warm for too long, and corals turn white. When the coral goes, the fish go too")
        html('<div class="kz-grid kz-g3" style="margin-top:16px">'
             + stat("On bleaching alert", f"{int((risk['dhw'] >= 4).sum())}<small> of {len(risk)} reef regions</small>", tone="heat")
             + stat("Likely to bleach severely", f"{int((risk['risk_class'] == 2).sum())}<small> of {len(risk)}</small>", tone="heat")
             + stat("Jazan, Saudi Red Sea", f"#{int(jazan['rank'])}<small> most at risk</small>", tone="heat") + "</div>")

        head("Why it matters", "More heat, more bleaching. Less coral, fewer fish")
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            html(bars([(f"DHW {k}", v, "heat" if k == "8+" else "") for k, v in facts["heat_vs_bleach"].items()], 70,
                      caption="Surveys with severe bleaching (20%+ of coral), by heat stress"))
        with col_b:
            html(bars([(f"Coral {k}", v, "accent" if k == "30–50%" else "") for k, v in facts["coral_vs_fish"].items()], 60, unit="",
                      caption="Fish species seen per dive, by hard coral cover (Reef Life Survey)"))

        head("Try it", "Will this reef bleach?", "Pick a reef, then push the heat up")
        predictor()

        head("Treasure at risk", "Where will we lose the treasure first?",
             "Rich in hidden life and likely to bleach severely. Colour is heat stress, height is treasure at risk")
        col_map, col_list = st.columns([3, 2], gap="large")
        with col_map:
            globe("risk", key="globe_risk", height=560, rings=list(top_risk["station"].head(8)), focus=JAZAN, showFocus=True,
                  flyOnStart=True, points=[{"name": r.station, "lat": round(r.lat, 2), "lon": round(r.lon, 2),
                                            "dhw": round(float(r.dhw), 1), "v": round(float(r.treasure_at_risk), 1),
                                            "risk": round(float(r.severe_risk), 3), "rank": int(r.rank)} for r in risk.itertuples()],
                  legend='<b>214 reef regions</b><div class="k"><i style="background:#FF6A4D"></i>Colour: heat stress</div>'
                         '<div class="k"><i style="background:#EEF6F6;width:3px;height:12px"></i>Height: treasure at risk</div>')
        with col_list:
            sub("Top 5")
            html('<div class="kz-rows">' + "".join(
                f'<div class="kz-row {"on" if r.station == JAZAN else ""}"><span class="i">{int(r.rank):02d}</span>'
                f'<div><div class="name">{r.station}</div><div class="meta">DHW {r.dhw:.1f} · severe {r.severe_risk:.0%}</div></div>'
                f'<div class="val heat">{r.treasure_at_risk:.0f}</div></div>'
                for r in top_risk.head(5).itertuples()) + "</div>")
            html(f"""<div class="kz-card kz-callout" style="margin-top:20px;padding:22px 24px">
  <div style="font-family:var(--serif);font-size:24px;line-height:1.2">Jazan: DHW {jazan['dhw']:.1f} now, #{int(jazan['rank'])} of 214</div>
  <p>Yet under strong heat, only <b style="color:var(--life)">{facts['red_sea']}%</b> of Red Sea reefs bleached severely,
  against <b style="color:var(--heat)">{facts['elsewhere']}%</b> elsewhere. The Red Sea may be a refuge for the world's corals.</p>
</div>""")

        head("Saudi waters", "Two years of heat on our coast",
             "Daily heat stress for the three Saudi reef regions. Above 4, bleaching is likely. Above 8, severe bleaching is likely")
        saudi_heat = facts["saudi_heat"]
        fig = go.Figure()
        for s, color, width in [("Tabuk, Saudi Arabia", "#4E6C77", 2), ("Al Madinah and Makkah", "#86A2A9", 2), (JAZAN, HEAT, 3.5)]:
            d = saudi_heat[saudi_heat["station"] == s]
            short = s.split(",")[0].replace("Al Madinah and Makkah", "Makkah")
            fig.add_scatter(x=d["date"], y=d["dhw"], mode="lines", line=dict(color=color, width=width, shape="spline", smoothing=.6),
                            hovertemplate=f"{short} · %{{x|%d %b %Y}} · DHW %{{y:.1f}}<extra></extra>")
            fig.add_annotation(x=d["date"].iloc[-1], y=d["dhw"].iloc[-1], text=short, showarrow=False, xanchor="left", xshift=8,
                               font=dict(size=15, color=color))
        for level in (4, 8):
            fig.add_hline(y=level, line_dash="dot", line_color="rgba(238,246,246,.25)", line_width=1)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(title=dict(text="DHW", font=dict(size=15, color=TEXT2)))
        chart(fig, 320, margin=dict(l=8, r=72, t=16, b=8))


# ================================================================ 3. ACT — where to dive, who lives there
with tab_act:
    if tab_act.open:
        band("reef_sharks", "Reef health index · 2,648 dive sites", "Dive where reefs thrive, rest the ones that overheat",
             "Scored on fish, coral, visibility, bleaching risk and past bleaching. Click a site to see who lives near it")

        f1, f2 = st.columns([2, 1], vertical_alignment="bottom")
        countries = f1.multiselect("Countries", sorted(dive["country"].dropna().unique()), placeholder="All countries", key="countries")
        only_cr = f2.toggle("Critically endangered nearby", key="only_cr")
        sites = dive.sort_values("health_index", ascending=False)
        if countries:
            sites = sites[sites["country"].isin(countries)]
        if only_cr:
            sites = sites[sites["CR"] > 0]
        st.caption(f"{len(sites):,} sites match · the map shows the top 400 · click a site to see who lives near it")
        col_map, col_cards = st.columns([3, 2], gap="large")
        with col_map:
            fig = px.scatter_geo(sites.head(400), lat="latitude", lon="longitude", color="health_index", hover_name="site_name",
                                 color_continuous_scale=WATER_SCALE, range_color=[30, 90], custom_data=["site_code"],
                                 hover_data={"latitude": False, "longitude": False, "country": True, "fish_species": ":.0f", "health_index": ":.0f"},
                                 labels={"health_index": "Health", "fish_species": "Fish species", "country": "Country"})
            fig.update_traces(marker=dict(size=9, line=dict(width=0)))
            fig.update_geos(projection_type="natural earth", showland=True, landcolor="#17323F", showocean=True, oceancolor="#08202D",
                            showcountries=False, coastlinecolor="#2E5363", coastlinewidth=.6, showlakes=False, showframe=False,
                            bgcolor="rgba(0,0,0,0)", lataxis_range=[-60, 75])
            fig.update_layout(coloraxis_showscale=False)
            clicked_site = picked(chart(fig, 460, key="dive_map", select=True))
        with col_cards:
            sub("Healthiest reefs")
            html('<div class="kz-rows">' + "".join(
                f'<div class="kz-site"><div class="top"><div class="name">{r.site_name}</div><div class="score">{r.health_index:.0f}</div></div>'
                f'<div class="meta">{r.country} · {r.fish_species:.0f} fish species</div>'
                f'<div class="track"><div style="width:{r.health_index:.0f}%"></div></div></div>'
                for r in sites.head(5).itertuples()) + "</div>")

        threatened = facts["threatened"]
        checked = sites[sites["site_code"].isin(threatened["site_code"])]
        labels = dict(zip(checked["site_code"], checked["site_name"] + " · " + checked["country"]))
        codes = list(labels)
        head("Rare creatures", "Who lives near your dive?", "IUCN threatened species recorded within about 25 km")
        if not codes:
            st.info("None of the matching sites were checked for threatened species. Try other countries")
        else:
            start = codes.index(clicked_site) if clicked_site in labels else 0
            col_pick, col_counts = st.columns([2, 3], gap="large")
            with col_pick:
                code = st.selectbox("Dive site", codes, index=start, format_func=labels.get, key=f"site_{start}")
                if clicked_site and clicked_site not in labels:
                    st.caption("That site wasn't checked for threatened species, so here is one that was")
            near = threatened[threatened["site_code"] == code]
            near = near.sort_values("category", key=lambda s: s.map({"CR": 0, "EN": 1, "VU": 2}))
            counts = near["category"].value_counts()
            with col_counts:
                html('<div class="kz-grid kz-g3">'
                     + stat("Critically endangered", int(counts.get("CR", 0)), tone="heat")
                     + stat("Endangered", int(counts.get("EN", 0)))
                     + stat("Vulnerable", int(counts.get("VU", 0))) + "</div>")
                html('<div style="margin-top:12px">' + "".join(
                    f'<span class="kz-tag {c.lower()}"><b>{c}</b><i>{s}</i></span>'
                    for s, c in zip(near["species"].head(12), near["category"].head(12))) + "</div>")

        head("Who it is for", "One map, three kinds of user")
        users = [("Divers and travellers", "Free", "The healthiest reefs to dive today, and the rare animals you might meet there"),
                 ("Dive operators and eco-tourism", "Paid dashboard", "Which sites to promote, and which to rest while they overheat"),
                 ("Researchers and conservation", "Priority list", "Places rich in hidden life that are under heat stress today")]
        html('<div class="kz-users">' + "".join(
            f'<div><div class="k">{k}</div><h3>{t}</h3><p>{d}</p></div>' for t, k, d in users) + "</div>")


# ---------------------------------------------------------------- footer (credits, one line)
credits = json.loads((STATIC / "credits.json").read_text(encoding="utf-8"))
shown = [f"{n}_video" if (STATIC / f"{n}.mp4").exists() and f"{n}_video" in credits else n
         for n in ["hero_turtle", "bleaching", "reef_sharks"]]
media_line = " · ".join(dict.fromkeys(f'{credits[k]["author"].split(" from ")[0]} ({credits[k]["license"]})'
                                      for k in shown if k in credits))
html(f'<div class="kz-foot">Kanz · Tuwaiq Academy · Data: OBIS, Global Coral Bleaching Database, NOAA Coral Reef Watch, '
     f'Reef Life Survey / IMOS, NOAA Deep-Sea Coral &amp; Sponge Database, IUCN · '
     f'Photos and videos: {media_line}; deep-sea photos NOAA</div>')
