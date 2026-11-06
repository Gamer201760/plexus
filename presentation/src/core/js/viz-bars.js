(() => {
  const v = window.deckKit.viz
  const { node, text, counter, at, tone, scale, yAxis, plotBox, extent } = v
  const numbersOf = v.numbers

  const columns = (svg, o) => {
    const negRoom = !o.flag("noValues") && o.series.some((row) => row.some((value) => value < 0)) ? 44 : 0
    const plot = plotBox(o, { bottom: (o.labels.length ? 64 : 24) + negRoom, top: 56 })
    const [min, max] = extent(o.series, o)
    const y = yAxis(svg, o, plot, min, max)
    const n = o.values.length
    const groups = o.series.length
    const band = (plot.x1 - plot.x0) / n
    const gap = band * (Number(o.d.gap ?? 0.32))
    const width = (band - gap) / groups
    const back = node("g", {}, svg)
    const mid = node("g", {}, svg)
    const front = node("g", {}, svg)
    if (o.d.target !== undefined) {
      const ty = y(Number(o.d.target))
      at(node("path", { d: `M${plot.x0} ${ty} H${plot.x1}`, pathLength: 1 }, mid, "viz-target dr"), o.delay + 1.1)
      if (o.d.targetLabel) at(text(front, plot.x0 + 12, ty - 14, o.d.targetLabel, "viz-note is-strong f"), o.delay + 1.2)
    }
    o.values.forEach((_, i) => {
      o.series.forEach((row, s) => {
        const value = row[i]
        const x = plot.x0 + band * i + gap / 2 + width * s
        const top = y(Math.max(value, 0))
        const height = Math.abs(y(value) - y(0))
        const cls = groups > 1 ? `viz-bar ${tone(o, s, true) || "is-muted"}` : `viz-bar ${tone(o, i)}`
        at(node("rect", { x, y: top, width: width - 4, height, rx: 6 }, back, `${cls} gy${value < 0 ? " is-neg" : ""}`), o.delay + 0.3 + 0.06 * i)
        const hot = groups === 1 ? tone(o, i) : tone(o, s, true)
        if (!o.flag("noValues") && !(o.flag("accentValues") && !hot)) {
          const label = counter(front, o, x + (width - 4) / 2, value < 0 ? y(value) + 34 : top - 16, value, `viz-value f${hot ? ` is-strong ${hot}` : ""}`, { "text-anchor": "middle" })
          at(label, o.delay + 0.6 + 0.06 * i)
        }
      })
      if (o.labels[i]) at(text(svg, plot.x0 + band * i + band / 2, plot.y1 + 40 + negRoom, o.labels[i], "viz-label f", { "text-anchor": "middle" }), o.delay + 0.2)
    })
  }

  const bars = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const valueW = o.flag("noValues") ? 0 : 140
    const x0 = labelW
    const x1 = o.w - valueW
    const [min, max] = extent([o.values], o)
    const x = scale(min, max, x0, x1)
    const row = o.h / o.values.length
    const thick = Math.min(row * 0.5, 48)
    o.values.forEach((value, i) => {
      const cy = row * i + row / 2
      const cls = tone(o, i)
      if (cls) at(node("rect", { x: -16, y: cy - row / 2 + 4, width: o.w + 16, height: row - 8, rx: 14 }, svg, `viz-row f ${cls}`), o.delay)
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", `viz-label f ${cls ? "is-strong" : ""}`), o.delay + 0.05 * i)
      at(node("rect", { x: x0, y: cy - thick / 2, width: x1 - x0, height: thick, rx: thick / 2 }, svg, "viz-track f"), o.delay)
      at(node("rect", { x: Math.min(x(0), x(value)), y: cy - thick / 2, width: Math.abs(x(value) - x(0)), height: thick, rx: thick / 2 }, svg, `viz-bar gx ${cls}`), o.delay + 0.2 + 0.07 * i)
      if (valueW) at(counter(svg, o, x1 + 28, cy + 10, value, `viz-value f${cls ? ` is-strong ${cls}` : ""}`), o.delay + 0.5 + 0.07 * i)
    })
  }

  const seriesTone = (o, s) => {
    if (o.accent.length) return o.accent.includes(s) ? "is-accent" : ["is-muted", "is-faint", "is-shade-3"][Math.min(s, 2)]
    return s === 0 ? "is-accent" : `is-shade-${Math.min(s, 3)}`
  }

  const stacked = (svg, o) => {
    const plot = plotBox(o, { bottom: 64, top: 64 })
    const totals = o.values.map((_, i) => o.series.reduce((sum, row) => sum + (row[i] ?? 0), 0))
    const max = o.d.max !== undefined ? Number(o.d.max) : v.nice(Math.max(...totals))
    const y = yAxis(svg, o, plot, 0, max)
    const band = (plot.x1 - plot.x0) / o.values.length
    const width = band * 0.62
    o.values.forEach((_, i) => {
      let base = 0
      const x = plot.x0 + band * i + (band - width) / 2
      const column = at(node("g", {}, svg, "gy"), o.delay + 0.2 + 0.1 * i)
      o.series.forEach((row, s) => {
        const value = row[i] ?? 0
        const top = y(base + value)
        node("rect", { x, y: top, width, height: Math.max(y(base) - top - 3, 0), rx: 4 }, column, `viz-bar ${seriesTone(o, s)}`)
        base += value
      })
      at(counter(svg, o, x + width / 2, y(base) - 16, totals[i], "viz-value f", { "text-anchor": "middle" }), o.delay + 0.8 + 0.1 * i)
      if (o.labels[i]) at(text(svg, x + width / 2, plot.y1 + 40, o.labels[i], "viz-label f", { "text-anchor": "middle" }), o.delay)
    })
    if (o.names.length) v.legend(svg, o, o.names.map((label, s) => ({ label, tone: seriesTone(o, s) })), plot.x0, 24)
  }

  const share = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 280)
    const top = o.names.length ? 64 : 0
    const row = (o.h - top) / o.series.length
    const thick = Math.min(row * 0.6, 76)
    const rows = numbersOf(o.d.rows)
    o.series.forEach((parts, r) => {
      const total = parts.reduce((a, b) => a + b, 0) || 1
      const cy = top + row * r + row / 2
      const hot = rows.includes(r)
      at(text(svg, 0, cy + 9, o.labels[r] ?? "", `viz-label f${hot ? " is-strong" : ""}`), o.delay + 0.05 * r)
      const line = at(node("g", {}, svg, "gx"), o.delay + 0.2 + 0.12 * r)
      let cursor = labelW
      parts.forEach((value, s) => {
        const width = ((o.w - labelW) * value) / total
        node("rect", { x: cursor, y: cy - thick / 2, width: Math.max(width - 4, 0), height: thick, rx: 6 }, line, `viz-bar ${seriesTone(o, s)}`)
        if (width > 96) at(text(svg, cursor + 18, cy + 10, `${v.fmt(o, (value / total) * 100, "%")}`, `viz-inside f ${seriesTone(o, s) === "is-accent" ? "is-on-accent" : ""}`), o.delay + 0.8 + 0.12 * r)
        cursor += width
      })
      if (hot) at(node("rect", { x: labelW - 8, y: cy - thick / 2 - 8, width: o.w - labelW + 8, height: thick + 16, rx: 12 }, svg, "viz-ring s"), o.delay + 1.2)
    })
    if (o.names.length) v.legend(svg, o, o.names.map((label, s) => ({ label, tone: seriesTone(o, s) })), labelW, 24)
  }

  Object.assign(v.types, { columns, bars, stacked, share })
  Object.assign(v, { seriesTone })
})()
