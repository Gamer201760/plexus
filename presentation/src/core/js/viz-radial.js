(() => {
  const v = window.deckKit.viz
  const { node, text, counter, at, arc, polar } = v
  const TAU = Math.PI * 2

  const shade = (o, i) => v.tone(o, i) || (o.flag("rest") && i > 0 ? "is-faint" : i === 0 && !o.accent.length ? "is-accent" : `is-shade-${Math.min(i, 3)}`)

  const donut = (svg, o) => {
    const size = Math.min(o.w, o.h)
    const cx = o.flag("legend") ? size / 2 : o.w / 2
    const cy = o.h / 2
    const r = size / 2 - 40
    const thick = Number(o.d.thick ?? r * 0.3)
    const total = o.values.reduce((a, b) => a + b, 0) || 1
    node("circle", { cx, cy, r }, svg, "viz-ring-track").style.strokeWidth = thick
    let angle = -Math.PI / 2
    o.values.forEach((value, i) => {
      const sweep = (value / total) * TAU
      const gap = o.values.length > 1 ? 0.012 : 0
      const path = at(node("path", { d: arc(cx, cy, r, angle + gap, angle + sweep - gap), pathLength: 1 }, svg, `viz-arc dr ${shade(o, i)}`), o.delay + 0.2 + 0.25 * i, 0.7)
      path.style.strokeWidth = thick
      angle += sweep
    })
    if (o.d.center !== undefined) {
      const big = at(counter(svg, o, cx, cy + (o.d.caption ? 8 : 24), Number(o.d.center), "viz-center f", { "text-anchor": "middle" }), o.delay + 0.4)
      big.style.fontSize = `${Math.round(r * 0.42)}px`
    }
    if (o.d.caption) at(text(svg, cx, cy + 56, o.d.caption, "viz-label f", { "text-anchor": "middle" }), o.delay + 0.5)
    if (o.flag("legend")) {
      const x = size + 72
      const valueX = Math.min(o.w, x + Number(o.d.legendWidth ?? 600))
      const row = Math.min(80, (o.h - 40) / o.values.length)
      const top = cy - (row * o.values.length) / 2 + row / 2
      o.values.forEach((value, i) => {
        const g = at(node("g", {}, svg, "a"), o.delay + 0.5 + 0.12 * i)
        node("circle", { cx: x + 12, cy: top + row * i - 8, r: 12 }, g, `viz-swatch ${shade(o, i)}`)
        text(g, x + 40, top + row * i, o.labels[i] ?? "", "viz-label")
        text(g, valueX, top + row * i, v.fmt(o, (value / total) * 100, "%"), `viz-value${i === 0 ? " is-strong is-accent" : ""}`, { "text-anchor": "end" })
        if (i < o.values.length - 1) node("path", { d: `M${x} ${top + row * i + row / 2 - 6} H${valueX}` }, g, "viz-guide")
      })
    }
  }

  const gauge = (svg, o) => {
    const min = Number(o.d.min ?? 0)
    const max = Number(o.d.max ?? 100)
    const value = o.values[0] ?? 0
    const cx = o.w / 2
    const r = Math.min(o.w / 2 - 70, (o.h - 110) * 0.92)
    const cy = r + 60
    const thick = r * 0.2
    const start = Math.PI
    const toAngle = (x) => start + ((x - min) / (max - min || 1)) * Math.PI
    node("path", { d: arc(cx, cy, r, start, TAU) }, svg, "viz-ring-track").style.strokeWidth = thick
    for (const [index, zone] of v.list(o.d.zones, ";").entries()) {
      const [a, b] = v.numbers(zone)
      const z = at(node("path", { d: arc(cx, cy, r + thick * 0.5 + 18, toAngle(a), toAngle(b)), pathLength: 1 }, svg, `viz-arc dr ${index ? "is-good" : "is-danger"}`), o.delay + 0.1)
      z.style.strokeWidth = 8
    }
    const fill = at(node("path", { d: arc(cx, cy, r, start, toAngle(value)), pathLength: 1 }, svg, `viz-arc dr ${o.danger.length ? "is-danger" : "is-accent"}`), o.delay + 0.2, 1.2)
    fill.style.strokeWidth = thick
    if (o.d.target !== undefined) {
      const ta = toAngle(Number(o.d.target))
      const [x0, y0] = polar(cx, cy, r - thick * 0.75, ta)
      const [x1, y1] = polar(cx, cy, r + thick * 0.5 + 30, ta)
      at(node("path", { d: `M${x0} ${y0} L${x1} ${y1}` }, svg, "viz-needle f"), o.delay + 1.2)
      const [lx, ly] = polar(cx, cy, r + thick * 0.5 + 60, ta)
      at(text(svg, lx, ly + 8, `${o.d.targetLabel ?? ""} ${v.fmt(o, Number(o.d.target))}`.trim(), "viz-note is-strong f", { "text-anchor": lx > cx ? "start" : "end" }), o.delay + 1.3)
    }
    const big = at(counter(svg, o, cx, cy - 16, value, "viz-center f", { "text-anchor": "middle" }), o.delay + 0.2)
    big.style.fontSize = `${Math.round(r * 0.4)}px`
    at(text(svg, cx - r, cy + 44, v.fmt(o, min), "viz-tick f", { "text-anchor": "middle" }), o.delay)
    at(text(svg, cx + r, cy + 44, v.fmt(o, max), "viz-tick f", { "text-anchor": "middle" }), o.delay)
    if (o.d.caption) at(text(svg, cx, cy + 40, o.d.caption, "viz-label f", { "text-anchor": "middle" }), o.delay + 0.5)
  }

  const rings = (svg, o) => {
    const size = Math.min(o.h, o.w * 0.5)
    const cx = size / 2
    const cy = o.h / 2
    const thick = Math.min(58, size / (o.values.length * 3.6))
    const row = Math.min(150, o.h / o.values.length)
    const top = cy - (row * o.values.length) / 2
    o.values.forEach((value, i) => {
      const r = size / 2 - thick / 2 - 4 - i * (thick + 12)
      const max = v.numbers(o.d.max)[i] ?? 100
      node("circle", { cx, cy, r }, svg, "viz-ring-track").style.strokeWidth = thick
      const share = Math.min(value / max, 0.999)
      const path = at(node("path", { d: arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + share * TAU), pathLength: 1 }, svg, `viz-arc is-round dr ${shade(o, i)}`), o.delay + 0.2 + 0.2 * i, 1.1)
      path.style.strokeWidth = thick
      const g = at(node("g", {}, svg, "a"), o.delay + 0.5 + 0.15 * i)
      const x = size + 96
      node("circle", { cx: x + 14, cy: top + row * i + 40, r: 14 }, g, `viz-swatch ${shade(o, i)}`)
      text(g, x + 48, top + row * i + 49, o.labels[i] ?? "", "viz-label")
      const val = counter(g, o, x + 48, top + row * i + 112, value, "viz-big")
      val.style.fontSize = "64px"
    })
  }

  const radar = (svg, o) => {
    const cx = o.w / 2
    const cy = o.h / 2 + 10
    const r = Math.min(o.w, o.h) / 2 - 70
    const n = o.labels.length || o.values.length
    const max = Number(o.d.max ?? Math.max(...o.series.flat()))
    const angle = (i) => -Math.PI / 2 + (i * TAU) / n
    for (let ring = 1; ring <= 4; ring += 1) {
      const pts = Array.from({ length: n }, (_, i) => polar(cx, cy, (r * ring) / 4, angle(i)))
      at(node("path", { d: `${v.linePath(pts)} Z` }, svg, "grid-line f"), o.delay)
    }
    for (let i = 0; i < n; i += 1) {
      const [x, y] = polar(cx, cy, r, angle(i))
      at(node("path", { d: `M${cx} ${cy} L${x} ${y}` }, svg, "grid-line f"), o.delay)
      const [lx, ly] = polar(cx, cy, r + 40, angle(i))
      at(text(svg, lx, ly + 8, o.labels[i] ?? "", "viz-label f", { "text-anchor": Math.abs(lx - cx) < 10 ? "middle" : lx > cx ? "start" : "end" }), o.delay + 0.1)
    }
    const order = o.series.map((_, s) => s).sort((a, b) => (v.tone(o, a, true) ? 1 : 0) - (v.tone(o, b, true) ? 1 : 0))
    order.forEach((s, k) => {
      const row = o.series[s]
      const pts = row.map((value, i) => polar(cx, cy, (r * value) / max, angle(i)))
      const cls = v.tone(o, s, true) || "is-muted"
      const when = o.delay + 0.4 + 0.35 * k
      const shape = at(node("path", { d: `${v.linePath(pts)} Z` }, svg, `viz-shape gc ${cls}${cls === "is-muted" && k % 2 ? " is-dashed" : ""}`), when, 0.8)
      shape.style.transformOrigin = `${cx}px ${cy}px`
      if (cls !== "is-muted") pts.forEach(([x, y], i) => at(node("circle", { cx: x, cy: y, r: 9 }, svg, `viz-dot is-ringed pop ${cls}`), when + 0.6 + 0.04 * i))
    })
    if (o.names.length) v.legend(svg, o, o.names.map((label, s) => ({ label, tone: v.tone(o, s, true) || "is-muted" })), 0, 24)
  }

  const polarBars = (svg, o) => {
    const cx = o.w / 2
    const cy = o.h / 2
    const outer = Math.min(o.w, o.h) / 2 - 60
    const inner = outer * 0.38
    const max = Number(o.d.max ?? Math.max(...o.values))
    const n = o.values.length
    const sweep = TAU / n
    at(node("circle", { cx, cy, r: outer }, svg, "viz-guide f"), o.delay)
    at(node("circle", { cx, cy, r: inner - 10 }, svg, "viz-guide f"), o.delay)
    o.values.forEach((value, i) => {
      const a0 = -Math.PI / 2 + i * sweep + 0.03
      const a1 = a0 + sweep - 0.06
      const r = inner + ((outer - inner) * value) / max
      const [x0, y0] = polar(cx, cy, inner, a0)
      const [x1, y1] = polar(cx, cy, r, a0)
      const [x2, y2] = polar(cx, cy, r, a1)
      const [x3, y3] = polar(cx, cy, inner, a1)
      const d = `M${x0} ${y0} L${x1} ${y1} A${r} ${r} 0 0 1 ${x2} ${y2} L${x3} ${y3} A${inner} ${inner} 0 0 0 ${x0} ${y0} Z`
      const bar = at(node("path", { d }, svg, `viz-bar gc ${v.tone(o, i) || "is-shade-2"}`), o.delay + 0.2 + 0.035 * i, 0.6)
      bar.style.transformOrigin = `${cx}px ${cy}px`
      if (o.labels[i]) {
        const mid = a0 + sweep / 2 - 0.03
        const [t0x, t0y] = polar(cx, cy, outer + 6, mid)
        const [t1x, t1y] = polar(cx, cy, outer + 18, mid)
        at(node("path", { d: `M${t0x} ${t0y} L${t1x} ${t1y}` }, svg, "axis f"), o.delay)
        const [lx, ly] = polar(cx, cy, outer + 42, mid)
        at(text(svg, lx, ly + 8, o.labels[i], "viz-tick f", { "text-anchor": "middle" }), o.delay + 0.1)
      }
    })
    if (o.d.center) at(text(svg, cx, cy + 9, o.d.center, "viz-label is-strong f", { "text-anchor": "middle" }), o.delay + 0.6)
  }

  Object.assign(v.types, { donut, gauge, rings, radar, polar: polarBars })
})()
