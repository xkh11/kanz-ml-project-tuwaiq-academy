// Runs on every page load (mounted above the tabs).
//
// 1) Slider fix: Streamlit's sliders take their direction from the browser language. In an Arabic browser they
//    switch to right-to-left and mirror the knob, while the coloured fill still draws left to right, so the knob
//    and the fill disagree. Pinning the widget locale to English keeps every slider left to right.
const LOCALE = Symbol.for("react-aria.i18n.locale");
function pinLocale() {
  if (window[LOCALE] === "en-US") return;
  window[LOCALE] = "en-US";
  window.dispatchEvent(new Event("languagechange"));   // re-render widgets that already read the locale
}
pinLocale();

// 2) Presenter keys: the right and left arrows (what a presentation clicker sends) move between tabs.
export default function (component) {
  pinLocale();
  window.__kzNav = component.setTriggerValue;
  if (window.__kzKeys) return;
  window.__kzKeys = true;
  window.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    const t = e.target;
    if (t && t.closest && t.closest("input, textarea, select, [role='slider'], [role='combobox'], [contenteditable='true']")) return;
    e.preventDefault();
    window.__kzNav && window.__kzNav("nav", e.key === "ArrowRight" ? "next" : "prev");
  });
}
