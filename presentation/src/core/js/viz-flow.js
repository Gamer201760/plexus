(() => {
  const kit = window.deckKit
  const v = kit.viz
  const { node, text, at, scale } = v

  const sankey = (svg, o) => {
    const cols = v.numbers(o.d.cols)
    const links = o.series.map(([source, target, value], i) => ({ source, target, value, i }))
    const count = o.labels.length
    const inflow = Array(count).fill(0)
    const outflow = Array(count).fill(0)
    for (const link of links) {
      outflow[link.source] += link.value
      inflow[link.target] += link.value
    }
    const size = inflow.map((value, i) => Math.max(value, outflow[i]))
    const depth = Math.max(...cols) + 1
    const nodeW = 16
    const labelPad = Number(o.d.labelWidth ?? 220)
    const x = (c) => labelPad + (c * (o.w - 2 * labelPad - nodeW)) / Math.max(depth - 1, 1)
    const gap = 72
    const perCol = Array.from({ length: depth }, (_, c) => o.labels.map((_, i) => i).filter((i) => cols[i] === c))
    const k = Math.min(...perCol.map((ids) => (o.h - gap * (ids.length - 1)) / ids.reduce((a, i) => a + size[i], 0)))
    const pos = []
    perCol.forEach((ids) => {
      const used = ids.reduce((a, i) => a + size[i] * k, 0) + gap * (ids.length - 1)
      let y = (o.h - used) / 2
      for (const i of ids) {
        pos[i] = { y, h: size[i] * k, out: 0, in: 0 }
        y += size[i] * k + gap
      }
    })
    links.forEach((link) => {
      const a = pos[link.source]
      const b = pos[link.target]
      const h = link.value * k
      const y0 = a.y + a.out + h / 2
      const y1 = b.y + b.in + h / 2
      a.out += h
      b.in += h
      const x0 = x(cols[link.source]) + nodeW
      const x1 = x(cols[link.target])
      const mx = (x0 + x1) / 2
      const path = node("path", { d: `M${x0} ${y0} C${mx} ${y0} ${mx} ${y1} ${x1} ${y1}`, pathLength: 1 }, svg, `viz-flow dr ${v.tone(o, link.i)}`)
      path.style.strokeWidth = Math.max(h, 2)
      at(path, o.delay + 0.3 + 0.35 * cols[link.source] + 0.04 * link.i, 0.9)
    })
    o.labels.forEach((label, i) => {
      const p = pos[i]
      if (!p) return
      const c = cols[i]
      at(node("rect", { x: x(c), y: p.y, width: nodeW, height: Math.max(p.h, 4), rx: nodeW / 2 }, svg, "viz-node-bar s"), o.delay + 0.35 * c)
      const right = c === depth - 1
      const middle = c > 0 && !right
      const tx = middle ? x(c) + nodeW / 2 : right ? x(c) + nodeW + 18 : x(c) - 18
      const ty = middle ? p.y - 44 : p.y + p.h / 2 - 4
      const anchor = middle ? "middle" : right ? "start" : "end"
      at(text(svg, tx, ty, label, "viz-label is-strong is-halo f", { "text-anchor": anchor }), o.delay + 0.35 * c + 0.2)
      at(text(svg, tx, ty + 28, v.fmt(o, size[i]), "viz-tick f", { "text-anchor": anchor }), o.delay + 0.35 * c + 0.3)
    })
  }

  const gantt = (svg, o) => {
    const left = Number(o.d.labelWidth ?? 320)
    const top = o.names.length ? 56 : 8
    const max = Number(o.d.max ?? Math.max(...o.series.map((row) => row[1])))
    const min = Number(o.d.min ?? 0)
    const x = scale(min, max, left, o.w - 8)
    const row = (o.h - top) / o.series.length
    o.names.forEach((name, i) => {
      const tx = left + ((o.w - 8 - left) * i) / Math.max(o.names.length - 1, 1)
      at(text(svg, tx, 28, name, "viz-tick f", { "text-anchor": i === 0 ? "start" : i === o.names.length - 1 ? "end" : "middle" }), o.delay)
      at(node("path", { d: `M${tx} 44 V${o.h}` }, svg, "grid-line f"), o.delay)
    })
    o.series.forEach(([start, end], i) => {
      const cy = top + row * i + row / 2
      const cls = v.tone(o, i) || "is-shade-1"
      at(text(svg, 0, cy + 8, o.labels[i] ?? "", `viz-label f ${v.tone(o, i) ? "is-strong" : ""}`), o.delay + 0.05 * i)
      at(node("rect", { x: x(start), y: cy - row * 0.3, width: Math.max(x(end) - x(start), 8), height: row * 0.6, rx: 8 }, svg, `viz-bar gx ${cls}`), o.delay + 0.2 + 0.12 * i)
      if (o.flag("durations")) {
        const inside = x(end) - x(start) > 120
        at(text(svg, inside ? x(end) - 16 : x(end) + 14, cy + 9, v.fmt(o, end - start), `${inside ? "viz-inside" : "viz-value"} f${inside && cls === "is-accent" ? " is-on-accent" : ""}`, { "text-anchor": inside ? "end" : "start" }), o.delay + 0.5 + 0.12 * i)
      }
    })
    if (o.d.now !== undefined) {
      const nx = x(Number(o.d.now))
      at(node("path", { d: `M${nx} ${top - 10} V${o.h}`, pathLength: 1 }, svg, "viz-today dr"), o.delay + 1.2)
      if (o.d.nowLabel) at(text(svg, nx + 10, top + 2, o.d.nowLabel, "viz-note is-strong f"), o.delay + 1.3)
    }
  }

  const network = (svg, o) => {
    const rng = kit.rng(Number(o.d.seed ?? 5))
    const n = o.labels.length
    const cx = o.w / 2
    const cy = o.h / 2
    const placed = v.list(o.d.pos, "|").map(v.numbers)
    const pts = o.labels.map((_, i) => {
      if (placed[i]) return [60 + placed[i][0] * (o.w - 120), 40 + placed[i][1] * (o.h - 110)]
      if (i === 0 && o.flag("center")) return [cx, cy]
      const k = o.flag("center") ? i - 1 : i
      const m = o.flag("center") ? n - 1 : n
      const a = -Math.PI / 2 + (k * Math.PI * 2) / m + (rng() - 0.5) * 0.25
      const shrink = 0.72 + rng() * 0.28
      return [cx + (o.w / 2 - 140) * shrink * Math.cos(a), cy + (o.h / 2 - 50) * shrink * Math.sin(a)]
    })
    const alert = v.numbers(o.d.alert)
    o.series.forEach(([a, b], i) => {
      if (!pts[a] || !pts[b]) return
      const hot = alert.includes(i)
      const edge = at(node("path", { d: `M${pts[a][0]} ${pts[a][1]} L${pts[b][0]} ${pts[b][1]}`, pathLength: 1 }, svg, `viz-edge dr${hot ? " is-danger" : ""}`), o.delay + (hot ? 1.1 : 0.4) + 0.03 * i, hot ? 0.6 : 0.5)
      if (hot) edge.style.strokeWidth = "5px"
    })
    const sides = [
      [0, 1],
      [0, -1],
      [1, 0],
      [-1, 0],
    ]
    const blocked = (i, [sx, sy]) =>
      o.series.filter(([a, b]) => a === i || b === i).filter(([a, b]) => {
        const other = pts[a === i ? b : a]
        if (!other) return false
        const dx = other[0] - pts[i][0]
        const dy = other[1] - pts[i][1]
        return sy ? dy * sy > 0 && Math.abs(dx) < Math.abs(dy) * 1.25 : dx * sx > 0 && Math.abs(dy) < Math.abs(dx) * 0.8
      }).length
    pts.forEach(([x, y], i) => {
      const cls = v.tone(o, i) || "is-muted"
      const big = cls !== "is-muted"
      const r = big ? 24 : 14
      const fits = ([sx, sy]) => (sy < 0 ? y - r - 16 > 28 : true) && (sx > 0 ? x < o.w - 260 : true) && (sx < 0 ? x > 260 : true)
      const side = sides.filter(fits).reduce((best, s) => (blocked(i, s) < blocked(i, best) ? s : best))
      const pos = side[1] > 0 ? [x, y + r + 34, "middle"] : side[1] < 0 ? [x, y - r - 16, "middle"] : side[0] > 0 ? [x + r + 14, y + 8, "start"] : [x - r - 14, y + 8, "end"]
      at(node("circle", { cx: x, cy: y, r }, svg, `viz-dot is-ringed pop ${cls}`), o.delay + 0.1 + 0.04 * i)
      at(text(svg, pos[0], pos[1], o.labels[i], `viz-label is-halo f${big ? " is-strong" : ""}`, { "text-anchor": pos[2] }), o.delay + 0.5 + 0.04 * i)
    })
  }

  Object.assign(v.types, { sankey, gantt, network })
})()
