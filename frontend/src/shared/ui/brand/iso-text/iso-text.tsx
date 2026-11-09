import clsx from "clsx"
import type { CSSProperties } from "react"
import glyphs from "./iso-glyphs.json"
import styles from "./iso-text.module.css"

export type IsoGlyph = keyof typeof glyphs

export interface IsoTextProps {
  readonly glyph: IsoGlyph
  readonly className?: string | undefined
}

export function IsoText({ glyph, className }: IsoTextProps) {
  const paths = glyphs[glyph]
  return (
    <svg className={clsx(styles.iso, className)} viewBox={paths.viewBox} aria-hidden="true">
      {paths.rings.map((d, index) => (
        <path
          key={d.slice(0, 32)}
          className={styles.ring}
          data-ring={index + 1}
          style={{ "--i": index } as CSSProperties}
          d={d}
          fillRule="evenodd"
        />
      ))}
      <path className={styles.word} d={paths.word} fillRule="evenodd" />
    </svg>
  )
}
