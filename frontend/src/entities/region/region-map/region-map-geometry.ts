import type { components } from "@/shared/api"

export type MapLink = components["schemas"]["LinkResponse"]
export type MapSettlement = components["schemas"]["SettlementResponse"]
export type MapMode = components["schemas"]["Mode"]

export interface Endpoint {
  readonly key: string
  readonly x: number
  readonly y: number
  readonly mode: MapMode
  readonly active: boolean
}

const RADIUS_STEPS = 260
const RADIUS_FLOOR = 0.6
const RADIUS_CAP = 1.6
const POPULATION_SCALE = 70

export const ENDPOINT_SCALE = 1.25
export const ACTIVE_ENDPOINT_SCALE = 1.9

export function baseRadius(span: number) {
  return span / RADIUS_STEPS
}

export function placeRadius(population: number | null, span: number) {
  const base = baseRadius(span)
  if (population === null) return base * RADIUS_FLOOR
  return base * (RADIUS_FLOOR + Math.min(Math.sqrt(population) / POPULATION_SCALE, RADIUS_CAP))
}

export function isDrawable(link: MapLink) {
  return link.from.x !== null && link.from.y !== null && link.to.x !== null && link.to.y !== null
}

export function linkEndpoints(links: readonly MapLink[], activeId: string | null) {
  const byKey = new Map<string, Endpoint>()
  for (const link of links) {
    const active = link.id === activeId
    for (const end of [link.from, link.to]) {
      if (end.x === null || end.y === null) continue
      const key = `${end.x}:${end.y}`
      const known = byKey.get(key)
      if (known && (known.active || !active)) continue
      byKey.set(key, { key, x: end.x, y: end.y, mode: link.mode, active })
    }
  }
  return [...byKey.values()].sort((a, b) => Number(a.active) - Number(b.active))
}

export function presentModes(links: readonly MapLink[]) {
  return [...new Set(links.map((link) => link.mode))]
}
