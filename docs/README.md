# Docs

Project documents for Kanz | كنز.

| File | What it is |
|---|---|
| `index.html` | The final presentation in Arabic (12 slides): problem, solution, results, then the live demo |

## Open the presentation

Online: **https://xkh11.github.io/kanz-ml-project-tuwaiq-academy/** (GitHub Pages, served from this `docs` folder).

Offline: double-click `index.html`. It opens in your browser and works offline, except the researchers' photo on slide 10, which loads from NOAA.

* **Next slide:** right arrow, Space or Enter. **Previous:** left arrow. **Full screen:** F.
* **Slide 2:** the first press reveals the answer, the second moves on.
* **Slide 11:** the first press plays a year of reef heat on the globe (about 20 seconds, ending on the Red Sea today). You can also press the play button or drag the bar.

## The font

The slides use the **Thmanyah** font (Thmanyah Sans and Thmanyah Serif Display). Its licence does not allow uploading the font files, so they are **not** in this repo.

* To see the slides in Thmanyah, download the font from the official site, [thmanyah.com](https://thmanyah.com), and install it on your computer. The slides pick it up automatically.
* Without it, the slides use IBM Plex Sans Arabic and Noto Naskh Arabic from Google Fonts instead.
* Never commit Thmanyah font files (`.otf`, `.woff2`) or `fonts-local-only.css` to this repo.

## Editing

All the text is in `index.html`, one `<section class="slide">` per slide, in order. Change the Arabic text between the tags and keep the tags as they are.

* `img/`: the photos (credits in the main README).
* `vendor/`: the 3D globe library and the data it draws (`reefs.js` today's reef heat, `heatyear.js` a year of weekly heat, `land.js` the world map).
