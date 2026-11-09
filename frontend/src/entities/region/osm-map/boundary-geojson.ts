import type { Feature, FeatureCollection, MultiPolygon } from "geojson"

export interface RegionBoundary {
  readonly id: string
  readonly name: string
  readonly bounds: readonly number[]
  readonly polygons: number[][][][]
}

export type LonLatBounds = readonly [number, number, number, number]

export interface BoundaryFeature {
  readonly id: number
  readonly bounds: LonLatBounds
}

export interface BoundaryAtlas {
  readonly collection: FeatureCollection<MultiPolygon>
  readonly regionOf: ReadonlyMap<number, string>
  readonly featureOf: ReadonlyMap<string, BoundaryFeature>
  readonly home: LonLatBounds
}

const RUSSIA: LonLatBounds = [19, 41, 191, 82]

function widen(total: LonLatBounds | null, bounds: LonLatBounds): LonLatBounds {
  if (total === null) return bounds
  return [
    Math.min(total[0], bounds[0]),
    Math.min(total[1], bounds[1]),
    Math.max(total[2], bounds[2]),
    Math.max(total[3], bounds[3]),
  ]
}

export function buildBoundaryAtlas(regions: readonly RegionBoundary[]): BoundaryAtlas {
  const features: Feature<MultiPolygon>[] = []
  const regionOf = new Map<number, string>()
  const featureOf = new Map<string, BoundaryFeature>()
  let home: LonLatBounds | null = null
  for (const region of regions) {
    const id = Number(region.id)
    const [west, south, east, north] = region.bounds
    if (!Number.isFinite(id) || regionOf.has(id)) continue
    if (west === undefined || south === undefined || east === undefined || north === undefined)
      continue
    const bounds: LonLatBounds = [west, south, east, north]
    features.push({
      type: "Feature",
      id,
      properties: { name: region.name },
      geometry: { type: "MultiPolygon", coordinates: region.polygons },
    })
    regionOf.set(id, region.id)
    featureOf.set(region.id, { id, bounds })
    home = widen(home, bounds)
  }
  return {
    collection: { type: "FeatureCollection", features },
    regionOf,
    featureOf,
    home: home ?? RUSSIA,
  }
}
