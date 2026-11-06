deckScene("measured", {
  init(el) {
    const fills = [...el.querySelectorAll("[data-bar]")]
    const values = fills.map((fill) => Number(el.querySelector(`[data-num="${fill.dataset.bar}"]`)?.dataset.value))
    if (!values.every((value) => Number.isFinite(value) && value >= 0)) return
    const max = Math.max(...values) || 1
    fills.forEach((fill, i) => fill.style.setProperty("--w", String(values[i] / max)))
  },
})
