deckScene("funnel", {
  init(el) {
    const field = el.querySelector("[data-field]")
    const random = deckKit.rng(7)
    const cols = 16
    const rows = 8
    const picks = new Set()
    while (picks.size < 6) picks.add(Math.floor(random() * cols * rows))
    let k = 0
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const dot = document.createElement("i")
        const x = c * 64
        const y = r * 56 + 20
        dot.className = "dot"
        dot.style.setProperty("--x", `${x}px`)
        dot.style.setProperty("--y", `${y}px`)
        dot.style.setProperty("--d", `${0.2 + (c + r) * 0.02}s`)
        if (picks.has(r * cols + c)) {
          dot.classList.add("is-picked")
          dot.style.setProperty("--k", String(k))
          dot.style.setProperty("--tx", `${1560 - x}px`)
          dot.style.setProperty("--ty", `${60 + k * 64 - y}px`)
          k += 1
        }
        field.append(dot)
      }
    }
  },
})
