# Kanz | كنز

**Find the ocean's hidden life before heat takes it.**

### [Open the live app → kanz-ml.streamlit.app](https://kanz-ml.streamlit.app/)

Machine Learning final project, Tuwaiq Academy.

---

## The idea

The ocean's real treasure is life, and most of it has never been recorded.

* Only **28.7%** of the seafloor has been mapped in detail.
* **18.9%** of known marine species have been seen only once.
* Most of the unrecorded life lives in warm seas, and warm seas are exactly where coral reefs are bleaching from heat.

Kanz uses two machine-learning models on real scientific data to answer five questions:

| # | Question | Answer |
|---|---|---|
| 1 | Where is the treasure? | **Model 1, Treasure Map**: how many species each ocean area *should* have, against how many are recorded. The gap is life we have not found yet |
| 2 | Can we predict bleaching? | **Model 2, Bleaching Risk**: none, mild or severe bleaching, from heat stress and reef conditions |
| 3 | Where will we lose it first? | **Treasure at risk**: hidden life (Model 1) × today's bleaching risk (Model 2 on live NOAA data) |
| 4 | Is there hope? | Under the same strong heat, only **2.1%** of Red Sea reefs bleached severely, against **56.4%** elsewhere |
| 5 | What can we do? | **Dive Finder**: a reef health score for 2,648 dive sites, so divers visit healthy reefs and rest the overheating ones |

---

## What you can do in the app

| Tab | Try this |
|---|---|
| **Kanz** | Spin a 3D globe of all 214 reef regions today. Jump to a reef (Jazan, the Caribbean, the Maldives…) and see its heat stress, bleaching risk and hidden species |
| **Discover** | Explore the treasure map in 3D, see how fast new species are still being found, and dive from the reef down to 6,000 m past real deep-sea animals |
| **Danger** | Pick any reef, add +1, +2 or +3 °C, and watch the model's bleaching risk change. Then press play to watch a year of heat move across the world's reefs |
| **At risk** | Click any reef on the globe to see where the most life is in danger today, plus a spotlight on the Saudi Red Sea |
| **Dive** | Choose what matters to you (fish, coral, visibility, low risk), filter by country, and see the endangered animals living near each dive site |

Every tab has a **How we know** section with the model's score, how it was tested, and its limits.

---

## Results

Both models are tested on data they never saw during training.

| Model | Chosen | Tested on | Score | Simple baseline |
|---|---|---|---|---|
| Treasure Map | Random Forest | ocean regions it never saw | **R² 0.82** | 0.68 |
| Bleaching Risk | Random Forest | reef sites it never saw | **macro F1 0.70** | 0.43 |

**Why these metrics**
* **R²** shows how much of the species count the model explains.
* **macro F1** treats the three bleaching classes fairly. Accuracy would hide a weak "severe" class, and missing severe bleaching is the costly mistake.

**Limits**
* On future years the bleaching model is weaker (F1 0.50), so today's risk is an estimate, not a forecast.
* Species records follow where scientists have looked, so hidden species are an estimate, not a count.

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
app/            the Streamlit app
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
| [OBIS](https://obis.org) | Marine species, discovery history, threatened species near dive sites |
| [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) and [HadISST](https://www.metoffice.gov.uk/hadobs/hadisst/) | Ocean depth and sea temperature for the Treasure Map |
| [Global Coral Bleaching Database](https://www.ncei.noaa.gov/products/coral-bleaching-database) | Training the bleaching model, the Red Sea finding |
| [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov) | Daily heat stress for 214 reef regions |
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

Deep-sea photos: NOAA. 3D globe: [globe.gl](https://github.com/vasturiano/globe.gl) (MIT licence).
