import { HOME } from "./map-gesture"
import { type Box, type MapView, type Size, unitsPerPixel } from "./map-motion"
import { contains, intersects, pathBox } from "./map-shapes"

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
}

export class MapPainter {
  private readonly hit = document.createElement("canvas").getContext("2d")
  private readonly shapes: readonly Shape[]
  private readonly group: SVGGElement
  private readonly overlay: SVGPathElement
  private readonly selectedPath: SVGPathElement
  private readonly frame: Box
  private view: MapView = HOME
  private detailed = false
  private selected: string | null = null
  private colors: MapColors | null = null
  private hovered: string | null = null

  constructor(element: HTMLDivElement, frame: Box, regions: readonly PaintRegion[]) {
    this.frame = frame
    const svg = element.querySelector("svg")
    const hover = element.querySelectorAll("svg")[1]
    if (!svg || !hover) throw new Error("Map surface is missing")
    this.group = document.createElementNS("http://www.w3.org/2000/svg", "g")
    svg.replaceChildren(this.group)
    this.shapes = regions.map((region) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path")
      path.setAttribute("d", region.path_low ?? region.path)
      path.dataset.regionId = region.id
      this.group.append(path)
      return {
        region,
        full: new Path2D(region.path),
        box: pathBox(region.path),
        element: path,
        visible: true,
      }
    })
    this.selectedPath = document.createElementNS("http://www.w3.org/2000/svg", "path")
    this.selectedPath.setAttribute("fill", "none")
    this.group.append(this.selectedPath)
    this.overlay = document.createElementNS("http://www.w3.org/2000/svg", "path")
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
    const region = this.shapes.find((shape) => shape.region.id === selected)?.region
    this.selectedPath.setAttribute(
      "d",
      region ? (this.detailed ? region.path : (region.path_low ?? region.path)) : "",
    )
  }

  draw(view: MapView, size: Size, settled: boolean) {
    if (!this.colors || !size.width || !size.height) return
    this.view = view
    this.cull(view, size)
    this.setDetail(settled && view.scale > 2)
    this.group.style.willChange = settled ? "" : "transform"
    this.group.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.scale})`
    this.overlay.setAttribute("transform", `translate(${view.x} ${view.y}) scale(${view.scale})`)
    const unit = unitsPerPixel(this.frame, size) / view.scale
    if (settled) {
      this.group.setAttribute("stroke-width", String(this.colors.line * unit))
      this.selectedPath.setAttribute("stroke-width", String(this.colors.selectedLine * unit))
    }
    this.hover(null)
  }

  private cull(view: MapView, size: Size) {
    const k = unitsPerPixel(this.frame, size)
    const visible = {
      x: (this.frame.x - view.x - (size.width * k - this.frame.width) / 2) / view.scale,
      y: (this.frame.y - view.y - (size.height * k - this.frame.height) / 2) / view.scale,
      width: (size.width * k) / view.scale,
      height: (size.height * k) / view.scale,
    }
    for (const shape of this.shapes) {
      const shown = intersects(shape.box, visible)
      if (shown !== shape.visible) {
        shape.visible = shown
        shape.element.style.display = shown ? "" : "none"
      }
    }
  }

  private setDetail(detailed: boolean) {
    if (detailed !== this.detailed) {
      this.detailed = detailed
      for (const { element, region } of this.shapes)
        element.setAttribute("d", detailed ? region.path : (region.path_low ?? region.path))
      const region = this.shapes.find((shape) => shape.region.id === this.selected)?.region
      this.selectedPath.setAttribute(
        "d",
        region ? (detailed ? region.path : (region.path_low ?? region.path)) : "",
      )
    }
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
    this.overlay.setAttribute(
      "d",
      region ? (this.detailed ? region.path : (region.path_low ?? region.path)) : "",
    )
  }
}
