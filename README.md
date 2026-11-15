# Kanz | كنز

**Find the ocean's hidden life before heat takes it.**

### [Open the live app → kanz-ml.streamlit.app](https://kanz-ml.streamlit.app/)

Machine Learning final project, Tuwaiq Academy.

---

## The idea

The ocean's real treasure is life, and most of it has never been recorded.

* Only **28.7%** of the seafloor has been mapped in detail.
* **18.9%** of known sea animals have been seen only once.
* Most unrecorded life lives in warm seas, and warm seas are exactly where coral reefs are turning white from heat (called *bleaching*).

Kanz uses two machine-learning models on real scientific data to answer three questions:

| Question | Answer |
|---|---|
| Where is the treasure? | **Treasure map model**: how many kinds of sea life each patch of ocean *should* have, against how many have been recorded. The gap is life nobody has found yet |
| Which reefs will heat damage? | **Bleaching model**: predicts whether a reef will bleach not at all, a little, or badly, from the sea's heat and the reef's surroundings. Combined with the treasure map, it shows where we could lose the most life first |
| What can we do? | **Reef health score**: a score out of 100 for 2,648 dive sites, so divers visit healthy reefs and rest the ones under heat |

**Is there hope?** Under the same strong heat, only **2%** of Red Sea reefs bleached badly, against **56%** elsewhere. The Red Sea may be a refuge for the world's corals.

---

## What you can do in the app

| Tab | Try this |
|---|---|
| **Treasure** | Spin a 3D globe and hover any patch of ocean to see how much life is still unrecorded there. Then dive from the reef down to 6,000 m past real deep-sea animals |
| **Risk** | Pick any reef, make the sea +1, +2 or +3 °C warmer, and watch the model's answer change. See what the model relies on most, which reefs could lose the most life today, and two years of heat on the Saudi coast |
| **Act** | Find the healthiest reefs to dive, filter by country, and click a site to see the endangered animals living near it |

**Heat build-up**, used across the app, measures how hot the sea has been and for how long over the last 3 months. Scientists call it *degree heating weeks*. Above 4, bleaching is likely. Above 8, bad bleaching is likely.

---

## Results

Both models were tested on places they never saw during training.

| Model | Chosen | Result in plain words | Score | Simple baseline |
|---|---|---|---|---|
| Treasure map | Random Forest | Explains 82% of the differences in sea life between ocean regions it never saw | R² **0.82** | 0.68 |
| Bleaching | Random Forest | Catches 7 in 10 cases of bad bleaching on reefs it never saw | macro F1 **0.70** | 0.43 |

**What the bleaching model relies on most:** sea heat (39%), where the reef is (25%), storms and wind (15%), the usual temperature for that place and month (13%), and water clarity (9%).

**Why these scores**
* **R²** shows how much of the difference in sea life between places the model explains.
* **macro F1** treats the three bleaching levels fairly. Plain accuracy would hide a weak "bad bleaching" class, and missing bad bleaching is the costly mistake.

**Limits**
* On future years the bleaching model is weaker (F1 0.50), so today's risk is an estimate, not a forecast.
* Sea-life records follow where scientists have looked, so "not yet recorded" is an estimate, not a count.

Every step, choice and reason is in [`notebooks/Kanz.ipynb`](notebooks/Kanz.ipynb).

---

## Run it yourself

Python 3.11 or newer.

```bash
pip install -r requirements.txt
```

```bash
streamlit run app/streamlit_app.py
```

To rebuild the models and tables from the raw data, run `notebooks/Kanz.ipynb` from top to bottom (about 2 minutes).

---

## What's in the repo

```
app/            the Streamlit app (streamlit_app.py) and its 3D globe and deep-sea dive
notebooks/      Kanz_EDA.ipynb (data exploration) and Kanz.ipynb (the full project)
datasets_csv/   the 10 datasets
models/         the two trained models
outputs/        the tables the app reads
docs/           the presentation
```

---

## Data

| Source | Used for |
|---|---|
| [OBIS](https://obis.org) | The global sea-life database: species, discovery history, endangered animals near dive sites |
| [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) and [HadISST](https://www.metoffice.gov.uk/hadobs/hadisst/) | Ocean depth and sea temperature for the treasure map |
| [Global Coral Bleaching Database](https://www.ncei.noaa.gov/products/coral-bleaching-database) | Training the bleaching model, the Red Sea finding |
| [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov) | Daily heat build-up for 214 reef areas |
| [Reef Life Survey](https://reeflifesurvey.com) | Fish and coral on 2,648 dive sites |
| [NOAA Deep-Sea Coral & Sponge Database](https://deepseacoraldata.noaa.gov) | Deep-sea animal photos |
| [Our World in Data](https://ourworldindata.org/grapher/sea-surface-temperature-anomaly) | Ocean warming since 1850 |

---

## Credits

Photos from Wikimedia Commons:
* Hawksbill turtle, Red Sea, by Derek Keats ([CC BY 2.0](https://commons.wikimedia.org/wiki/File:Hawksbill_turtle_at_Elphinstone_Reef,_Red_Sea,_Egypt_(35150034493).jpg))
* Red Sea soft corals, by Alexander Vasenin ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Elphinstone_Reef_soft_corals.jpg))
* Coral bleaching, by Ryan Goehrung ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Colorful_Coral_Bleaching.jpg))
* Whitetip reef sharks, by Diego Delso ([CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:Tiburones_de_arrecife_de_punta_blanca_(Triaenodon_obesus),_Nosy_Tanikely,_Madagascar,_2025-09-19,_DD_119.jpg))

Videos and deep-sea photos: see `app/static/credits.json` and NOAA. 3D globe: [globe.gl](https://github.com/vasturiano/globe.gl) (MIT licence).
