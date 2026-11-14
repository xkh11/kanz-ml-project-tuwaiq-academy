# 💎 Kanz | كنز — How to build the whole project

> *Discover it. Protect it. Dive it.*
> Machine Learning final project (Units 4 & 5) — Tuwaiq Academy

---

## 1. The idea
The ocean's real treasure is **life**, and most of it is still unknown. Marine heat is killing coral reefs (the richest homes of ocean life) before we even find what lives there.

**Kanz** answers 5 questions, one per app tab:

| # | Question | Answer from our data |
|---|---|---|
| 1 | **Why care?** | Only 28.7% of the seafloor is mapped (outside figure: cite its source); ~9,000 new marine species are still described per decade (8,896 in the 2010s); 18.9% of species were seen only once |
| 2 | **Where is the treasure?** | **Model 1 (Treasure Map):** expected vs recorded species per ocean area. The biggest gaps are in warm seas (median 1,075 hidden species per cell vs 400 in cold seas) |
| 3 | **What threatens it?** | Heat stress: severe bleaching goes from 12.7% (no heat stress) to 58.6% (DHW 8+). Coral loss = fish loss (15 → 49.4 fish species with more coral). **Model 2 (Bleaching risk)** predicts it |
| 4 | **Where will we lose it first, and is there hope?** | Model 1 × Model 2 on NOAA heat = **Treasures at Risk**. On 10 Nov 2026: #1 Northern Myanmar; **Jazan #4 worldwide and #1 in Saudi Arabia / the Red Sea**. Twist: Red Sea corals barely bleach (2.1% vs 56.4%) → possible coral refuge |
| 5 | **What can we do?** | **Dive Finder:** healthy dive sites + threatened species nearby (sharks, turtles) + list of areas to explore and protect |

**One sentence:** the ocean's treasure is life; it lives in warm seas; heat is killing it before we find it; it's happening today, even in our Red Sea, whose corals may be the world's refuge; Kanz shows where to act and where to dive.

---

## 2. The data (10 CSV files in `datasets_csv/`)

The 3 biggest files are compressed (`.csv.gz`) so they upload to GitHub easily. pandas reads them the same way: `pd.read_csv("file.csv.gz")`.

| File | Rows | What it is | Used for |
|---|---|---|---|
| `coral_bleaching_surveys.csv.gz` | 41,361 | Coral surveys: % bleached + sea temperature + heat stress (1980–2020) | Model 2, Red Sea finding |
| `noaa_reef_stations.csv` | 214 | NOAA reef regions: name, location, normal hottest-month temperature | Risk today |
| `noaa_reef_heat_stress_daily.csv.gz` | 156,220 | Daily sea temperature + heat stress (DHW) per region, 17 Oct 2024 → 10 Nov 2026 | Risk today, Saudi waters |
| `reef_life_surveys.csv` | 36,447 | One row per dive survey: fish species, count, biomass, hard coral %, depth, visibility | Coral → fish, Dive Finder |
| `reef_life_sites.csv` | 4,894 | Dive sites: name, country, location, zone | Dive Finder |
| `obis_marine_animal_species.csv.gz` | 164,232 | Marine animal species: description year (in `scientificNameAuthorship`), number of records | Discovery curve, rare species |
| `ocean_grid_cells.csv` | 1,881 | 5° × 5° ocean cells: depth, sea temperature, OBIS records + species | Model 1 |
| `threatened_species_near_dive_sites.csv` | 5,019 | IUCN threatened species near the top 149 dive sites (CR / EN / VU) | Dive & Act |
| `deep_sea_corals_species.csv` | 4,384 | Deep-sea coral / sponge species: deepest depth, ocean, photo link | Creature gallery |
| `sea_temperature_anomaly.csv` | 531 | Sea temperature vs the 1961–1990 average, per year | "The ocean is warming" chart |

**Sources (4 main):** OBIS · Global Coral Bleaching Database (van Woesik & Kratochwill 2022) · NOAA Coral Reef Watch · Reef Life Survey / IMOS NRMN. Extras: NOAA Deep-Sea Coral Database, Our World in Data.

### Data traps (read before starting)
* **Coral bleaching file:**
  * missing values are written as `nd` → `pd.read_csv(..., na_values=["nd"])`
  * each sample is repeated once per seabed type (same bleaching %) → keep one row per `Sample_ID` (34,515 labelled rows → 23,271 samples from 11,068 sites)
  * `ClimSST = 262.15` (−11 °C) is a fake placeholder → make it missing (4,229 samples)
  * columns with "Kelvin" in the name, and `ClimSST`, are in Kelvin (°C = K − 273.15)
* **DHW** (degree heating weeks): 4 or more = bleaching likely, 8 or more = severe bleaching likely.
* **Reef Life Survey:** 57.5% of sites are in Australia → split by site when testing.
* **OBIS:** shows where scientists *recorded* species, not every species that exists.
* **Threatened species file:** "near the site" = in the wider area, not "seen on the dive" (e.g. deep-sea vent snails near Fiji). The list seems capped at 100 species per site.

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
| **1. Problem definition** | The 5 questions (= the 5 app tabs), the users, the 2 ML tasks + 1 score | Why ML: it estimates what is unknown (missing species, future bleaching) |
| **2. Data** | Load the 10 CSVs, the table above, what was dropped | Why each source |
| **3. EDA** | Use the answers from `Kanz_EDA.ipynb`: discovery curve, heat → bleaching, coral → fish, Red Sea, class balance, missing values, sampling bias | Class imbalance → macro F1; sampling bias → group splits |
| **4. Preprocessing** | **Bleaching:** one row per sample, fake ClimSST → missing, target 0 none / 1 mild (<20%) / 2 severe (≥20%), 12 current columns, median imputation inside the pipelines (no one-hot: all 12 inputs are numbers). **Grid:** log of species and records, distance from the equator, 30° blocks. **Dive sites:** average per site, 3+ dives only, join by distance (BallTree haversine, 50 km; NOAA station within 300 km) | Each step + its number |
| **5. Modeling** | **Model 1** (regression): baseline (effort only), Ridge, Random Forest, Gradient Boosting. **Model 2** (classification): baselines (most common, heat rule), Logistic Regression, KNN, Random Forest, Gradient Boosting, Voting | Why each model family |
| **6. Evaluation** | **Model 1:** R², MAE (log), **spatial-block CV** (30° blocks), **2-part sanity check** (1: best-searched areas: expected ≈ recorded; 2: no exploding at maximum search). **Model 2:** macro F1, severe recall, confusion matrix, **GroupKFold by site**, **12 vs all 38 columns**, **future-years test** (train ≤ 2010, test after), calibration, top features | Why each metric and split; honest limits |
| **7. Model selection** | Same rule for both, then tune the winners | Results table |
| **8. Linking the results** | Treasure Map, Risk today, Treasures at Risk, Red Sea spotlight, Dive Finder | Why a score (no "good site" label) |
| **9. Save** | Clean tables + 2 models (`joblib.dump(..., compress=3)`, ~13 MB and ~30 MB) + results CSVs for the "How we know" boxes + `station_inputs.csv` for the live app | — |

### Selection rule (same for every model)
```
1 It must beat its baseline
2 Take the best cross-validated score
3 If a simpler model is within 1 std of the best -> take the simpler one
4 (Model 1 only) it must pass the sanity check
5 Tune the winner (RandomizedSearchCV with the same group split)
```

### Final results (from `Kanz.ipynb`)
| Model | Test | Score | Baseline |
|---|---|---|---|
| Model 1 — Treasure Map (Random Forest, tuned) | Unseen ocean regions | R² 0.82 ± 0.02 | effort only 0.68 |
| Model 2 — Bleaching risk (Random Forest, tuned, 12 current columns) | Unseen reef sites | macro F1 0.70, severe recall 0.72 | heat rule 0.43 (severe recall 0.31) |

Key decisions (tested):
* **Model 2 uses 12 current columns, not all 38.** The 12: `Temperature_Kelvin, SSTA, TSA, SSTA_DHW, TSA_DHW, Date_Month` (heat now) + `ClimSST, Depth_m, Distance_to_Shore, Turbidity, Cyclone_Frequency, Windspeed` (the place). With 38: 0.719 on unseen sites but 0.426 on future years (future severe recall 0.05). With 12: 0.682 and 0.505 (future severe recall 0.29). Future prediction is the real use, fewer inputs are simpler, and only these 12 can be built from today's NOAA data.
* **Model 1 is Random Forest, not Ridge.** Ridge was as accurate (0.815 vs 0.816) and passed part 1 of the sanity check (+5.7%; Random Forest −9.6%), but failed part 2: at maximum search it said the best-searched areas still hide +712% species (a straight line never stops growing). Random Forest levels off (+32%; tuned: −17% / +12%).
* **Model 2 is Random Forest, not Voting.** Voting scored best (0.684 ± 0.010), but Random Forest (0.682) is within 1 std and simpler.
* **Checks:** catches 72% of severe cases, only 8% of severe cases called "none"; calibrated (says 70% → really 73%); risk drivers: the place 56%, heat now 39%, month 5%.
* **Honest limit:** on future years, Model 2's severe recall is 0.27 vs 0.33 for the heat rule (macro F1 0.50), because the data changes over time: 76% of samples after 2010 come from Reef Check, and severe bleaching is rarer (13.4% vs 25.2% before).

### Step 8 details
* **Treasure Map:** expected species if every cell were searched like a well-searched cell (373,261 records) → hidden species = expected − recorded.
* **Risk today:** feed each NOAA station's last day (**10 Nov 2026**) into Model 2:
  * `Temperature_Kelvin` = SST + 273.15
  * `SSTA` = anomaly
  * `TSA` = SST − hottest-month mean
  * `TSA_DHW` = `SSTA_DHW` = DHW
  * `Date_Month` = this month
  * site columns = median of bleaching surveys within 300 km (179 of 214 stations; the other 35 use the world median)

  Result: 65 of 214 reef regions predicted severe. Limit: NOAA's daily DHW is computed a bit differently from the database's DHW, so this is an **estimate**.
* **Treasures at Risk** = rank of hidden species (Model 1) × rank of severe risk today (Model 2). On 10 Nov 2026: 1 Northern Myanmar · 2 Dhofar (Oman) · 3 Southwestern Cuba · **4 Jazan** (62% severe risk, DHW 17.5) · Tabuk #13 · Al Madinah & Makkah #24.
* **Dive Finder (Reef Health Index):**
  * percentile score of fish species (0.30), hard coral (0.25), visibility (0.15), low risk today (0.15), low bleaching history (0.15); missing parts = 50 (neutral)
  * 2,648 sites with 3+ dives; risk today from the nearest NOAA station within 300 km
  * ranking is stable when the weights change: Spearman 0.96–0.99, 6–8 of the top 10 stay the same
  * demo site: Ransiwor Islet (Raja Ampat) #6 of 2,648, with 4 critically endangered species nearby (incl. the hawksbill turtle)
  * *Optional:* K-means reef types as a filter (Unit 5) — not done

---

## 4. Streamlit app: 5 tabs (one question per tab)

| Tab | Shows |
|---|---|
| 1. 🌊 **Kanz** | 3 hero numbers (28.7% mapped · reef regions on alert (live) · Red Sea 2.1% vs 56.4%) + today's headline |
| 2. 💎 **Discover** | Treasure Map, top hidden-treasure areas, discovery curve, deep-sea photos |
| 3. 🔥 **Danger** | Heat → bleaching, coral → fish, bleaching predictor with "+°C" slider, today's risk map |
| 4. ⚠️ **At Risk** | **Live** Treasures at Risk map + top 10, Red Sea spotlight (Jazan + the twist), with the data date on screen |
| 5. 🤿 **Dive & Act** | Dive Finder (weights, filters), threatened species near a site, explore list, business box |

* Each tab ends with a **"Next →"** question.
* Each tab has a **"🔬 How we know"** expander: baseline vs model, the test used, one limit.
* "+°C" slider: +1 °C adds 4 DHW (assumes the warmth lasts ~4 weeks) — show this on screen.
* **Live data:** `live_risk.py` downloads NOAA's newest day for every reef region (~30 s, kept 6 hours, 🔄 refresh button) and runs Model 2 on it. If NOAA can't be reached, it uses the saved 10 Nov 2026 data and shows a warning.
* "Today" = **10 Nov 2026 in the notebook** and **the newest NOAA day in the app**.
* Files: `app.py`, `live_risk.py`, `requirements.txt` (same scikit-learn version as the notebook), `models/`, `outputs/`.

---

## 5. Presentation (8 min: Problem → Solution → Results → Demo)
1. **Problem (1.5 min):** "We know the Moon better than our ocean floor."
2. **Solution (1.5 min):** Kanz = 5 tabs = 5 questions.
3. **Results (3 min):**
   * one chart: baseline vs model for both models (R² 0.82 vs 0.68; macro F1 0.70 vs 0.43)
   * top risk factors in plain words (the place matters as much as the heat)
   * the twist: "On 10 Nov 2026, Jazan was the #4 Treasure at Risk in the world and #1 in the Red Sea", but Red Sea corals are tough
   * limits slide, including the plastics model we dropped (proof we follow our rule)
4. **Demo (1.5 min):** click the 5 tabs left to right, ending on the critically endangered hawksbill turtle near Ransiwor Islet (Raja Ampat).
5. **Close (0.5 min):** *"Every reef we lose takes species we never met. Kanz finds them first."*

**Business:**
* divers → free guide
* dive operators / eco-tourism → paid dashboard
* researchers / conservation → priority list

Don't claim real companies use Kanz. Always say the date with notebook results ("as of 10 Nov 2026").

---

## 6. Who does what

| Member | EDA (now) | Build | Present |
|---|---|---|---|
| Member 1 | Tasks 1–2 | Model 1 (Treasure Map) + Discover tab | Problem + Discover |
| Member 2 | Tasks 3–4 | Model 2 (Bleaching risk) + Danger tab | Danger |
| Member 3 | Tasks 5–6 | Risk today + Treasures at Risk + At Risk tab | At Risk + Red Sea |
| Member 4 | Task 7 | Dive Finder + Dive & Act tab + app assembly + live NOAA data (`live_risk.py`) | Dive & Act + demo |

## 7. Build order
1. **EDA** — finish `Kanz_EDA.ipynb` (every answer with numbers).
2. **Preprocessing** — clean tables (section 3). ✅ done in `Kanz.ipynb`
3. **Models** — Model 1 and Model 2 with baselines, honest splits, selection rule. ✅ done
4. **Linking** — Treasure Map, risk today, Treasures at Risk, Dive Finder. ✅ done
5. **App** — the 5 tabs (live At Risk tab code ready; test the NOAA download on a laptop).
6. **Slides + rehearsal** — twice, with Q&A: why this model / metric / split / weights?

## 8. Done checklist
- [ ] Every section of `Kanz.ipynb` ends with "Why we chose this" with real numbers (add Sections 2, 4 and 6)
- [x] Both models beat their baselines (shown in one table)
- [x] Sanity check (Model 1) and future-years test (Model 2) are shown
- [ ] All 5 app tabs open with no errors; the slider changes the prediction
- [ ] Live NOAA download tested on a laptop with internet
- [ ] Limits are stated honestly (future years, sampling bias, live risk is an estimate)
- [ ] The 28.7% figure has a source on the slide
- [ ] Slides say "as of 10 Nov 2026" for notebook results
- [ ] Every member can explain their own part

---

## 9. What changed from the first plan
* Results updated: Model 1 R² 0.80 → **0.82**; Model 2 0.71 / 0.75 → **0.70 / 0.72**; future severe recall 0.22 → **0.27**.
* "All 32 columns" → **all 38 columns** (same decision: keep 12).
* Sanity check now has **2 parts** (Ridge passed part 1; part 2 removes it: +712%).
* Treasures at Risk #1: Jazan → **Northern Myanmar**; Jazan is **#4 worldwide, #1 in the Red Sea** (10 Nov 2026).
* "One-hot" removed (no text columns are used).
* New: 3+ dives rule, neutral 50 for missing parts, 300 km radius for site columns, live NOAA data in the app.