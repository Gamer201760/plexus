(() => {
  const v = window.deckKit.viz
  const { node, text, counter, at, scale, yAxis, plotBox, extent, tight, linePath, list, numbers } = v

  const xLabels = (svg, o, plot, x) => {
    const step = Math.max(1, Math.ceil(o.labels.length / 8))
    o.labels.forEach((label, i) => {
      if (!label || (i % step && i !== o.labels.length - 1)) return
      at(text(svg, x(i), plot.y1 + 40, label, "viz-label f", { "text-anchor": "middle" }), o.delay)
    })
  }

  const stepPath = (points) =>
    points.map(([px, py], i) => (i ? `H${px.toFixed(1)} V${py.toFixed(1)}` : `M${px.toFixed(1)} ${py.toFixed(1)}`)).join(" ")

  const line = (svg, o) => {
    const plot = plotBox(o, { bottom: o.labels.length ? 64 : 24, right: o.names.length ? 220 : 24 })
    const [min, max] = extent(o.series, o)
    const y = yAxis(svg, o, plot, min, max)
    const n = Math.max(...o.series.map((row) => row.length))
    const x = scale(0, n - 1, plot.x0, plot.x1)
    if (o.d.zone) {
      const [a, b] = numbers(o.d.zone)
      at(node("rect", { x: x(a), y: plot.y0, width: x(b) - x(a), height: plot.y1 - plot.y0 }, svg, "zone f"), o.delay)
    }
    if (o.flag("diagonal")) at(node("path", { d: `M${plot.x0} ${plot.y1} L${plot.x1} ${plot.y0}`, pathLength: 1 }, svg, "viz-line is-muted is-dashed dr"), o.delay + 0.2)
    const lead = o.series.findIndex((_, s) => v.tone(o, s, true) === "is-accent")
    const drawAt = (s) => (s === lead ? o.delay + 0.5 : o.delay + 0.3 + 0.1 * s)
    const drawFor = (s) => (s === lead ? 1.3 : 0.8)
    const ends = []
    o.series.forEach((row, s) => {
      const points = row.map((value, i) => [x(i), y(value)])
      const cls = v.tone(o, s, true) || "is-muted"
      const stepped = o.flag("step") && (o.d.step === "" || numbers(o.d.step).includes(s))
      const d = stepped ? stepPath(points) : linePath(points, o.flag("curve"))
      if (o.flag("area") && s === Math.max(lead, 0)) {
        const base = y(Math.max(min, 0))
        at(node("path", { d: `${d} L${points.at(-1)[0]} ${base} L${points[0][0]} ${base} Z` }, svg, "viz-area w"), drawAt(s), drawFor(s))
      }
      at(node("path", { d, pathLength: 1 }, svg, `viz-line dr ${cls}${s > 0 && o.flag("dashRest") ? " is-dashed" : ""}`), drawAt(s), drawFor(s))
      const [ex, ey] = points.at(-1)
      at(node("circle", { cx: ex, cy: ey, r: cls === "is-accent" ? 11 : 8 }, svg, `viz-dot is-ringed pop ${cls}`), drawAt(s) + drawFor(s))
      if (o.names[s]) ends.push({ s, cls, x: ex, y: ey, value: row.at(-1) })
    })
    ends.sort((a, b) => a.y - b.y)
    ends.forEach((end, k) => {
      if (k > 0) end.y = Math.max(end.y, ends[k - 1].y + 34)
      const label = at(text(svg, end.x + 24, end.y + 9, "", `viz-label f${end.cls === "is-accent" ? " is-strong is-accent" : ""}`), drawAt(end.s) + drawFor(end.s))
      const name = node("tspan", {}, label)
      name.textContent = o.names[end.s]
      if (!o.flag("noValues")) {
        const value = node("tspan", { dx: 12 }, label, "viz-end-value")
        value.textContent = v.fmt(o, end.value)
      }
    })
    const span = Math.max(n - 1, 1)
    if (o.flag("pointValues")) {
      const s = Math.max(lead, 0)
      o.series[s].forEach((value, i) => {
        at(text(svg, x(i), y(value) + 52, v.fmt(o, value), `viz-value is-strong f${i === n - 1 ? " is-accent" : ""}`, { "text-anchor": "middle" }), drawAt(s) + (drawFor(s) * i) / span + 0.1)
      })
    }
    for (const mark of list(o.d.marks, ";")) {
      const [index, label] = mark.split(":")
      const i = Number(index)
      const s = Math.max(lead, 0)
      const value = o.series[s][i]
      const when = drawAt(s) + (drawFor(s) * i) / span
      at(node("path", { d: `M${x(i)} ${y(value) - 22} V${plot.y0 + 30}`, pathLength: 1 }, svg, "viz-link dr"), when)
      at(node("circle", { cx: x(i), cy: y(value), r: 13 }, svg, "viz-dot is-ringed pop is-ink"), when)
      at(text(svg, x(i), plot.y0 + 16, label ?? "", "viz-note is-strong f", { "text-anchor": "middle" }), when + 0.1)
    }
    xLabels(svg, o, plot, x)
  }

  const band = (svg, o) => {
    const [fact, low, high, forecast] = o.series
    const plot = plotBox(o, { bottom: o.labels.length ? 64 : 24 })
    const [min, max] = tight(o.series, o, 0.15)
    const y = yAxis(svg, o, plot, min, max)
    const start = fact.length - 1
    const n = start + high.length
    const x = scale(0, n - 1, plot.x0, plot.x1)
    const top = high.map((value, i) => [x(start + i), y(value)])
    const bottom = low.map((value, i) => [x(start + i), y(value)]).reverse()
    at(node("path", { d: `${linePath(top)} ${linePath(bottom).replace("M", "L")} Z` }, svg, "viz-area is-band w"), o.delay + 1.1, 1.2)
    at(node("path", { d: linePath(fact.map((value, i) => [x(i), y(value)])), pathLength: 1 }, svg, "viz-line is-ink dr"), o.delay + 0.3, 1)
    if (forecast) at(node("path", { d: linePath(forecast.map((value, i) => [x(start + i), y(value)])), pathLength: 1 }, svg, "viz-line is-accent is-dashed dr"), o.delay + 1.2, 1)
    at(node("path", { d: `M${x(start)} ${plot.y0} V${plot.y1}` }, svg, "viz-today f"), o.delay + 1)
    if (o.d.now) at(text(svg, x(start) + 12, plot.y0 + 20, o.d.now, "viz-note is-strong f"), o.delay + 1.1)
    xLabels(svg, o, plot, x)
  }

  const spread = (items, gap, lo, hi) => {
    const sorted = [...items].sort((a, b) => a.y - b.y)
    sorted.forEach((item, k) => {
      if (k > 0) item.y = Math.max(item.y, sorted[k - 1].y + gap)
    })
    const over = sorted.length ? sorted.at(-1).y - hi : 0
    if (over > 0) sorted.forEach((item) => (item.y = Math.max(lo, item.y - over)))
    return items
  }

  const slope = (svg, o) => {
    const [from, to] = o.series
    const [min, max] = tight(o.series, o, 0.12)
    const left = Number(o.d.labelWidth ?? 380)
    const right = o.w - left
    const y = scale(min, max, o.h - 30, 90)
    at(node("path", { d: `M${left} 60 V${o.h - 10} M${right} 60 V${o.h - 10}` }, svg, "viz-guide f"), o.delay)
    if (o.names.length) {
      at(text(svg, left, 28, o.names[0], "viz-label is-strong f", { "text-anchor": "middle" }), o.delay)
      at(text(svg, right, 28, o.names[1] ?? "", "viz-label is-strong f", { "text-anchor": "middle" }), o.delay)
    }
    const rows = from.map((a, i) => ({ i, a, b: to[i], cls: v.tone(o, i) || "is-muted" }))
    const lefts = spread(rows.map((r) => ({ r, y: y(r.a) })), 36, 90, o.h - 20)
    const rights = spread(rows.map((r) => ({ r, y: y(r.b) })), 36, 90, o.h - 20)
    const order = [...rows].sort((p, q) => (p.cls === "is-muted" ? 0 : 1) - (q.cls === "is-muted" ? 0 : 1))
    order.forEach((r, k) => {
      const start = o.delay + 0.3 + 0.08 * k + (r.cls === "is-muted" ? 0 : 0.4)
      const hot = r.cls !== "is-muted"
      at(node("circle", { cx: left, cy: y(r.a), r: hot ? 11 : 8 }, svg, `viz-dot is-ringed pop ${r.cls}`), start)
      at(node("path", { d: `M${left} ${y(r.a)} L${right} ${y(r.b)}`, pathLength: 1 }, svg, `viz-line dr ${r.cls}`), start + 0.1, 0.8)
      at(node("circle", { cx: right, cy: y(r.b), r: hot ? 11 : 8 }, svg, `viz-dot is-ringed pop ${r.cls}`), start + 0.9)
      const l = lefts.find((p) => p.r === r)
      const q = rights.find((p) => p.r === r)
      at(text(svg, left - 26, l.y + 9, `${o.labels[r.i] ?? ""}  ${v.fmt(o, r.a)}`, `viz-label f ${hot ? "is-strong" : ""}`, { "text-anchor": "end" }), start)
      at(text(svg, right + 26, q.y + 9, `${v.fmt(o, r.b)}  ${o.labels[r.i] ?? ""}`, `viz-label f ${hot ? "is-strong is-accent" : ""}`), start + 1)
    })
  }

  const spark = (svg, o) => {
    const lo = Math.min(...o.values)
    const hi = Math.max(...o.values)
    const span = hi - lo || Math.abs(hi) || 1
    const min = o.d.min !== undefined ? Number(o.d.min) : lo - span * 0.45
    const max = o.d.max !== undefined ? Number(o.d.max) : hi + span * 0.08
    const x = scale(0, o.values.length - 1, 6, o.w - 14)
    const y = scale(min, max, o.h - 8, 8)
    const points = o.values.map((value, i) => [x(i), y(value)])
    const d = linePath(points, true)
    at(node("path", { d: `${d} L${o.w - 14} ${o.h} L6 ${o.h} Z` }, svg, "viz-area w"), o.delay + 0.2, 1)
    at(node("path", { d, pathLength: 1 }, svg, `viz-line dr ${o.danger.length ? "is-danger" : "is-accent"}`), o.delay, 1)
    at(node("circle", { cx: points.at(-1)[0], cy: points.at(-1)[1], r: 7 }, svg, `viz-dot pop ${o.danger.length ? "is-danger" : "is-accent"}`), o.delay + 1)
  }

  const histogram = (svg, o) => {
    const plot = plotBox(o, { bottom: 64, top: 72 })
    const y = yAxis(svg, o, plot, 0, v.nice(Math.max(...o.values)))
    const band = (plot.x1 - plot.x0) / o.values.length
    o.values.forEach((value, i) => {
      const x = plot.x0 + band * i
      at(node("rect", { x: x + 1, y: y(value), width: band - 3, height: y(0) - y(value), rx: 3 }, svg, `viz-bar gy ${v.tone(o, i) || "is-muted"}`), o.delay + 0.2 + 0.03 * i)
    })
    for (const mark of list(o.d.marks, ";")) {
      const [index, label] = mark.split(":")
      const mx = plot.x0 + band * Number(index)
      at(node("path", { d: `M${mx} ${plot.y1} V${plot.y0 - 20}`, pathLength: 1 }, svg, "viz-target dr"), o.delay + 1.1)
      at(text(svg, mx, plot.y0 - 32, label ?? "", "viz-note is-strong f", { "text-anchor": "middle" }), o.delay + 1.2)
    }
    if (o.labels.length) {
      const x = (i) => plot.x0 + (band * (i * (o.values.length - 1))) / Math.max(o.labels.length - 1, 1) + band / 2
      o.labels.forEach((label, i) => at(text(svg, x(i), plot.y1 + 40, label, "viz-label f", { "text-anchor": "middle" }), o.delay))
    }
  }

  Object.assign(v.types, { line, band, slope, spark, histogram })
  Object.assign(v, { xLabels })
})()
