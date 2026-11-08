import clsx from "clsx"
import { type CSSProperties, useLayoutEffect, useMemo, useRef, useState } from "react"
import type { Box } from "./map-motion"
import styles from "./selection-waves.module.css"
import { wavePath } from "./wave-path"

export interface SelectionWavesProps {
  readonly path: string
  readonly unit: number
}

const WAVE_REACH_PX = 28
const WAVE_STEP_PX = 2
const WAVE_MIN_SIZE_PX = 24
const WAVES = [
  { order: 0, line: styles.wave1 },
  { order: 1, line: styles.wave2 },
  { order: 2, line: styles.wave3 },
] as const
const LAST_WAVE = WAVES.length - 1

function waveScale(box: Box, unit: number): CSSProperties {
  const reach = WAVE_REACH_PX * unit * 2
  return {
    "--wave-x": 1 + reach / Math.max(box.width, unit),
    "--wave-y": 1 + reach / Math.max(box.height, unit),
  } as CSSProperties
}

export function SelectionWaves({ path, unit }: SelectionWavesProps) {
  const probe = useRef<SVGPathElement | null>(null)
  const [box, setBox] = useState<Box | null>(null)
  const [settled, setSettled] = useState(false)
  const outline = useMemo(
    () => wavePath(path, WAVE_STEP_PX * unit, WAVE_MIN_SIZE_PX * unit),
    [path, unit],
  )

  useLayoutEffect(() => {
    const node = probe.current
    if (node === null || typeof node.getBBox !== "function") return
    const { x, y, width, height } = node.getBBox()
    setBox({ x, y, width, height })
  }, [])

  if (settled) return null
  return (
    <g className={styles.waves} style={box === null ? undefined : waveScale(box, unit)}>
      {box === null ? <path ref={probe} className={styles.probe} d={outline} /> : null}
      {box === null
        ? null
        : WAVES.map((wave) => (
            <path
              key={wave.order}
              className={clsx(styles.wave, wave.line)}
              style={{ "--i": wave.order } as CSSProperties}
              d={outline}
              onAnimationEnd={wave.order === LAST_WAVE ? () => setSettled(true) : undefined}
            />
          ))}
    </g>
  )
}
