# 💎 Kanz | كنز — How to build the whole project

> *Discover it. Protect it. Dive it.*
> Machine Learning final project (Units 4 & 5) — Tuwaiq Academy

---

## 1. The idea
The ocean's real treasure is **life**, and most of it is still unknown. Marine heat is killing coral reefs (the richest homes of ocean life) before we even find what lives there.

**Kanz** answers 5 questions, one per app tab:

| # | Question | Answer from our data |
|---|---|---|
| 1 | **Why care?** | Only 28.7% of the seafloor is mapped; ~9,000 new marine species are still described per decade; 19% of species were seen only once |
| 2 | **Where is the treasure?** | **Model 1 (Treasure Map):** expected vs recorded species per ocean area. The biggest gaps are in warm seas |
| 3 | **What threatens it?** | Heat stress: severe bleaching goes from 13% (no heat stress) to 59% (high heat stress). Coral loss = fish loss (15 → 49 fish species with more coral). **Model 2 (Bleaching risk)** predicts it |
| 4 | **Where will we lose it first, and is there hope?** | Model 1 × Model 2 on today's NOAA heat = **Treasures at Risk**. Top today: **Jazan (Saudi Red Sea)**. Twist: Red Sea corals barely bleach (2% vs 56%) → possible coral refuge |
| 5 | **What can we do?** | **Dive Finder:** healthy dive sites + threatened species nearby (sharks, turtles) + list of areas to explore and protect |

**One sentence:** the ocean's treasure is life; it lives in warm seas; heat is killing it before we find it; it's happening today, even in our Red Sea, whose corals may be the world's refuge; Kanz shows where to act and where to dive.

---

## 2. The data (10 CSV files in `datasets_csv/`)

The 3 biggest files are compressed (`.csv.gz`) so they upload to GitHub easily. pandas reads them the same way: `pd.read_csv("file.csv.gz")`.

| File | Rows | What it is | Used for |
|---|---|---|---|
| `coral_bleaching_surveys.csv.gz` | 41,361 | Coral surveys: % bleached + sea temperature + heat stress (1980–2020) | Model 2, Red Sea finding |
| `noaa_reef_stations.csv` | 214 | NOAA reef regions: name, location, normal hottest-month temperature | Risk today |
| `noaa_reef_heat_stress_daily.csv.gz` | 156,220 | Daily sea temperature + heat stress (DHW) per region, last 2 years | Risk today, Saudi waters |
| `reef_life_surveys.csv` | 36,447 | One row per dive survey: fish species, count, biomass, hard coral %, depth, visibility | Coral → fish, Dive Finder |
| `reef_life_sites.csv` | 4,894 | Dive sites: name, country, location, zone | Dive Finder |
| `obis_marine_animal_species.csv.gz` | 164,232 | Marine animal species: description year (in `scientificNameAuthorship`), number of records | Discovery curve, rare species |
| `ocean_grid_cells.csv` | 1,881 | 5° × 5° ocean cells: depth, sea temperature, OBIS records + species | Model 1 |
| `threatened_species_near_dive_sites.csv` | 5,019 | IUCN threatened species near the top 150 dive sites (CR / EN / VU) | Dive & Act |
| `deep_sea_corals_species.csv` | 4,384 | Deep-sea coral / sponge species: deepest depth, ocean, photo link | Creature gallery |
| `sea_temperature_anomaly.csv` | 531 | Sea temperature vs the 1961–1990 average, per year | "The ocean is warming" chart |

**Sources (4 main):** OBIS · Global Coral Bleaching Database (van Woesik & Kratochwill 2022) · NOAA Coral Reef Watch · Reef Life Survey / IMOS NRMN. Extras: NOAA Deep-Sea Coral Database, Our World in Data.

### Data traps (read before starting)
* **Coral bleaching file:**
  * missing values are written as `nd` → `pd.read_csv(..., na_values=["nd"])`
  * each sample is repeated once per seabed type (same bleaching %) → keep one row per `Sample_ID` (34,515 labelled rows → 23,271)
  * `ClimSST = 262.15` (−11 °C) is a fake placeholder → make it missing
  * columns with "Kelvin" in the name, and `ClimSST`, are in Kelvin (°C = K − 273.15)
* **DHW** (degree heating weeks): 4 or more = bleaching likely, 8 or more = severe bleaching likely.
* **Reef Life Survey:** 57% of sites are in Australia → split by site when testing.
* **OBIS:** shows where scientists *recorded* species, not every species that exists.

### Dropped data (and why) — say this if asked
* **Microplastics:** a model could not beat the "always Medium" baseline (accuracy 0.39 vs 0.45).
* **Oil spills:** US-only data, not linked to reefs.
* **Fish stocks:** country-level only.
* **Deep-sea species list:** overlaps with the deep-sea corals; not used by any model.

---

## 3. One notebook: `Kanz.ipynb` (follows the brief's 7 steps)

Style:
* one step per cell, short `#` comments
* `# Task` headings, `*` bullets
* every section ends with **"Why we chose this"**: `1- … 2- …` with real numbers

| Section | What to do | Justify |
|---|---|---|
| **1. Problem definition** | The 5 questions, the users, the 2 ML tasks + 1 score | Why ML: it estimates what is unknown (missing species, future bleaching) |
| **2. Data** | Load the 10 CSVs, the table above, what was dropped | Why each source |
| **3. EDA** | Use the answers from `Kanz_EDA.ipynb`: discovery curve, heat → bleaching, coral → fish, Red Sea, class balance, missing values, sampling bias | Class imbalance → macro F1; sampling bias → group splits |
| **4. Preprocessing** | **Bleaching:** one row per sample, fake ClimSST → missing, target 0 none / 1 mild (<20%) / 2 severe (≥20%), median imputation, one-hot. **Grid:** log of species and records. **Dive sites:** average per site, join by distance (BallTree haversine, 50 km; NOAA station within 300 km) | Each step + its number |
| **5. Modeling** | **Model 1** (regression): baseline (effort only), Ridge, Random Forest, Gradient Boosting. **Model 2** (classification): baselines (most common, heat rule), Logistic Regression, KNN, Random Forest, Gradient Boosting, Voting | Why each model family |
| **6. Evaluation** | **Model 1:** R², MAE (log), **spatial-block CV** (30° blocks), **sanity check** (best-sampled areas: expected ≈ recorded). **Model 2:** macro F1, severe recall, confusion matrix, **GroupKFold by site**, **future-years test** (train ≤ 2010, test after), calibration, top features | Why each metric and split; honest limits |
| **7. Model selection** | Same rule for both | Results table |
| **8. Linking the results** | Risk today, Treasures at Risk, Red Sea spotlight, Dive Finder | Why a score (no "good site" label) |
| **9. Save** | Clean tables + 2 models (`joblib.dump(..., compress=3)`) | — |

### Selection rule (same for every model)
```
1 It must beat its baseline
2 Take the best cross-validated score
3 If a simpler model is within 1 std of the best -> take the simpler one
4 (Model 1 only) it must pass the sanity check
5 Tune the winner (RandomizedSearchCV with the same group split)
```

### Results we already found (targets to reproduce)
| Model | Test | Score | Baseline |
|---|---|---|---|
| Model 1 — Treasure Map (Random Forest) | Unseen ocean regions | R² 0.80 | effort only 0.67 |
| Model 2 — Bleaching risk (Random Forest, 12 current-heat columns) | Unseen reef sites | macro F1 0.71, severe recall 0.75 | heat rule 0.42 |

Key decisions already tested:
* **Model 2 uses 12 current-heat columns, not all 32.** With 32: 0.733 on unseen sites but 0.447 on future years. With 12: 0.710 and 0.492. Future prediction is the real use, and fewer inputs are simpler.
* **Model 1 is Random Forest, not Ridge.** Ridge was as accurate, but failed the sanity check (it said the best-sampled areas still hide +75% species; Random Forest: −4%).
* **Honest limit:** on future years, Model 2's severe recall is 0.22 vs 0.33 for the heat rule, because the data sources change over time (bleaching-event compilations before 2010, Reef Check after).

### Step 8 details
* **Risk today:** feed each NOAA station's last day into Model 2:
  * `Temperature_Kelvin` = SST + 273.15
  * `SSTA` = anomaly
  * `TSA` = SST − hottest-month mean
  * `TSA_DHW` = `SSTA_DHW` = DHW
  * `Date_Month` = this month
  * site columns = median of nearby bleaching surveys

  Limit: NOAA's daily DHW is computed a bit differently from the database's DHW, so this is an **estimate**.
* **Treasures at Risk** = rank of discovery gap (Model 1) × rank of severe risk today (Model 2).
* **Dive Finder (Reef Health Index):**
  * percentile score of fish species (0.30), hard coral (0.25), visibility (0.15), low risk today (0.15), low bleaching history (0.15)
  * check that the ranking is stable when the weights change (Spearman correlation)
  * *Optional:* K-means reef types as a filter (Unit 5)

---

## 4. Streamlit app: 5 tabs (one question per tab)

| Tab | Shows |
|---|---|
| 1. 🌊 **Kanz** | 3 hero numbers (28.7% mapped · reef regions on alert today · Red Sea 2% vs 56%) + today's headline |
| 2. 💎 **Discover** | Treasure Map, top hidden-treasure areas, discovery curve, deep-sea photos |
| 3. 🔥 **Danger** | Heat → bleaching, coral → fish, bleaching predictor with "+°C" slider, today's risk map |
| 4. ⚠️ **At Risk** | Treasures at Risk map + top 10, Red Sea spotlight (Jazan today + the twist) |
| 5. 🤿 **Dive & Act** | Dive Finder (weights, filters), threatened species near a site, explore list, business box |

* Each tab ends with a **"Next →"** question.
* Each tab has a **"🔬 How we know"** expander: baseline vs model, the test used, one limit.
* "+°C" slider: +1 °C adds 4 DHW (assumes the warmth lasts ~4 weeks) — show this on screen.

---

## 5. Presentation (8 min: Problem → Solution → Results → Demo)
1. **Problem (1.5 min):** "We know the Moon better than our ocean floor."
2. **Solution (1.5 min):** Kanz = 5 tabs = 5 questions.
3. **Results (3 min):**
   * one chart: baseline vs model for both models
   * top risk factors in plain words
   * the twist: Jazan on alert today, but Red Sea corals are tough
   * limits slide, including the plastics model we dropped (proof we follow our rule)
4. **Demo (1.5 min):** click the 5 tabs left to right, ending on a critically endangered turtle near a top dive site.
5. **Close (0.5 min):** *"Every reef we lose takes species we never met. Kanz finds them first."*

**Business:**
* divers → free guide
* dive operators / eco-tourism → paid dashboard
* researchers / conservation → priority list

Don't claim real companies use Kanz.

---

## 6. Who does what

| Member | EDA (now) | Build | Present |
|---|---|---|---|
| Member 1 | Tasks 1–2 | Model 1 (Treasure Map) + Discover tab | Problem + Discover |
| Member 2 | Tasks 3–4 | Model 2 (Bleaching risk) + Danger tab | Danger |
| Member 3 | Tasks 5–6 | Risk today + Treasures at Risk + At Risk tab | At Risk + Red Sea |
| Member 4 | Task 7 | Dive Finder + Dive & Act tab + app assembly | Dive & Act + demo |

## 7. Build order
1. **EDA** — finish `Kanz_EDA.ipynb` (every answer with numbers).
2. **Preprocessing** — clean tables (section 3).
3. **Models** — Model 1 and Model 2 with baselines, honest splits, selection rule.
4. **Linking** — risk today, Treasures at Risk, Dive Finder.
5. **App** — the 5 tabs.
6. **Slides + rehearsal** — twice, with Q&A: why this model / metric / split / weights?

## 8. Done checklist
- [ ] Every section of `Kanz.ipynb` ends with "Why we chose this" with real numbers
- [ ] Both models beat their baselines (shown in one table)
- [ ] Sanity check (Model 1) and future-years test (Model 2) are shown
- [ ] All 5 app tabs open with no errors; the slider changes the prediction
- [ ] Limits are stated honestly (future years, sampling bias, live risk is an estimate)
- [ ] Every member can explain their own part
