import { execFileSync } from "node:child_process"
import { createHash } from "node:crypto"
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join } from "node:path"

const source = new URL("../public/geo/region-paths.json", import.meta.url)
const target = new URL("../public/geo/region-paths-low.json", import.meta.url)
const contents = readFileSync(source, "utf8")
const document = JSON.parse(contents)
const features = document.regions.map((region) => ({
  type: "Feature",
  properties: { id: region.id },
  geometry: {
    type: "MultiPolygon",
    coordinates: [...region.path.matchAll(/M([^M]+)Z/g)].map((match) => {
      const ring = [...match[1].matchAll(/(-?\d*\.?\d+)[ ,](-?\d*\.?\d+)/g)]
        .map((point) => [Number(point[1]), Number(point[2])])
      if (String(ring[0]) !== String(ring.at(-1))) ring.push(ring[0])
      return [ring]
    }),
  },
}))
const directory = mkdtempSync(join(tmpdir(), "plexus-map-detail-"))
try {
  const input = join(directory, "regions.json")
  const output = join(directory, "simplified.json")
  writeFileSync(input, JSON.stringify({ type: "FeatureCollection", features }))
  execFileSync("npx", ["--yes", "mapshaper@0.7.101", "-i", input,
    "-simplify", "dp", "interval=0.3", "planar", "keep-shapes", "stats",
    "-o", output, "format=geojson", "precision=0.1"], { stdio: "inherit" })
  const result = JSON.parse(readFileSync(output, "utf8"))
  const regions = result.features.map((feature) => {
    if (!feature.geometry) throw new Error(`Missing geometry for ${feature.properties.id}`)
    const polygons = feature.geometry.type === "Polygon" ? [feature.geometry.coordinates] : feature.geometry.coordinates
    const path = polygons.flatMap((polygon) => polygon.map((ring) =>
      `M${ring.map(([x, y]) => `${x},${y}`).join("L")}Z`)).join(" ")
    return { id: feature.properties.id, path }
  })
  if (regions.length !== document.regions.length) throw new Error("Region count changed")
  writeFileSync(target, JSON.stringify({
    source_sha256: createHash("sha256").update(contents).digest("hex"),
    method: "mapshaper 0.7.101, planar Douglas-Peucker, interval 0.3, keep-shapes",
    regions,
  }) + "\n")
} finally {
  rmSync(directory, { recursive: true, force: true })
}
