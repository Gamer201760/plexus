import type { FeatureCollection, Point } from "geojson"
import {
  type GeoJSONSource,
  type Map as LibreMap,
  type MapLayerMouseEvent,
  Popup,
} from "maplibre-gl"
import { type RefObject, useEffect } from "react"
import type { AirportCatalog } from "@/shared/api/airports"
import { useTranslation } from "@/shared/i18n"
import styles from "./osm-map.module.css"

export const AIRPORT_LAYER = "airport-points"

export function useAirportLayer(
  engine: RefObject<LibreMap | null>,
  catalog: AirportCatalog | undefined,
  ready: boolean,
) {
  const { t } = useTranslation()
  useEffect(() => {
    const map = engine.current
    if (!ready || !map || !catalog) return
    const data: FeatureCollection<Point> = {
      type: "FeatureCollection",
      features: catalog.airports.map((airport) => ({
        type: "Feature",
        properties: {
          id: airport.id,
          name: airport.name,
          iata: airport.iata,
          scheduled: airport.scheduled,
        },
        geometry: { type: "Point", coordinates: [airport.longitude, airport.latitude] },
      })),
    }
    if (!map.getSource(AIRPORT_LAYER)) {
      const style = getComputedStyle(map.getContainer())
      map.addSource(AIRPORT_LAYER, { type: "geojson", data })
      map.addLayer({
        id: AIRPORT_LAYER,
        type: "circle",
        source: AIRPORT_LAYER,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 3, 8, 6],
          "circle-color": style.getPropertyValue("--mode-air").trim(),
          "circle-stroke-color": style.getPropertyValue("--surface-base").trim(),
          "circle-stroke-width": 2,
        },
      })
    } else (map.getSource(AIRPORT_LAYER) as GeoJSONSource).setData(data)
    const popup = new Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: getComputedStyle(map.getContainer()).getPropertyValue("--legend-width").trim(),
      className: styles.airportPopup ?? "",
    })
    const show = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0]
      if (feature?.geometry.type !== "Point") return
      const properties = feature.properties
      const x = feature.geometry.coordinates[0]
      const y = feature.geometry.coordinates[1]
      if (x === undefined || y === undefined) return
      popup
        .setLngLat([x, y])
        .setText(
          t("map:airports.detail", {
            name: properties.name,
            code: properties.iata || properties.id,
          }),
        )
        .addTo(map)
    }
    const hide = () => {
      popup.remove()
    }
    map.on("mouseenter", AIRPORT_LAYER, show)
    map.on("click", AIRPORT_LAYER, show)
    map.on("mouseleave", AIRPORT_LAYER, hide)
    map.getContainer().dataset.airportCount = String(data.features.length)
    return () => {
      popup.remove()
      map.off("mouseenter", AIRPORT_LAYER, show)
      map.off("click", AIRPORT_LAYER, show)
      map.off("mouseleave", AIRPORT_LAYER, hide)
    }
  }, [engine, catalog, ready, t])
}
