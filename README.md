# Kanz | كنز

**Find the ocean's hidden life before heat takes it.**

Machine Learning final project, Tuwaiq Academy.

| | |
|---|---|
| **Live app** | [kanz-ml.streamlit.app](https://kanz-ml.streamlit.app/) |
| **Presentation (Arabic)** | [xkh11.github.io/kanz-ml-project-tuwaiq-academy](https://xkh11.github.io/kanz-ml-project-tuwaiq-academy/) |


---

## The idea

Most life in the ocean has never been recorded, and most of it lives in warm seas. Those same warm seas are where coral reefs are turning white from heat (*bleaching*) and dying. We could lose species before anyone finds them.

Kanz answers three questions with two machine-learning models:

1. **Where is the treasure?** A model estimates how much sea life each patch of ocean holds that nobody has recorded yet.
2. **Which reefs will heat damage?** A second model predicts whether a reef will bleach not at all, a little, or badly. Combined with the first, it shows where we could lose the most life first.
3. **What can we do?** A health score for 2,648 dive sites shows divers the healthiest reefs and the endangered animals living there.

**The hopeful part:** under the same strong heat, only **2%** of Red Sea reefs bleached badly, against **56%** elsewhere.

---

## Results

Both models were tested on places they never saw during training.

| Model | In plain words | Score | Baseline |
|---|---|---|---|
| Treasure map (Random Forest) | Explains 82% of the differences in sea life between ocean regions | R² **0.82** | 0.68 |
| Bleaching (Random Forest) | Catches 7 in 10 cases of bad bleaching | macro F1 **0.70** | 0.43 |

**Limits:** the bleaching model is weaker on future years (F1 0.50), so today's risk is an estimate. Sea-life records follow where scientists have looked, so "not yet recorded" is an estimate too.

---

## The app

| Tab | What you can do |
|---|---|
| **Treasure** | Spin a 3D globe, hover any patch of ocean, and dive down to 6,000 m |
| **Risk** | Pick a reef, make the sea warmer, and watch the model's answer change |
| **Act** | Find the healthiest reefs to dive and the endangered animals near them |

**Heat build-up** (used in the app) means how hot the sea has been and for how long. Scientists call it *degree heating weeks*. Above 4, bleaching is likely. Above 8, bad bleaching is likely.

---

## Run it yourself

```bash
pip install -r requirements.txt
```

```bash
streamlit run app/streamlit_app.py
```

Python 3.11 or newer. To rebuild the models from the raw data, run `notebooks/Kanz.ipynb` top to bottom (about 2 minutes).

---

## What's in the repo

```
app/            the Streamlit app
notebooks/      Kanz_EDA.ipynb (data exploration) and Kanz.ipynb (the full project)
datasets_csv/   the 10 datasets
models/         the two trained models
outputs/        the tables the app reads
docs/           the presentation (live on GitHub Pages)
```

---

## Data

[OBIS](https://obis.org) (sea life) · [Global Coral Bleaching Database](https://www.ncei.noaa.gov/products/coral-bleaching-database) · [NOAA Coral Reef Watch](https://coralreefwatch.noaa.gov) (daily reef heat) · [Reef Life Survey](https://reeflifesurvey.com) (dive sites) · [NOAA ETOPO](https://www.ncei.noaa.gov/products/etopo-global-relief-model) (ocean depth) · [HadISST](https://www.metoffice.gov.uk/hadobs/hadisst/) (sea temperature) · [NOAA Deep-Sea Coral & Sponge Database](https://deepseacoraldata.noaa.gov) (deep-sea photos) · [Our World in Data](https://ourworldindata.org/grapher/sea-surface-temperature-anomaly) (ocean warming)

## Credits

Photos from Wikimedia Commons: Derek Keats (CC BY 2.0), Alexander Vasenin, Ryan Goehrung and Diego Delso (CC BY-SA 4.0). Video credits in `app/static/credits.json`. 3D globe: [globe.gl](https://github.com/vasturiano/globe.gl) (MIT).
