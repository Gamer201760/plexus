import { HOME } from "./map-gesture"
import {
  type Box,
  type DrawPhase,
  type MapView,
  type Size,
  unitsPerPixel,
  viewShift,
  visibleBox,
} from "./map-motion"
import { contains, encloses, expand, intersects, pathBox, union } from "./map-shapes"

export interface PaintRegion {
  readonly id: string
  readonly path: string
  readonly path_low?: string | null
}

export interface MapColors {
  readonly fills: readonly string[]
  readonly water: string
  readonly border: string
  readonly selected: string
  readonly hover: string
  readonly line: number
  readonly selectedLine: number
}

interface Shape {
  readonly region: PaintRegion
  readonly full: Path2D
  readonly box: Box
  readonly element: SVGPathElement
  visible: boolean
  detailed: boolean
}

const SVG = "http://www.w3.org/2000/svg"
const DETAIL_SCALE = 2
const COVER_SHARE = 1
const REBASE_IN = 2.5
const REBASE_OUT = 0.4

function geometry(region: PaintRegion, detailed: boolean): string {
  return detailed ? region.path : (region.path_low ?? region.path)
}

function placement(view: MapView): string {
  return `translate(${view.x}px, ${view.y}px) scale(${view.scale})`
}

export class MapPainter {
  private readonly hit = document.createElement("canvas").getContext("2d")
  private readonly shapes: readonly Shape[]
  private readonly stage: HTMLElement
  private readonly group: SVGGElement
  private readonly overlay: SVGPathElement
  private readonly selectedPath: SVGPathElement
  private readonly frame: Box
  private size: Size = { width: 0, height: 0 }
  private view: MapView = HOME
  private base: MapView = HOME
  private covered: Box | null = null
  private detailed = false
  private selected: string | null = null
  private colors: MapColors | null = null
  private hovered: string | null = null

  constructor(element: HTMLDivElement, frame: Box, regions: readonly PaintRegion[]) {
    this.frame = frame
    const stage = element.querySelector<HTMLElement>("[data-map-stage]")
    const [svg, hover] = element.querySelectorAll("svg")
    if (!stage || !svg || !hover) throw new Error("Map surface is missing")
    this.stage = stage
    this.group = document.createElementNS(SVG, "g")
    svg.replaceChildren(this.group)
    this.shapes = regions.map((region) => {
      const path = document.createElementNS(SVG, "path")
      path.setAttribute("d", geometry(region, false))
      path.dataset.regionId = region.id
      this.group.append(path)
      return {
        region,
        full: new Path2D(region.path),
        box: pathBox(region.path),
        element: path,
        visible: true,
        detailed: false,
      }
    })
    this.selectedPath = document.createElementNS(SVG, "path")
    this.selectedPath.setAttribute("fill", "none")
    this.group.append(this.selectedPath)
    this.overlay = document.createElementNS(SVG, "path")
    hover.replaceChildren(this.overlay)
  }

  configure(colors: MapColors, steps: ReadonlyMap<string, number>, selected: string | null) {
    this.colors = colors
    this.selected = selected
    this.group.setAttribute("stroke", colors.border)
    this.group.setAttribute("stroke-linejoin", "round")
    this.selectedPath.setAttribute("stroke", colors.selected)
    this.overlay.setAttribute("fill", colors.hover)
    for (const shape of this.shapes)
      shape.element.setAttribute(
        "fill",
        colors.fills[steps.get(shape.region.id) ?? 0] ?? colors.water,
      )
    this.outlineSelected()
  }

  draw(view: MapView, size: Size, phase: DrawPhase) {
    if (!this.colors || !size.width || !size.height) return
    this.size = size
    this.view = view
    this.hover(null)
    if (phase === "settled") {
      this.place(view)
      this.setDetail(view.scale > DETAIL_SCALE)
      this.refineViewport(view)
      this.stage.style.transform = ""
      return
    }
    const ratio = view.scale / this.base.scale
    if (phase === "moving" && (ratio > REBASE_IN || ratio < REBASE_OUT)) this.place(view)
    else if (!this.covered || !encloses(this.covered, visibleBox(view, this.frame, size)))
      this.cover([view])
    this.stage.style.transform = viewShift(this.base, view, this.frame, size)
  }

  cover(views: readonly MapView[]) {
    if (!this.size.width || !this.size.height) return
    let box: Box | null = this.covered
    for (const view of views)
      box = union(box, expand(visibleBox(view, this.frame, this.size), COVER_SHARE))
    if (box) this.cull(box)
  }

  pick(x: number, y: number): string | null {
    const worldX = (x - this.view.x) / this.view.scale
    const worldY = (y - this.view.y) / this.view.scale
    for (const shape of this.shapes) {
      if (
        contains(shape.box, worldX, worldY) &&
        this.hit?.isPointInPath(shape.full, worldX, worldY)
      )
        return shape.region.id
    }
    return null
  }

  hover(id: string | null) {
    if (id === this.hovered) return
    this.hovered = id
    const region = this.shapes.find((shape) => shape.region.id === id)?.region
    this.overlay.setAttribute("d", region ? geometry(region, this.detailed) : "")
  }

  private place(view: MapView) {
    this.base = view
    this.group.style.transform = placement(view)
    this.overlay.setAttribute("transform", `translate(${view.x} ${view.y}) scale(${view.scale})`)
    this.cull(expand(visibleBox(view, this.frame, this.size), COVER_SHARE))
    if (this.colors) {
      const unit = unitsPerPixel(this.frame, this.size) / view.scale
      this.group.setAttribute("stroke-width", String(this.colors.line * unit))
      this.selectedPath.setAttribute("stroke-width", String(this.colors.selectedLine * unit))
    }
  }

  private cull(box: Box) {
    this.covered = box
    for (const shape of this.shapes) {
      const shown = intersects(shape.box, box)
      if (shown !== shape.visible) {
        shape.visible = shown
        shape.element.style.display = shown ? "" : "none"
      }
    }
  }

  private setDetail(detailed: boolean) {
    if (detailed === this.detailed) return
    this.detailed = detailed
    this.outlineSelected()
  }

  private refineViewport(view: MapView) {
    const viewport = visibleBox(view, this.frame, this.size)
    for (const shape of this.shapes) {
      if (shape.visible && shape.detailed !== this.detailed && intersects(shape.box, viewport)) {
        shape.detailed = this.detailed
        shape.element.setAttribute("d", geometry(shape.region, this.detailed))
      }
    }
  }

  private outlineSelected() {
    const region = this.shapes.find((shape) => shape.region.id === this.selected)?.region
    this.selectedPath.setAttribute("d", region ? geometry(region, this.detailed) : "")
  }
}
