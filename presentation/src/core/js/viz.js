(() => {
  const kit = window.deckKit
  const types = {}

  const list = (text, sep = ",") =>
    String(text ?? "")
      .split(sep)
      .map((part) => part.trim())
      .filter((part) => part !== "")

  const numbers = (text) =>
    String(text ?? "")
      .split(/[\s,]+/)
      .filter((part) => part !== "")
      .map(Number)

  const options = (host, box) => {
    const d = host.dataset
    const series = list(d.values, "|").map(numbers)
    return {
      host,
      d,
      w: box.w,
      h: box.h,
      series,
      values: series[0] ?? [],
      labels: d.labels === undefined ? [] : d.labels.split(";").map((part) => part.trim()),
      names: d.names === undefined ? [] : d.names.split(";").map((part) => part.trim()),
      accent: numbers(d.accent),
      danger: numbers(d.danger),
      unit: d.unit ?? "",
      digits: Number(d.digits ?? 0),
      delay: Number(d.delay ?? 0.3),
      flag: (name) => d[name] !== undefined && d[name] !== "false",
    }
  }

  const fmt = (o, value, unit = o.unit) => `${kit.fmt(value, o.digits)}${unit}`

  const scale = (d0, d1, r0, r1) => (value) => r0 + ((value - d0) / (d1 - d0 || 1)) * (r1 - r0)

  const tickStep = (span, count = 5) => {
    const raw = Math.abs(span) / count || 1
    const power = 10 ** Math.floor(Math.log10(raw))
    const m = raw / power
    return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * power
  }

  const nice = (value) => {
    if (value <= 0) return 1
    const step = tickStep(value)
    return Math.ceil(value / step - 1e-9) * step
  }

  const extent = (values, o) => {
    const flat = values.flat().filter(Number.isFinite)
    const lo = Math.min(0, ...flat)
    const hi = Math.max(...flat, 0)
    const step = tickStep(hi - lo)
    const min = o.d.min !== undefined ? Number(o.d.min) : Math.floor(lo / step + 1e-9) * step
    const max = o.d.max !== undefined ? Number(o.d.max) : Math.ceil(hi / step - 1e-9) * step
    return [min, max]
  }

  const decimals = (value) => {
    const text = String(Number(value.toPrecision(6)))
    return text.includes(".") ? text.split(".")[1].length : 0
  }

  const tight = (values, o, pad = 0.08) => {
    const flat = values.flat().filter(Number.isFinite)
    const lo = Math.min(...flat)
    const hi = Math.max(...flat)
    const span = hi - lo || Math.abs(hi) || 1
    const step = tickStep(span + span * pad * 2)
    const min = o.d.min !== undefined ? Number(o.d.min) : Math.floor((lo - span * pad) / step) * step
    const max = o.d.max !== undefined ? Number(o.d.max) : Math.ceil((hi + span * pad) / step) * step
    return [min, max]
  }

  const node = (tag, attrs = {}, parent = null, cls = "") => {
    const el = kit.svg(tag, attrs, parent)
    if (cls) el.setAttribute("class", cls)
    return el
  }

  const text = (parent, x, y, content, cls = "", attrs = {}) => {
    const el = node("text", { x, y, ...attrs }, parent, cls)
    el.textContent = content
    return el
  }

  const counter = (parent, o, x, y, value, cls = "", attrs = {}) => {
    const el = text(parent, x, y, fmt(o, value), `count ${cls}`.trim(), attrs)
    el.dataset.value = String(value)
    el.dataset.digits = String(o.digits)
    el.dataset.unit = o.unit
    return el
  }

  const at = (el, seconds, duration) => {
    el.style.setProperty("--d", `${seconds.toFixed(2)}s`)
    if (duration) el.style.setProperty("--t", `${duration.toFixed(2)}s`)
    return el
  }

  const tone = (o, index, series = false) => {
    if (o.danger.includes(index)) return "is-danger"
    if (o.accent.includes(index)) return "is-accent"
    if (series && !o.accent.length && index === 0) return "is-accent"
    return ""
  }

  const polar = (cx, cy, r, angle) => [cx + r * Math.cos(angle), cy + r * Math.sin(angle)]

  const arc = (cx, cy, r, a0, a1) => {
    const [x0, y0] = polar(cx, cy, r, a0)
    const [x1, y1] = polar(cx, cy, r, a1)
    const large = Math.abs(a1 - a0) > Math.PI ? 1 : 0
    return `M${x0.toFixed(1)} ${y0.toFixed(1)} A${r} ${r} 0 ${large} ${a1 > a0 ? 1 : 0} ${x1.toFixed(1)} ${y1.toFixed(1)}`
  }

  const linePath = (points, curve = false) => {
    const f = (n) => n.toFixed(1)
    if (!curve || points.length < 3) return points.map(([x, y], i) => `${i ? "L" : "M"}${f(x)} ${f(y)}`).join(" ")
    let d = `M${f(points[0][0])} ${f(points[0][1])}`
    for (let i = 0; i < points.length - 1; i += 1) {
      const p0 = points[Math.max(i - 1, 0)]
      const p1 = points[i]
      const p2 = points[i + 1]
      const p3 = points[Math.min(i + 2, points.length - 1)]
      const lo = Math.min(p1[1], p2[1])
      const hi = Math.max(p1[1], p2[1])
      const c1y = Math.min(Math.max(p1[1] + (p2[1] - p0[1]) / 6, lo), hi)
      const c2y = Math.min(Math.max(p2[1] - (p3[1] - p1[1]) / 6, lo), hi)
      d += ` C${f(p1[0] + (p2[0] - p0[0]) / 6)} ${f(c1y)} ${f(p2[0] - (p3[0] - p1[0]) / 6)} ${f(c2y)} ${f(p2[0])} ${f(p2[1])}`
    }
    return d
  }

  const yAxis = (svg, o, plot, min, max) => {
    const y = scale(min, max, plot.y1, plot.y0)
    const g = node("g", {}, svg, "viz-axis f")
    at(g, o.delay)
    const span = max - min || 1
    const isNice = (value) => {
      const m = value / 10 ** Math.floor(Math.log10(value) + 1e-9)
      return [1, 2, 2.5, 5].some((k) => Math.abs(m - k) < 1e-6)
    }
    const count = [5, 4, 6, 3, 8, 2].find((c) => isNice(span / c))
    const step = count ? span / count : tickStep(span)
    const first = count ? min : Math.ceil(min / step - 1e-9) * step
    const ticks = count ?? Math.floor((max - first) / step + 1e-9)
    const digits = Math.max(o.digits, decimals(step))
    for (let i = 0; i <= ticks; i += 1) {
      const v = first + step * i
      node("path", { d: `M${plot.x0} ${y(v).toFixed(1)} H${plot.x1}` }, g, Math.abs(v) < 1e-9 ? "axis" : "grid-line")
      if (!o.flag("noTicks")) text(g, plot.x0 - 16, y(v) + 8, kit.fmt(v, digits), "viz-tick", { "text-anchor": "end" })
    }
    return y
  }

  const plotBox = (o, pad = {}) => {
    const left = pad.left ?? (o.flag("noTicks") ? 8 : 96)
    return { x0: left, x1: o.w - (pad.right ?? 16), y0: pad.top ?? 48, y1: o.h - (pad.bottom ?? 48) }
  }

  const legend = (svg, o, items, x, y) => {
    let cursor = x
    items.forEach((item, i) => {
      const g = at(node("g", {}, svg, "viz-legend f"), o.delay + 0.1 * i)
      node("circle", { cx: cursor + 8, cy: y - 7, r: 8 }, g, `viz-swatch ${item.tone}`)
      const label = text(g, cursor + 26, y, item.label)
      cursor += 60 + label.textContent.length * 12
    })
  }

  const render = (scope = document) => {
    for (const host of scope.querySelectorAll("[data-viz]")) {
      if (host.dataset.rendered) continue
      const type = types[host.dataset.viz]
      if (!type) {
        console.error(`viz: unknown type "${host.dataset.viz}"`)
        continue
      }
      const w = Math.round(host.offsetWidth || Number(host.dataset.w) || 800)
      const h = Math.round(host.offsetHeight || Number(host.dataset.h) || 400)
      const svg = node("svg", { viewBox: `0 0 ${w} ${h}`, "aria-hidden": "true" }, null, "chart viz")
      host.append(svg)
      host.dataset.rendered = "1"
      try {
        type(svg, options(host, { w, h }))
        for (const dashed of svg.querySelectorAll(".is-dashed, .viz-link, .viz-target, .viz-today")) {
          dashed.removeAttribute("pathLength")
          dashed.classList.replace("dr", "f")
        }
      } catch (error) {
        console.error(`viz ${host.dataset.viz}`, error)
      }
    }
    kit.icons(scope)
  }

  kit.viz = {
    types,
    render,
    list,
    numbers,
    fmt,
    scale,
    nice,
    tickStep,
    extent,
    tight,
    node,
    text,
    counter,
    at,
    tone,
    polar,
    arc,
    linePath,
    yAxis,
    plotBox,
    legend,
  }
})()
