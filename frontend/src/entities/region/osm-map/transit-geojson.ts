import type { FeatureCollection, LineString } from "geojson"
import type { components } from "@/shared/api"

type Link = components["schemas"]["LinkResponse"]
type Endpoint = Link["from"]

function position(endpoint: Endpoint): [number, number] | null {
  const { lon, lat } = endpoint
  if (
    typeof lon !== "number" ||
    typeof lat !== "number" ||
    !Number.isFinite(lon) ||
    !Number.isFinite(lat) ||
    Math.abs(lon) > 180 ||
    Math.abs(lat) > 90
  )
    return null
  return [lon, lat]
}

export function buildTransitCollection(links: readonly Link[], regionId: string | null) {
  const data: FeatureCollection<LineString> = { type: "FeatureCollection", features: [] }
  const seen = new Set<string>()
  let missing = 0
  let modeled = false
  for (const link of links) {
    if (link.region_id !== regionId || (link.mode !== "rail" && link.mode !== "air")) continue
    modeled ||= link.is_model === true
    const from = position(link.from)
    const to = position(link.to)
    if (!from || !to) {
      missing++
      continue
    }
    const key = `${link.mode}:${[from.join(","), to.join(",")].sort().join(";")}`
    if (seen.has(key)) continue
    seen.add(key)
    const delta = to[0] - from[0]
    if (Math.abs(delta) > 180) to[0] -= Math.sign(delta) * 360
    data.features.push({
      type: "Feature",
      properties: { mode: link.mode },
      geometry: { type: "LineString", coordinates: [from, to] },
    })
  }
  return { data, missing, modeled }
}
