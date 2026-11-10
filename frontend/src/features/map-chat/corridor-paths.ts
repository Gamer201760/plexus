export function corridorPaths(lines: number[][][]): string[] {
  const points = lines.flat()
  if (!points.length) return []
  const latitude = points.reduce((sum, point) => sum + (point[1] ?? 0), 0) / points.length
  const ratio = Math.cos((latitude * Math.PI) / 180)
  const xs = points.map((point) => (point[0] ?? 0) * ratio)
  const ys = points.map((point) => point[1] ?? 0)
  const left = Math.min(...xs)
  const bottom = Math.min(...ys)
  const width = Math.max(...xs) - left
  const height = Math.max(...ys) - bottom
  const scale = Math.min(280 / Math.max(width, 0.001), 120 / Math.max(height, 0.001))
  return lines.map((line) =>
    line
      .map((point, index) => {
        const x = 160 + ((point[0] ?? 0) * ratio - left - width / 2) * scale
        const y = 80 - ((point[1] ?? 0) - bottom - height / 2) * scale
        return `${index ? "L" : "M"}${x.toFixed(2)},${y.toFixed(2)}`
      })
      .join(" "),
  )
}
