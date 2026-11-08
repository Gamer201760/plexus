import clsx from "clsx"
import { type CSSProperties, useLayoutEffect, useRef, useState } from "react"
import styles from "./iso-text.module.css"

export interface IsoTextProps {
  readonly text: string
  readonly className?: string | undefined
}

interface Ring {
  readonly order: 1 | 2 | 3
  readonly offset: number
}

const FONT_SIZE = 100
const LINE = 1.8
const RINGS: readonly Ring[] = [
  { order: 3, offset: 21 },
  { order: 2, offset: 14 },
  { order: 1, offset: 7 },
]
const PAD = 24
const GLYPH_WIDTH = 0.62
const CAP_HEIGHT = 0.72

function estimate(text: string): string {
  const width = text.length * FONT_SIZE * GLYPH_WIDTH
  return `${-PAD} ${-FONT_SIZE * CAP_HEIGHT - PAD} ${width + PAD * 2} ${FONT_SIZE * CAP_HEIGHT + PAD * 2}`
}

export function IsoText({ text, className }: IsoTextProps) {
  const glyph = useRef<SVGTextElement | null>(null)
  const [viewBox, setViewBox] = useState(() => estimate(text))

  useLayoutEffect(() => {
    const node = glyph.current
    if (node === null || typeof node.getBBox !== "function") return
    const measure = () => {
      const box = node.getBBox()
      if (box.width === 0) return
      setViewBox(`${box.x - PAD} ${box.y - PAD} ${box.width + PAD * 2} ${box.height + PAD * 2}`)
    }
    measure()
    void document.fonts?.ready.then(measure)
  }, [])

  return (
    <svg className={clsx(styles.iso, className)} viewBox={viewBox} aria-hidden="true">
      {RINGS.map((ring) => (
        <g
          key={ring.order}
          className={styles.ring}
          data-ring={ring.order}
          style={{ "--i": ring.order - 1 } as CSSProperties}
        >
          <text
            className={styles.band}
            fontSize={FONT_SIZE}
            strokeWidth={(ring.offset + LINE / 2) * 2}
          >
            {text}
          </text>
          <text
            className={styles.cut}
            fontSize={FONT_SIZE}
            strokeWidth={(ring.offset - LINE / 2) * 2}
          >
            {text}
          </text>
        </g>
      ))}
      <text ref={glyph} className={styles.glyph} fontSize={FONT_SIZE}>
        {text}
      </text>
    </svg>
  )
}
