import type { Map as LibreMap, LngLatBoundsLike } from "maplibre-gl"
import type { ChatMapCommand } from "@/shared/api/chat-map"
import type { BoundaryAtlas, LonLatBounds } from "./boundary-geojson"
import { NO_REGION, SELECTED_LAYER } from "./osm-style"

export function corners(bounds: LonLatBounds): LngLatBoundsLike {
  return [
    [bounds[0], bounds[1]],
    [bounds[2], bounds[3]],
  ]
}

export function regionFrame(atlas: BoundaryAtlas, ids: readonly string[]): LonLatBounds | null {
  const features = ids.map((id) => atlas.featureOf.get(id))
  if (!features.length || features.some((feature) => !feature)) return null
  const bounds = features.flatMap((feature) => (feature ? [feature.bounds] : []))
  return [
    Math.min(...bounds.map((box) => box[0])),
    Math.min(...bounds.map((box) => box[1])),
    Math.max(...bounds.map((box) => box[2])),
    Math.max(...bounds.map((box) => box[3])),
  ]
}

export function focusRegions(
  map: LibreMap,
  atlas: BoundaryAtlas,
  ids: readonly string[],
  duration: number,
) {
  const frame = ids.length ? regionFrame(atlas, ids) : atlas.home
  if (!frame) return
  map.stop()
  const selected = ids.map((id) => atlas.featureOf.get(id)?.id ?? NO_REGION)
  map.setFilter(SELECTED_LAYER, ["in", ["id"], ["literal", selected]])
  map.getContainer().dataset.focusRegions = ids.join(",")
  map.fitBounds(corners(frame), {
    padding: ids.length ? { top: 96, right: 56, bottom: 144, left: 56 } : 24,
    maxZoom: ids.length ? 8.5 : 18,
    duration,
    curve: 1.25,
    essential: false,
    linear: false,
  })
}

export function focusIds(
  command: ChatMapCommand | null | undefined,
  selectedId: string | null,
): readonly string[] {
  if (command?.action === "focus") return command.region_ids
  if (command?.action === "reset" || !selectedId) return []
  return [selectedId]
}
