(() => {
  const kit = window.deckKit
  const v = kit.viz
  const { node, text, at } = v

  const heatmap = (svg, o) => {
    const rows = o.series
    const cols = Math.max(...rows.map((row) => row.length))
    const left = o.names.length ? Number(o.d.labelWidth ?? 200) : 0
    const top = o.labels.length ? 44 : 0
    const scaleNames = v.list(o.d.scale, ";")
    const bottom = scaleNames.length ? 64 : 0
    const cw = (o.w - left) / cols
    const ch = (o.h - top - bottom) / rows.length
    const flat = rows.flat().filter(Number.isFinite)
    const max = Number(o.d.max ?? Math.max(...flat))
    const min = Number(o.d.min ?? Math.min(0, ...flat))
    const showValues = o.flag("showValues")
    const marked = new Set(v.list(o.d.mark, ";"))
    o.labels.forEach((label, c) => at(text(svg, left + cw * c + cw / 2, 26, label, "viz-tick f", { "text-anchor": "middle" }), o.delay))
    rows.forEach((row, r) => {
      if (o.names[r]) at(text(svg, left - 16, top + ch * r + ch / 2 + 8, o.names[r], "viz-label f", { "text-anchor": "end" }), o.delay)
      row.forEach((value, c) => {
        if (!Number.isFinite(value)) return
        const level = (value - min) / (max - min || 1)
        const hot = marked.has(`${r}:${c}`)
        const cell = node("rect", { x: left + cw * c + 3, y: top + ch * r + 3, width: cw - 6, height: ch - 6, rx: Math.min(10, cw / 6) }, svg, `viz-cell pop${hot ? " is-mark" : ""}`)
        cell.style.setProperty("--level", level.toFixed(3))
        at(cell, o.delay + 0.15 + 0.02 * (r + c))
        if (showValues) {
          const label = text(svg, left + cw * c + cw / 2, top + ch * r + ch / 2 + 9, v.fmt(o, value), `viz-cell-value f${level > 0.55 ? " is-on-accent" : ""}`, { "text-anchor": "middle" })
          at(label, o.delay + 0.5 + 0.02 * (r + c))
        }
      })
    })
    if (scaleNames.length) {
      const g = at(node("g", {}, svg, "f"), o.delay + 0.8)
      const y0 = o.h - 34
      const high = text(g, o.w, y0 + 24, scaleNames[1] ?? "", "viz-note", { "text-anchor": "end" })
      const w = 44
      const x1 = o.w - high.getComputedTextLength() - 16
      for (let k = 0; k < 5; k += 1) {
        const cell = node("rect", { x: x1 - w * (5 - k), y: y0, width: w - 4, height: 32, rx: 6 }, g, "viz-cell")
        cell.style.setProperty("--level", (k / 4).toFixed(2))
      }
      text(g, x1 - w * 5 - 16, y0 + 24, scaleNames[0], "viz-note", { "text-anchor": "end" })
    }
  }

  const waffle = (svg, o) => {
    const total = Number(o.d.total ?? 100)
    const cols = Number(o.d.cols ?? 10)
    const rows = Math.ceil(total / cols)
    const size = Math.min(o.w / cols, o.h / rows)
    const ox = (o.w - size * cols) / 2
    let filled = 0
    const bounds = o.values.map((value) => (filled += value))
    for (let i = 0; i < total; i += 1) {
      const group = bounds.findIndex((limit) => i < limit)
      const cls = group < 0 ? "is-empty" : v.tone(o, group) || (group === 0 ? "is-accent" : `is-shade-${Math.min(group, 3)}`)
      const x = ox + (i % cols) * size
      const y = Math.floor(i / cols) * size
      at(node("rect", { x: x + 4, y: y + 4, width: size - 8, height: size - 8, rx: size * 0.18 }, svg, `viz-unit pop ${cls}`), o.delay + 0.008 * i)
    }
  }

  const dots = (svg, o) => {
    const total = Number(o.d.total ?? 1000)
    const cols = Number(o.d.cols ?? Math.round(Math.sqrt((total * o.w) / o.h)))
    const rows = Math.ceil(total / cols)
    const step = Math.min(o.w / cols, o.h / rows)
    const r = step * 0.36
    const rng = kit.rng(Number(o.d.seed ?? 11))
    const picked = new Set()
    const count = o.values[0] ?? 1
    while (picked.size < Math.min(count, total)) picked.add(Math.floor(rng() * total))
    const ox = (o.w - step * cols) / 2 + step / 2
    for (let i = 0; i < total; i += 1) {
      const hit = picked.has(i)
      const cx = ox + (i % cols) * step
      const cy = Math.floor(i / cols) * step + step / 2
      const tone = o.danger.length ? "is-danger" : "is-accent"
      const dot = node("circle", { cx, cy, r: hit ? r * 1.7 : r }, svg, `viz-dot ${hit ? `pop is-ringed ${tone}` : "f is-faint"}`)
      const when = hit ? o.delay + 1 + 0.1 * [...picked].indexOf(i) : o.delay + 0.0006 * i
      at(dot, when)
      if (hit) {
        const ring = at(node("circle", { cx, cy, r: r * 1.7 }, svg, "ping only-motion"), when + 0.3)
        ring.style.color = o.danger.length ? "var(--deck-danger)" : "var(--deck-accent)"
      }
    }
  }

  const pictogram = (svg, o) => {
    const total = Number(o.d.total ?? 10)
    const icon = document.getElementById("deck-icons")?.content.querySelector(`svg[data-icon="${o.d.icon ?? "user"}"]`)
    const cols = Number(o.d.cols ?? total)
    const rows = Math.ceil(total / cols)
    const size = Math.min(o.w / cols, o.h / rows)
    const ox = (o.w - size * cols) / 2
    const count = o.values[0] ?? 1
    for (let i = 0; i < total; i += 1) {
      const hit = i < count
      const g = node("svg", { x: ox + (i % cols) * size + size * 0.1, y: Math.floor(i / cols) * size + size * 0.1, width: size * 0.8, height: size * 0.8, viewBox: "0 0 24 24" }, svg, `viz-icon ${hit ? (o.danger.length ? "is-danger" : "is-accent") : "is-faint"}`)
      if (icon) for (const child of icon.children) g.append(child.cloneNode(true))
      const wrap = node("g", {}, svg, "pop")
      wrap.append(g)
      at(wrap, o.delay + 0.08 * i)
    }
  }

  const calendar = (svg, o) => {
    const cells = o.values
    const rows = Number(o.d.rows ?? 7)
    const cols = Math.ceil(cells.length / rows)
    const top = o.labels.length ? 40 : 0
    const size = Math.min(o.w / cols, (o.h - top) / rows)
    const max = Number(o.d.max ?? Math.max(...cells))
    o.labels.forEach((label, i) => at(text(svg, (i * cols * size) / o.labels.length, 24, label, "viz-tick f"), o.delay))
    cells.forEach((value, i) => {
      const c = Math.floor(i / rows)
      const r = i % rows
      const cell = node("rect", { x: c * size + 3, y: top + r * size + 3, width: size - 6, height: size - 6, rx: size * 0.2 }, svg, `viz-cell pop${o.accent.includes(i) ? " is-mark" : ""}`)
      cell.style.setProperty("--level", (value / (max || 1)).toFixed(3))
      at(cell, o.delay + 0.006 * i)
    })
  }

  const squarify = (items, x, y, w, h, out) => {
    if (!items.length) return
    if (items.length === 1) {
      out.push({ ...items[0], x, y, w, h })
      return
    }
    const total = items.reduce((a, b) => a + b.value, 0)
    let acc = 0
    let split = 0
    while (split < items.length - 1 && acc + items[split].value <= total / 2) acc += items[split++].value
    if (split === 0) acc = items[split++].value
    const share = acc / total
    if (w >= h) {
      squarify(items.slice(0, split), x, y, w * share, h, out)
      squarify(items.slice(split), x + w * share, y, w * (1 - share), h, out)
    } else {
      squarify(items.slice(0, split), x, y, w, h * share, out)
      squarify(items.slice(split), x, y + h * share, w, h * (1 - share), out)
    }
  }

  const treemap = (svg, o) => {
    const items = o.values.map((value, i) => ({ value, i })).sort((a, b) => b.value - a.value)
    const total = o.values.reduce((a, b) => a + b, 0) || 1
    const out = []
    squarify(items, 0, 0, o.w, o.h, out)
    out.forEach((box, k) => {
      const cls = v.tone(o, box.i) || (k === 0 && !o.accent.length ? "is-accent" : `is-shade-${Math.min(1 + (k % 3), 3)}`)
      at(node("rect", { x: box.x + 4, y: box.y + 4, width: box.w - 8, height: box.h - 8, rx: 12 }, svg, `viz-tile s ${cls}`), o.delay + 0.1 * k)
      if (box.w > 150 && box.h > 90) {
        const light = cls === "is-accent"
        at(text(svg, box.x + 28, box.y + 52, o.labels[box.i] ?? "", `viz-label is-strong f${light ? " is-on-accent" : ""}`), o.delay + 0.4 + 0.1 * k)
        at(text(svg, box.x + 28, box.y + 90, v.fmt(o, (box.value / total) * 100, "%"), `viz-tile-value f${light ? " is-on-accent" : ""}`), o.delay + 0.5 + 0.1 * k)
      }
    })
  }

  Object.assign(v.types, { heatmap, waffle, dots, pictogram, calendar, treemap })
})()
