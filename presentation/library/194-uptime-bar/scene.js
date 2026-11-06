deckScene("uptime-bar", {
  init(el) {
    el.querySelectorAll(".ub-days i").forEach((day, i) => day.style.setProperty("--i", String(i)))
  },
})
