import type { LucideProps } from "lucide-react"
import { createElement } from "react"
import glyphs from "./design-glyphs.json"
export type DesignIconName = keyof typeof glyphs
export function designArtwork(name: DesignIconName) {
  return glyphs[name].map((shape, index) =>
    createElement(shape.tag, { ...shape.props, key: index }),
  )
}
export function createDesignIcon(name: DesignIconName, rotation = 0) {
  return function DesignIcon(props: LucideProps) {
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
        {...props}
      >
        <g transform={`rotate(${rotation} 12 12)`}>{designArtwork(name)}</g>
      </svg>
    )
  }
}
