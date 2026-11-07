const STEPS = 72

export function blobPath(cx: number, cy: number, radius: number, seed: number, wobble: number) {
  const points: string[] = []
  for (let step = 0; step <= STEPS; step += 1) {
    const angle = (step / STEPS) * Math.PI * 2
    const k =
      1 +
      wobble * Math.sin(3 * angle + seed) +
      wobble * 0.5 * Math.sin(5 * angle + seed * 1.7) +
      wobble * 0.3 * Math.cos(2 * angle + seed * 0.6)
    const x = cx + Math.cos(angle) * radius * k
    const y = cy + Math.sin(angle) * radius * k
    points.push(`${x.toFixed(2)} ${y.toFixed(2)}`)
  }
  return `M${points.join("L")}Z`
}
