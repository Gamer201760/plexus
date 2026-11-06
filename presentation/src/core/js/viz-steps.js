(() => {
  const v = window.deckKit.viz
  const { node, text, counter, at, tone, scale, yAxis, plotBox, extent } = v

  const waterfall = (svg, o) => {
    const plot = plotBox(o, { bottom: 64, top: 56 })
    let run = 0
    const steps = o.values.map((value, i) => {
      const total = i === 0 || i === o.values.length - 1
      const from = total ? 0 : run
      const to = total ? value : run + value
      run = total ? value : run + value
      return { from, to, value, total }
    })
    const max = o.d.max !== undefined ? Number(o.d.max) : v.nice(Math.max(...steps.map((s) => Math.max(s.from, s.to))))
    const y = yAxis(svg, o, plot, 0, max)
    const band = (plot.x1 - plot.x0) / steps.length
    const width = band * 0.6
    steps.forEach((s, i) => {
      const x = plot.x0 + band * i + (band - width) / 2
      const top = y(Math.max(s.from, s.to))
      const cls = s.total ? (i === 0 ? "is-muted" : "is-accent") : s.value < 0 ? "is-good" : "is-danger"
      at(node("rect", { x, y: top, width, height: Math.max(Math.abs(y(s.from) - y(s.to)), 2), rx: 4 }, svg, `viz-bar gy ${cls}${!s.total && s.value < 0 ? " is-neg" : ""}`), o.delay + 0.25 * i)
      if (i < steps.length - 1) at(node("path", { d: `M${x + width} ${y(s.to)} H${x + band}`, pathLength: 1 }, svg, "viz-link dr"), o.delay + 0.25 * i + 0.2)
      const label = s.total ? v.fmt(o, s.value) : `${s.value > 0 ? "+" : "−"}${v.fmt(o, Math.abs(s.value))}`
      at(text(svg, x + width / 2, top - 14, label, `viz-value f ${s.total ? "is-strong" : ""}`, { "text-anchor": "middle" }), o.delay + 0.25 * i + 0.3)
      if (o.labels[i]) at(text(svg, x + width / 2, plot.y1 + 40, o.labels[i], "viz-label f", { "text-anchor": "middle" }), o.delay)
    })
  }

  const lollipop = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const [min, max] = extent([o.values], o)
    const x = scale(min, max, labelW, o.w - 130)
    const row = o.h / o.values.length
    o.values.forEach((value, i) => {
      const cy = row * i + row / 2
      const cls = tone(o, i)
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", `viz-label f ${cls ? "is-strong" : ""}`), o.delay + 0.05 * i)
      at(node("path", { d: `M${labelW} ${cy} H${o.w - 130}` }, svg, "viz-guide f"), o.delay)
      at(node("path", { d: `M${x(min)} ${cy} H${x(value)}`, pathLength: 1 }, svg, `viz-stem dr ${cls}`), o.delay + 0.2 + 0.08 * i, 0.7)
      at(node("circle", { cx: x(value), cy, r: cls ? 18 : 12 }, svg, `viz-dot pop ${cls}`), o.delay + 0.8 + 0.08 * i)
      at(counter(svg, o, x(value) + (cls ? 34 : 26), cy + 10, value, `viz-value f${cls ? ` is-strong ${cls}` : ""}`), o.delay + 0.9 + 0.08 * i)
    })
  }

  const dumbbell = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const [from, to] = o.series
    const [min, max] = extent(o.series, o)
    const x = scale(min, max, labelW + 200, o.w - 140)
    const top = o.names.length ? 64 : 0
    const row = (o.h - top) / from.length
    from.forEach((a, i) => {
      const b = to[i]
      const cy = top + row * i + row / 2
      const cls = tone(o, i) || "is-accent"
      const down = b < a
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", "viz-label f"), o.delay + 0.05 * i)
      at(node("path", { d: `M${labelW} ${cy} H${o.w}` }, svg, "viz-guide f"), o.delay)
      at(node("circle", { cx: x(a), cy, r: 12 }, svg, "viz-dot pop is-muted"), o.delay + 0.2 + 0.08 * i)
      at(text(svg, x(a) + (down ? 26 : -26), cy + 9, v.fmt(o, a), "viz-value f", { "text-anchor": down ? "start" : "end" }), o.delay + 0.3 + 0.08 * i)
      at(node("path", { d: `M${x(a)} ${cy} H${x(b)}`, pathLength: 1 }, svg, `viz-span dr ${cls}`), o.delay + 0.7 + 0.08 * i, 0.8)
      const dot = at(node("circle", { cx: x(b), cy, r: 17 }, svg, `viz-dot mv ${cls}`), o.delay + 0.7 + 0.08 * i, 0.8)
      dot.style.setProperty("--dx", `${(x(a) - x(b)).toFixed(1)}px`)
      at(text(svg, x(b) + (down ? -30 : 30), cy + 11, v.fmt(o, b), `viz-value f is-strong ${cls}`, { "text-anchor": down ? "end" : "start" }), o.delay + 1.4 + 0.08 * i)
    })
    if (o.names.length) v.legend(svg, o, [{ label: o.names[0], tone: "is-muted" }, { label: o.names[1] ?? "", tone: "is-accent" }], labelW + 200, 24)
  }

  const bullet = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const [actual, target, top] = o.series
    const row = o.h / actual.length
    const end = o.w - 200
    actual.forEach((value, i) => {
      const cy = row * i + row / 2
      const goal = target?.[i]
      const max = top?.[i] ?? v.nice(Math.max(value, goal ?? 0) * 1.15)
      const x = scale(0, max, labelW, end)
      const ok = goal === undefined || value >= goal
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", "viz-label f"), o.delay + 0.05 * i)
      at(node("rect", { x: labelW, y: cy - 28, width: end - labelW, height: 56, rx: 10 }, svg, "viz-track f"), o.delay)
      at(node("rect", { x: labelW, y: cy - 13, width: x(value) - labelW, height: 26, rx: 6 }, svg, `viz-bar gx ${ok ? "is-accent" : "is-danger"}`), o.delay + 0.2 + 0.1 * i)
      if (goal !== undefined) at(node("rect", { x: x(goal) - 3, y: cy - 36, width: 6, height: 72, rx: 3 }, svg, "viz-marker pop"), o.delay + 0.8 + 0.1 * i)
      at(counter(svg, o, end + 32, cy + 4, value, `viz-value f is-strong ${ok ? "is-accent" : "is-danger"}`), o.delay + 0.5 + 0.1 * i)
      if (goal !== undefined) at(text(svg, end + 32, cy + 34, `${o.d.goalLabel ?? ""} ${v.fmt(o, goal)}`.trim(), "viz-note f"), o.delay + 0.9 + 0.1 * i)
    })
  }

  const funnel = (svg, o) => {
    const max = Math.max(...o.values)
    const row = o.h / o.values.length
    const labelW = Number(o.d.labelWidth ?? 320)
    const rateW = 240
    const full = o.w - labelW - rateW
    const center = labelW + full / 2
    const bar = row * 0.62
    const rates = o.values.map((value, i) => (i ? value / o.values[i - 1] : 1))
    const worst = rates.indexOf(Math.min(...rates.slice(1)))
    const widths = o.values.map((value) => Math.max((full * value) / max, 28))
    o.values.forEach((value, i) => {
      const cy = row * i + row / 2
      const width = widths[i]
      const last = i === o.values.length - 1
      const cls = last ? "is-accent" : i === 0 ? "is-muted" : `is-shade-${Math.min(i, 3)}`
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", `viz-label f${last ? " is-strong" : ""}`), o.delay + 0.1 * i)
      if (i > 0) {
        const prev = widths[i - 1]
        const top = cy - row + bar / 2
        const bottom = cy - bar / 2
        const d = `M${center - prev / 2} ${top} L${center + prev / 2} ${top} L${center + width / 2} ${bottom} L${center - width / 2} ${bottom} Z`
        at(node("path", { d }, svg, `viz-neck f${i === worst ? " is-danger" : ""}`), o.delay + 0.2 + 0.15 * i)
        at(text(svg, o.w, cy - row / 2 + 9, v.fmt(o, rates[i] * 100, "%"), `viz-value f${i === worst ? " is-strong is-danger" : ""}`, { "text-anchor": "end" }), o.delay + 0.5 + 0.15 * i)
      }
      at(node("rect", { x: center - width / 2, y: cy - bar / 2, width, height: bar, rx: 10 }, svg, `viz-bar sx ${cls}`), o.delay + 0.15 * i)
      const inside = width > 150
      at(counter(svg, o, inside ? center : center + width / 2 + 18, cy + 10, value, `viz-inside f${last && inside ? " is-on-accent" : ""}`, { "text-anchor": inside ? "middle" : "start" }), o.delay + 0.3 + 0.15 * i)
    })
  }

  const pareto = (svg, o) => {
    const plot = plotBox(o, { bottom: 64, top: 56, right: 96 })
    const total = o.values.reduce((a, b) => a + b, 0) || 1
    const y = yAxis(svg, o, plot, 0, v.nice(Math.max(...o.values)))
    const band = (plot.x1 - plot.x0) / o.values.length
    const width = band * 0.6
    const share = scale(0, 100, plot.y1, plot.y0)
    let run = 0
    const points = o.values.map((value, i) => {
      const x = plot.x0 + band * i + (band - width) / 2
      at(node("rect", { x, y: y(value), width, height: y(0) - y(value), rx: 6 }, svg, `viz-bar gy ${run / total < 0.8 ? "is-accent" : "is-muted"}`), o.delay + 0.2 + 0.07 * i)
      if (o.labels[i]) at(text(svg, x + width / 2, plot.y1 + 40, o.labels[i], "viz-label f", { "text-anchor": "middle" }), o.delay)
      run += value
      return [x + width / 2, share((run / total) * 100)]
    })
    const axis = at(node("g", {}, svg, "viz-axis f"), o.delay)
    for (const p of [0, 25, 50, 75, 100]) text(axis, plot.x1 + 16, share(p) + 8, `${p}%`, "viz-tick")
    const eighty = share(80)
    at(node("path", { d: `M${plot.x0} ${eighty} H${plot.x1}` }, svg, "viz-target f"), o.delay + 0.6)
    at(text(svg, plot.x1 - 8, eighty - 14, "80%", "viz-note is-strong f", { "text-anchor": "end" }), o.delay + 0.7)
    at(node("path", { d: v.linePath(points), pathLength: 1 }, svg, "viz-line is-ink dr"), o.delay + 0.9, 1.2)
    points.forEach(([x, py], i) => at(node("circle", { cx: x, cy: py, r: 8 }, svg, "viz-dot is-ringed pop is-ink"), o.delay + 0.9 + (1.2 * i) / Math.max(points.length - 1, 1)))
  }

  const diverging = (svg, o) => {
    const labelW = Number(o.d.labelWidth ?? 300)
    const lo = Math.min(0, ...o.values)
    const hi = Math.max(0, ...o.values)
    const pad = 170
    const x = scale(lo, hi, labelW + (lo < 0 ? pad : 20), o.w - (hi > 0 ? pad : 20))
    const center = x(0)
    const row = o.h / o.values.length
    at(node("path", { d: `M${center} 0 V${o.h}` }, svg, "axis f"), o.delay)
    o.values.forEach((value, i) => {
      const cy = row * i + row / 2
      const width = Math.abs(x(value) - center)
      const cls = value < 0 ? "is-danger" : "is-accent"
      at(text(svg, 0, cy + 9, o.labels[i] ?? "", "viz-label f"), o.delay + 0.05 * i)
      at(node("rect", { x: value < 0 ? center - width : center, y: cy - row * 0.3, width: Math.max(width, 4), height: row * 0.6, rx: 8 }, svg, `viz-bar ${value < 0 ? "gxr" : "gx"} ${cls}`), o.delay + 0.2 + 0.08 * i)
      const tx = value < 0 ? center - width - 16 : center + width + 16
      at(text(svg, tx, cy + 10, `${value > 0 ? "+" : value < 0 ? "−" : ""}${v.fmt(o, Math.abs(value))}`, `viz-value f ${cls}`, { "text-anchor": value < 0 ? "end" : "start" }), o.delay + 0.6 + 0.08 * i)
    })
  }

  Object.assign(v.types, { waterfall, lollipop, dumbbell, bullet, funnel, pareto, diverging })
})()
