# Kanz | كنز

Find the ocean's hidden life before heat takes it.

Machine Learning final project, Tuwaiq Academy.

The ocean's real treasure is life, and most of it has never been recorded. Only 28.7% of the seafloor is mapped, and 18.9% of known marine species have been seen only once. Most of the unrecorded life sits in warm seas, and warm seas are where coral reefs are bleaching from heat.

Kanz uses two ML models and one score to answer one chain of questions:

| # | Question | How we answer it |
|---|---|---|
| 1 | Where is the treasure? | **Model 1, Treasure Map** (regression): how many species each 5° ocean cell *should* have vs how many are recorded |
| 2 | What threatens it, and can we predict it? | **Model 2, Bleaching Risk** (classification): none / mild / severe bleaching from heat stress and site conditions |
| 3 | Where will we lose it first? | **Treasures at Risk** = hidden species (Model 1) × severe-bleaching risk today (Model 2 on live NOAA heat data) |
| 4 | Is there hope? | Red Sea corals: **2.1%** severe bleaching vs **56.4%** in the rest of the world under the same strong heat |
| 5 | What can we do? | **Dive Finder**, a Reef Health Index for 2,648 dive sites (fish, coral, visibility, risk today, past bleaching) |

---

## Results

Both models are tested on data they never saw: unseen ocean regions for Model 1, unseen reef sites for Model 2.

| Model | Chosen | Test | Score | Baseline |
|---|---|---|---|---|
| Model 1, Treasure Map | Random Forest (tuned) | unseen ocean regions (30° blocks) | **R² 0.82** | effort only 0.68 |
| Model 2, Bleaching Risk | Random Forest (tuned) | unseen reef sites | **macro F1 0.70** | heat rule 0.43 |

**Why these metrics**
* **R²** for Model 1: it shows how much of the species count the model explains.
* **macro F1** for Model 2: the three classes are not balanced, and accuracy would hide a weak "severe" class.
* **severe recall** is also reported: missing a severe bleaching is the costly mistake.

**Honest limits**
* On *future years*, Model 2 drops to F1 0.50, so the live risk is an estimate, not a forecast.
* NOAA's daily DHW is computed differently from the survey database's DHW.
* Species records follow where scientists dive (sampling bias). That is why Model 1 uses search effort as a feature and is tested on unseen regions.

Full details, every choice and its reason are in [`notebooks/Kanz.ipynb`](notebooks/Kanz.ipynb).

---

## The app (5 tabs)

| Tab | Question | What you can do |
|---|---|---|
| **Kanz** | Why should I care? | A live 3D globe of all 214 reef regions today: height = treasure at risk, colour = heat stress, rings = the 8 most at risk. Fly-to buttons (No. 1 at risk, Jazan, Caribbean, Florida Keys, Maldives) move the globe and update the big numbers |
| **Discover** | Where is the treasure? | A 3D globe of Model 1's hidden species per ocean cell, the discovery curve, and a dive from the reef to 6,400 m past real NOAA deep-sea photos, with a live depth meter |
| **Danger** | Can we predict bleaching? | Pick a reef region and tap +1, +2 or +3 °C to watch the model's risk respond (it opens on the Maldives: 6% today, 45% at +1 °C). Then press play to watch a year of heat move across the reefs on a 3D globe, ending on the Red Sea |
| **At risk** | Where will we lose it first? | Click a column on the 3D globe to follow that region, then send it to the model. Red Sea spotlight and two years of heat on the Saudi coast |
| **Dive** | What can we do? | Tune the reef health index, filter by country, and click a dive site to see the threatened species near it |

**For the presentation**
* The right and left arrow keys (what a presentation clicker sends) move between tabs.
* Each tab ends with a **Next** button, and every tab has its own link, for example `?tab=Danger`.
* Sliders stay left to right in Arabic-language browsers too (Streamlit mirrors them otherwise; the fix is in `app/components/keys.js`).
* Each tab has a **How we know** section with the model's score against its baseline, the test used, and one limit.
* The globes use [globe.gl](https://github.com/vasturiano/globe.gl) (MIT), saved in `app/static/vendor`, so the demo works without internet. The custom pieces live in `app/components`.

**Design.** A deep-ocean dark theme built for a projector: lagoon turquoise means life and treasure, coral means heat and danger, text is 17 px or larger and key numbers 44 px or larger. Newsreader for headlines, Instrument Sans for text, IBM Plex Mono for figures. Every place shows its coordinates in mono, like soundings on a nautical chart. The interface was cleaned with [unslop](https://github.com/heydamir/unslop) by Damir Sokolovsky (CC BY 4.0).

---

## How to run

Use Python 3.11 or newer.

```bash
pip install -r requirements.txt
```

```bash
streamlit run app/streamlit_app.py
```

The app reads the ready tables in `outputs/` and the models in `models/`, so it starts in seconds.

To rebuild everything from the raw data, run `notebooks/Kanz.ipynb` top to bottom (about 2 minutes). It writes `outputs/` and `models/` again.

---

## Repository layout

```
datasets_csv/   10 raw datasets (the 3 large ones are .csv.gz; pandas reads them directly)
notebooks/
  Kanz_EDA.ipynb   exploration of every dataset
  Kanz.ipynb       the full project: problem → data → EDA → preprocessing → models → evaluation → selection → linking
models/         model1_treasure_map.joblib, model2_bleaching_risk.joblib
outputs/        tables the app reads (treasure map, risk today, dive finder, results)
app/
  streamlit_app.py   the 5-tab app
  style.css          the design system
  components/        the 3D globe, the deep-sea dive and the presenter keys (JS + CSS)
  static/            photos, plus globe.gl and the world map in static/vendor
.streamlit/     app theme and settings
docs/           the presentation (added later)
```

---

## Datasets

| Dataset | Used for |
|---|---|
| [OBIS](https://obis.org): marine animal species, ocean grid cells, threatened species | Discovery curve, Model 1 target and search effort, threatened species near dive sites |
| [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) depth and [HadISST](https://www.metoffice.gov.uk/hadobs/hadisst/) sea temperature (via ERDDAP) | Model 1 features |
| [Global Coral Bleaching Database](https://www.ncei.noaa.gov/products/coral-bleaching-database) | EDA, Model 2, Red Sea finding |
| [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov) daily reef stations | Today's heat stress → live risk |
| [Reef Life Survey / IMOS](https://reeflifesurvey.com) | Coral → fish evidence, Dive Finder |
| [NOAA Deep-Sea Coral & Sponge Database](https://deepseacoraldata.noaa.gov) | Deep-sea creature photos |
| [Our World in Data](https://ourworldindata.org/grapher/sea-surface-temperature-anomaly): sea surface temperature anomaly | Ocean warming context |

---

## Photo credits

All photos are from Wikimedia Commons:

* Hawksbill turtle at Elphinstone Reef, Red Sea, by Derek Keats ([CC BY 2.0](https://commons.wikimedia.org/wiki/File:Hawksbill_turtle_at_Elphinstone_Reef,_Red_Sea,_Egypt_(35150034493).jpg))
* Elphinstone Reef soft corals, by Alexander Vasenin ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Elphinstone_Reef_soft_corals.jpg))
* Colorful coral bleaching, by Ryan Goehrung ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Colorful_Coral_Bleaching.jpg))
* Whitetip reef sharks, Nosy Tanikely, by Diego Delso ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Tiburones_de_arrecife_de_punta_blanca_(Triaenodon_obesus),_Nosy_Tanikely,_Madagascar,_2025-09-19,_DD_119.jpg))

Deep-sea photos load from NOAA's public image links.
