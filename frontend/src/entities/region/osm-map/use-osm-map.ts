import {
  Map as LibreMap,
  type LngLatBoundsLike,
  type MapLayerMouseEvent,
  type MapOptions,
} from "maplibre-gl"
import { useCallback, useEffect, useMemo, useRef } from "react"
import { motionMs, useReducedMotion } from "@/shared/motion"
import type { BoundaryAtlas, LonLatBounds } from "./boundary-geojson"
import {
  buildStyle,
  FILL_LAYER,
  NO_REGION,
  REGIONS_SOURCE,
  readMapColors,
  SELECTED_LAYER,
  selectionFilter,
} from "./osm-style"

const HOME_PADDING = 24
const FOCUS_PADDING = 56
const FOCUS_MAX_ZOOM = 8.5
const MIN_ZOOM = 1.4
const MAX_ZOOM = 18
const EDGE = 14

export type MapStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface MapControls {
  readonly zoomIn: (instant?: boolean) => void
  readonly zoomOut: (instant?: boolean) => void
  readonly reset: (instant?: boolean) => void
}

export interface OsmMapOptions {
  readonly atlas: BoundaryAtlas
  readonly stepOf: (id: string) => number
  readonly selectedId: string | null
  readonly onSelect: (id: string) => void
  readonly onHover: (id: string | null, x: number, y: number) => void
}

function corners(bounds: LonLatBounds): LngLatBoundsLike {
  return [
    [bounds[0], bounds[1]],
    [bounds[2], bounds[3]],
  ]
}

function margin(bounds: LonLatBounds): LonLatBounds {
  return [
    bounds[0] - EDGE,
    bounds[1] - EDGE / 2,
    bounds[2] + EDGE,
    Math.min(85, bounds[3] + EDGE / 2),
  ]
}

export function useOsmMap({ atlas, stepOf, selectedId, onSelect, onHover }: OsmMapOptions) {
  const container = useRef<HTMLDivElement | null>(null)
  const engine = useRef<LibreMap | null>(null)
  const ready = useRef(false)
  const hovered = useRef<number | null>(null)
  const reduced = useReducedMotion()
  const state = useRef({ atlas, stepOf, selectedId, onSelect, onHover, reduced })
  state.current = { atlas, stepOf, selectedId, onSelect, onHover, reduced }

  const duration = useCallback(
    (instant?: boolean) =>
      instant || state.current.reduced
        ? 0
        : motionMs("--dur-panel", container.current ?? undefined),
    [],
  )

  const paintSteps = useCallback(() => {
    const map = engine.current
    if (!map || !ready.current) return
    for (const [regionId, feature] of state.current.atlas.featureOf)
      map.setFeatureState(
        { source: REGIONS_SOURCE, id: feature.id },
        { step: state.current.stepOf(regionId) },
      )
  }, [])

  const setHover = useCallback((id: number | null) => {
    const map = engine.current
    if (!map || !ready.current || hovered.current === id) return
    if (hovered.current !== null)
      map.setFeatureState({ source: REGIONS_SOURCE, id: hovered.current }, { hover: false })
    if (id !== null) map.setFeatureState({ source: REGIONS_SOURCE, id }, { hover: true })
    map.getCanvas().style.cursor = id === null ? "" : "pointer"
    hovered.current = id
  }, [])

  const aim = useCallback(
    (instant?: boolean) => {
      const map = engine.current
      if (!map || !ready.current) return
      const { atlas: current, selectedId: selected } = state.current
      const target = selected === null ? undefined : current.featureOf.get(selected)
      map.setFilter(SELECTED_LAYER, selectionFilter(target?.id ?? NO_REGION))
      if (target)
        map.fitBounds(corners(target.bounds), {
          padding: FOCUS_PADDING,
          maxZoom: FOCUS_MAX_ZOOM,
          duration: duration(instant),
        })
      else
        map.fitBounds(corners(current.home), { padding: HOME_PADDING, duration: duration(instant) })
    },
    [duration],
  )

  useEffect(() => {
    const element = container.current
    if (!element || atlas.collection.features.length === 0) return
    const options: MapOptions = {
      container: element,
      style: buildStyle(readMapColors(element), atlas.collection),
      bounds: corners(atlas.home),
      fitBoundsOptions: { padding: HOME_PADDING },
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      maxBounds: corners(margin(atlas.home)),
      attributionControl: false,
      fadeDuration: state.current.reduced ? 0 : motionMs("--dur-fast", element),
    }
    const map = new LibreMap(options)
    engine.current = map
    const resize = new ResizeObserver(() => map.resize())
    resize.observe(element)
    const clearHover = () => {
      setHover(null)
      state.current.onHover(null, 0, 0)
    }
    const onMove = (event: MapLayerMouseEvent) => {
      if (map.isMoving()) return
      const id = event.features?.[0]?.id
      const numeric = typeof id === "number" ? id : null
      setHover(numeric)
      const region = numeric === null ? null : (state.current.atlas.regionOf.get(numeric) ?? null)
      state.current.onHover(region, event.originalEvent.clientX, event.originalEvent.clientY)
    }
    const onClick = (event: MapLayerMouseEvent) => {
      const id = event.features?.[0]?.id
      const region = typeof id === "number" ? state.current.atlas.regionOf.get(id) : undefined
      if (region) state.current.onSelect(region)
    }
    const markView = () => {
      element.dataset.zoom = map.getZoom().toFixed(3)
      const center = map.getCenter()
      element.dataset.center = `${center.lng.toFixed(3)},${center.lat.toFixed(3)}`
    }
    map.on("load", () => {
      ready.current = true
      paintSteps()
      aim(true)
      markView()
    })
    map.on("moveend", markView)
    map.on("mousemove", FILL_LAYER, onMove)
    map.on("mouseleave", FILL_LAYER, clearHover)
    map.on("movestart", clearHover)
    map.on("click", FILL_LAYER, onClick)
    return () => {
      ready.current = false
      hovered.current = null
      engine.current = null
      resize.disconnect()
      map.remove()
    }
  }, [atlas, paintSteps, aim, setHover])

  // biome-ignore lint/correctness/useExhaustiveDependencies: Repaint when data read through the latest-state ref changes.
  useEffect(() => {
    paintSteps()
  }, [paintSteps, atlas, stepOf])

  // biome-ignore lint/correctness/useExhaustiveDependencies: Ref-backed camera callback must react to selection changes.
  useEffect(() => {
    aim()
  }, [aim, atlas, selectedId])

  const controls = useMemo<MapControls>(
    () => ({
      zoomIn: (instant) => engine.current?.zoomIn({ duration: duration(instant) }),
      zoomOut: (instant) => engine.current?.zoomOut({ duration: duration(instant) }),
      reset: (instant) => {
        const map = engine.current
        if (map)
          map.fitBounds(corners(state.current.atlas.home), {
            padding: HOME_PADDING,
            duration: duration(instant),
          })
      },
    }),
    [duration],
  )

  return { container, controls }
}
