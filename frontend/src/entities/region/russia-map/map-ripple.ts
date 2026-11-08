import { motionMs, prefersReducedMotion, readEasing } from "@/shared/motion"
import type { Box } from "./map-motion"

const SVG = "http://www.w3.org/2000/svg"

export interface Ripple {
  readonly path: string
  readonly box: Box
  readonly unit: number
  readonly colors: readonly string[]
  readonly reach: number
  readonly line: number
}

export function playRipple(group: SVGGElement, host: Element, ripple: Ripple) {
  if (prefersReducedMotion() || typeof group.animate !== "function") return
  const reach = ripple.reach * ripple.unit * 2
  const scaleX = 1 + reach / Math.max(ripple.box.width, ripple.unit)
  const scaleY = 1 + reach / Math.max(ripple.box.height, ripple.unit)
  const duration = motionMs("--dur-ripple", host)
  const easing = readEasing("--ease-out", host)
  const step = motionMs("--delay-ripple", host)
  ripple.colors.forEach((color, index) => {
    const wave = document.createElementNS(SVG, "path")
    wave.setAttribute("d", ripple.path)
    wave.setAttribute("stroke", color)
    wave.setAttribute("stroke-width", String(ripple.line))
    wave.setAttribute("vector-effect", "non-scaling-stroke")
    wave.style.transformBox = "fill-box"
    wave.style.transformOrigin = "center"
    wave.style.opacity = "0"
    group.append(wave)
    const animation = wave.animate(
      [
        { opacity: 1, transform: "none" },
        { opacity: 0, transform: `scale(${scaleX}, ${scaleY})` },
      ],
      { duration, easing, delay: index * step },
    )
    animation.onfinish = () => wave.remove()
  })
}
