(() => {
  const v = window.deckKit.viz
  const { node, text, counter, at, scale, yAxis, plotBox, extent, tight } = v

  const scatter = (svg, o) => {
    const plot = plotBox(o, { bottom: 56, left: o.flag("noTicks") ? 16 : 96 })
    const points = o.series
    const xs = points.map((p) => p[0])
    const ys = points.map((p) => p[1])
    const pad = o.flag("hulls") ? 110 : 0
    const x = scale(o.d.xmin !== undefined ? Number(o.d.xmin) : Math.min(...xs), o.d.xmax !== undefined ? Number(o.d.xmax) : Math.max(...xs), plot.x0 + 60 + pad, plot.x1 - 60 - pad)
    const y = scale(o.d.ymin !== undefined ? Number(o.d.ymin) : Math.min(...ys), o.d.ymax !== undefined ? Number(o.d.ymax) : Math.max(...ys), plot.y1 - 50 - pad, plot.y0 + 50 + pad)
    at(node("path", { d: `M${plot.x0} ${plot.y0} V${plot.y1} H${plot.x1}` }, svg, "axis f"), o.delay)
    if (o.d.xname) at(text(svg, plot.x1, plot.y1 + 40, o.d.xname, "viz-label f", { "text-anchor": "end" }), o.delay)
    if (o.d.yname) at(text(svg, plot.x0 + 12, plot.y0 - 12, o.d.yname, "viz-label f"), o.delay)
    const rmax = Math.max(...points.map((p) => p[2] ?? 0))
    const accentGroup = o.d.accentGroup !== undefined ? Number(o.d.accentGroup) : -1
    const groupTone = (g) => (g === accentGroup ? "is-accent" : g ? `is-shade-${Math.min(g, 3)}` : "is-muted")
    if (o.flag("hulls")) {
      const groups = [...new Set(points.map((p) => p[3] ?? 0))]
      groups.forEach((g, k) => {
        const members = points.filter((p) => (p[3] ?? 0) === g).map((p) => [x(p[0]), y(p[1])])
        const cx = members.reduce((sum, p) => sum + p[0], 0) / members.length
        const cy = members.reduce((sum, p) => sum + p[1], 0) / members.length
        const r = Math.max(...members.map((p) => Math.hypot(p[0] - cx, p[1] - cy))) + 40
        at(node("circle", { cx, cy, r }, svg, `viz-hull s ${groupTone(g)}`), o.delay + 1 + 0.15 * k)
      })
    }
    points.forEach((p, i) => {
      const sized = rmax > 0 && p[2] > 0
      const r = sized ? 10 + 60 * Math.sqrt(p[2] / rmax) : 12
      const cls = v.tone(o, i) || groupTone(p[3] ?? 0)
      at(node("circle", { cx: x(p[0]), cy: y(p[1]), r }, svg, `viz-dot pop ${cls}${sized ? " is-bubble" : ""}`), o.delay + 0.3 + 0.025 * i)
      if (sized && v.tone(o, i) === "is-accent") {
        const ring = at(node("circle", { cx: x(p[0]), cy: y(p[1]), r }, svg, "ping only-motion"), o.delay + 1.2)
        ring.style.color = "var(--deck-accent)"
      }
      if (o.labels[i]) at(text(svg, x(p[0]), y(p[1]) - r - 14, o.labels[i], `viz-label f ${v.tone(o, i) ? "is-strong is-accent" : ""}`, { "text-anchor": "middle" }), o.delay + 0.8 + 0.025 * i)
    })
  }

  const strip = (svg, o) => {
    const rng = window.deckKit.rng(Number(o.d.seed ?? 7))
    const bottom = 56
    const row = (o.h - bottom) / o.series.length
    const labelW = Number(o.d.labelWidth ?? 280)
    const [min, max] = tight(o.series, o)
    const x = scale(min, max, labelW + 20, o.w - 20)
    o.series.forEach((values, r) => {
      const cy = row * r + row / 2
      const cls = v.tone(o, r) || "is-muted"
      const start = o.delay + 0.2 + 0.6 * r
      const lo = Math.min(...values)
      const hi = Math.max(...values)
      at(node("rect", { x: x(lo) - 18, y: cy - row * 0.32, width: x(hi) - x(lo) + 36, height: row * 0.64, rx: row * 0.32 }, svg, `viz-range gx ${cls}`), start)
      at(text(svg, 0, cy + 9, o.labels[r] ?? "", `viz-label f${cls !== "is-muted" ? " is-strong" : ""}`), o.delay)
      values.forEach((value, i) => {
        const jitter = (rng() - 0.5) * row * 0.42
        at(node("circle", { cx: x(value), cy: cy + jitter, r: 9 }, svg, `viz-dot pop ${cls}`), start + 0.15 + 0.015 * i)
      })
      const mean = values.reduce((a, b) => a + b, 0) / values.length
      at(node("path", { d: `M${x(mean)} ${cy - row * 0.38} V${cy + row * 0.38}` }, svg, "viz-mean s"), start + 0.6)
      at(text(svg, x(mean) + 14, cy - row * 0.38 + 6, `${o.d.meanLabel ?? ""} ${v.fmt(o, mean)}`.trim(), "viz-note is-strong f"), start + 0.7)
    })
    const axis = at(node("g", {}, svg, "viz-axis f"), o.delay)
    node("path", { d: `M${labelW + 20} ${o.h - bottom + 8} H${o.w - 20}` }, axis, "axis")
    const step = v.tickStep(max - min)
    for (let t = Math.ceil(min / step) * step; t <= max + 1e-9; t += step) {
      text(axis, x(t), o.h - 12, v.fmt(o, t), "viz-tick", { "text-anchor": "middle" })
    }
  }

  const boxplot = (svg, o) => {
    const plot = plotBox(o, { bottom: 64 })
    const [min, max] = extent(o.series, o)
    const y = yAxis(svg, o, plot, min, max)
    const band = (plot.x1 - plot.x0) / o.series.length
    o.series.forEach(([lo, q1, med, q3, hi], i) => {
      const cx = plot.x0 + band * i + band / 2
      const w = band * 0.4
      const cls = v.tone(o, i)
      const g = at(node("g", {}, svg, "s"), o.delay + 0.2 + 0.12 * i)
      node("path", { d: `M${cx} ${y(hi)} V${y(q3)} M${cx} ${y(q1)} V${y(lo)} M${cx - w / 4} ${y(hi)} H${cx + w / 4} M${cx - w / 4} ${y(lo)} H${cx + w / 4}` }, g, "viz-whisker")
      node("rect", { x: cx - w / 2, y: y(q3), width: w, height: y(q1) - y(q3), rx: 6 }, g, `viz-box ${cls}`)
      node("path", { d: `M${cx - w / 2} ${y(med)} H${cx + w / 2}` }, g, `viz-median ${cls}`)
      at(text(svg, cx + w / 2 + 12, y(med) + 8, v.fmt(o, med), `viz-value f ${cls ? "is-strong" : ""}`), o.delay + 0.6 + 0.12 * i)
      if (o.labels[i]) at(text(svg, cx, plot.y1 + 40, o.labels[i], "viz-label f", { "text-anchor": "middle" }), o.delay)
    })
  }

  const candles = (svg, o) => {
    const plot = plotBox(o, { bottom: o.labels.length ? 64 : 24, right: 180 })
    const [min, max] = tight(o.series, o, 0.3)
    const y = yAxis(svg, o, plot, min, max)
    const band = (plot.x1 - plot.x0) / o.series.length
    o.series.forEach(([open, high, low, close], i) => {
      const cx = plot.x0 + band * i + band / 2
      const cls = close >= open ? "is-good" : "is-danger"
      const g = at(node("g", {}, svg, "s"), o.delay + 0.2 + 0.04 * i)
      node("path", { d: `M${cx} ${y(high)} V${y(low)}` }, g, `viz-wick ${cls}`)
      node("rect", { x: cx - band * 0.3, y: y(Math.max(open, close)), width: band * 0.6, height: Math.max(Math.abs(y(open) - y(close)), 3), rx: 3 }, g, `viz-candle ${cls}`)
    })
    const x = (i) => plot.x0 + band * i + band / 2
    for (const mark of v.list(o.d.marks, ";")) {
      const [index, label] = mark.split(":")
      const i = Number(index)
      const [, , low, close] = o.series[i]
      const last = o.series.at(-1)[3]
      at(node("path", { d: `M${x(i)} ${y(close)} H${x(o.series.length - 1) + band * 0.65}` }, svg, "viz-link f"), o.delay + 1.1)
      at(node("circle", { cx: x(i), cy: y(low) + 30, r: 12 }, svg, "viz-dot is-ringed pop is-accent"), o.delay + 1)
      at(text(svg, x(i), y(low) + 72, label ?? "", "viz-note is-strong f", { "text-anchor": "middle" }), o.delay + 1.1)
      const gain = ((last - close) / close) * 100
      at(text(svg, x(o.series.length - 1) + band * 0.95, (y(close) + y(last)) / 2 + 10, `${gain >= 0 ? "+" : "−"}${v.fmt({ ...o, digits: 1 }, Math.abs(gain), "%")}`, `viz-value is-strong f ${gain >= 0 ? "is-good" : "is-danger"}`), o.delay + 1.4)
      at(node("path", { d: `M${x(o.series.length - 1) + band * 0.65} ${y(close)} V${y(last)}`, pathLength: 1 }, svg, `viz-span dr ${gain >= 0 ? "is-good" : "is-danger"}`), o.delay + 1.3)
    }
    v.xLabels(svg, o, plot, x)
  }

  const interval = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const [min, max] = tight(o.series, o, 0.25)
    const x = scale(min, max, labelW + 30, o.w - 40)
    const top = o.d.ref !== undefined ? 48 : 0
    const row = (o.h - top) / o.series.length
    if (o.d.ref !== undefined) {
      const rx = x(Number(o.d.ref))
      at(node("path", { d: `M${rx} ${top - 6} V${o.h}` }, svg, "viz-target f"), o.delay)
      at(text(svg, rx, 24, `${o.d.refLabel ?? ""} ${v.fmt(o, Number(o.d.ref))}`.trim(), "viz-note is-strong f", { "text-anchor": "middle" }), o.delay)
    }
    o.series.forEach(([lo, mid, hi], i) => {
      const cy = top + row * i + row / 2
      const cls = v.tone(o, i) || "is-muted"
      const hot = cls !== "is-muted"
      const when = o.delay + 0.3 + 0.2 * i
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", `viz-label f${hot ? " is-strong" : ""}`), o.delay)
      const span = at(node("path", { d: `M${x(mid)} ${cy} H${x(lo)} M${x(mid)} ${cy} H${x(hi)}`, pathLength: 1 }, svg, `viz-span is-thick dr ${cls}`), when + 0.2, 0.6)
      span.style.strokeWidth = hot ? "10px" : "8px"
      at(node("path", { d: `M${x(lo)} ${cy - 18} V${cy + 18} M${x(hi)} ${cy - 18} V${cy + 18}` }, svg, `viz-span f ${cls}`), when + 0.6)
      at(node("circle", { cx: x(mid), cy, r: hot ? 18 : 14 }, svg, `viz-dot is-ringed pop ${cls}`), when)
      at(counter(svg, o, x(hi) + 26, cy + 10, mid, `viz-value f${hot ? ` is-strong ${cls}` : ""}`), when + 0.6)
    })
  }

  Object.assign(v.types, { scatter, strip, boxplot, candles, interval })
})()
