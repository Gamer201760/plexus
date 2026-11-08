import type { Route } from "@/entities/region"

export interface Stop {
  readonly id: string
  readonly x: number
  readonly y: number
  readonly sweep: number
}

export interface HubRoute {
  readonly id: string
  readonly path: string
  readonly x: number
  readonly y: number
}

export interface Hub {
  readonly id: string
  readonly name: string
  readonly x: number
  readonly y: number
  readonly count: number
  readonly below: boolean
  readonly routes: readonly HubRoute[]
}

export interface AtlasScene {
  readonly stops: readonly Stop[]
  readonly hubs: readonly Hub[]
}

interface Point {
  readonly x: number
  readonly y: number
}

interface HubDraft {
  readonly x: number
  readonly y: number
  readonly names: Map<string, number>
  readonly routes: HubRoute[]
}

const BEND = 0.18
const HUB_COUNT = 10
const HUB_MIN_ROUTES = 8
const HUB_MIN_SPAN = 40
const TYPE_PREFIX = /^\P{Lu}+/u

function round(value: number): number {
  return Math.round(value * 10) / 10
}

function control(start: Point, end: Point): Point {
  const dx = end.x - start.x
  const dy = end.y - start.y
  const lift = dx >= 0 ? BEND : -BEND
  return {
    x: (start.x + end.x) / 2 + dy * lift,
    y: (start.y + end.y) / 2 - dx * lift,
  }
}

function curve(start: Point, bend: Point, end: Point): string {
  return `M${round(start.x)},${round(start.y)}Q${round(bend.x)},${round(bend.y)} ${round(end.x)},${round(end.y)}`
}

function keyOf(point: Point): string {
  return `${Math.round(point.x)}:${Math.round(point.y)}`
}

export function placeName(name: string): string {
  const trimmed = name.replace(TYPE_PREFIX, "").trim()
  return trimmed === "" ? name : trimmed
}

function collectHubs(routes: readonly Route[]): HubDraft[] {
  const drafts = new Map<string, HubDraft>()
  const touch = (point: Point, name: string, route: HubRoute) => {
    const key = keyOf(point)
    const draft: HubDraft = drafts.get(key) ?? {
      x: point.x,
      y: point.y,
      names: new Map(),
      routes: [],
    }
    draft.names.set(name, (draft.names.get(name) ?? 0) + 1)
    draft.routes.push(route)
    drafts.set(key, draft)
  }
  for (const route of routes) {
    const start = { x: route.x1, y: route.y1 }
    const end = { x: route.x2, y: route.y2 }
    if (keyOf(start) === keyOf(end)) continue
    const bend = control(start, end)
    touch(start, route.from_name, {
      id: route.id,
      path: curve(start, bend, end),
      x: round(end.x),
      y: round(end.y),
    })
    touch(end, route.to_name, {
      id: route.id,
      path: curve(end, bend, start),
      x: round(start.x),
      y: round(start.y),
    })
  }
  return [...drafts.values()]
}

function spanOf(draft: HubDraft): number {
  return Math.max(
    0,
    ...draft.routes.map((route) => Math.hypot(route.x - draft.x, route.y - draft.y)),
  )
}

function commonName(names: ReadonlyMap<string, number>): string {
  let best = ""
  let most = 0
  for (const [name, count] of names) {
    if (count > most) {
      best = name
      most = count
    }
  }
  return placeName(best)
}

function collectStops(routes: readonly Route[], width: number, hubs: ReadonlySet<string>): Stop[] {
  const stops = new Map<string, Stop>()
  for (const route of routes) {
    for (const point of [
      { x: route.x1, y: route.y1 },
      { x: route.x2, y: route.y2 },
    ]) {
      const key = keyOf(point)
      if (hubs.has(key) || stops.has(key)) continue
      stops.set(key, {
        id: key,
        x: round(point.x),
        y: round(point.y),
        sweep: Math.min(1, Math.max(0, point.x / width)),
      })
    }
  }
  return [...stops.values()].sort((a, b) => a.sweep - b.sweep)
}

export function buildScene(routes: readonly Route[], width: number): AtlasScene {
  const hubs = collectHubs(routes)
    .filter((draft) => draft.routes.length >= HUB_MIN_ROUTES && spanOf(draft) >= HUB_MIN_SPAN)
    .sort((a, b) => b.routes.length - a.routes.length)
    .slice(0, HUB_COUNT)
    .sort((a, b) => a.x - b.x)
    .map((draft) => ({
      id: keyOf(draft),
      name: commonName(draft.names),
      x: round(draft.x),
      y: round(draft.y),
      count: draft.routes.length,
      below: draft.routes.reduce((sum, route) => sum + route.y - draft.y, 0) < 0,
      routes: draft.routes,
    }))
  const stops = collectStops(routes, width, new Set(hubs.map((hub) => hub.id)))
  return { stops, hubs }
}
