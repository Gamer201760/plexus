import { useCallback, useEffect, useRef, useState } from "react"

export function useMapHover() {
  const [hoveredId, setHoveredId] = useState<string | null>(null)
  const cardRef = useRef<HTMLDivElement | null>(null)
  const point = useRef({ x: 0, y: 0 })
  const raf = useRef<number | null>(null)
  useEffect(
    () => () => {
      if (raf.current !== null) cancelAnimationFrame(raf.current)
    },
    [],
  )
  const onHover = useCallback((id: string | null, x: number, y: number) => {
    point.current = { x, y }
    setHoveredId(id)
    if (raf.current !== null) cancelAnimationFrame(raf.current)
    raf.current = null
    if (id !== null)
      raf.current = requestAnimationFrame(() => {
        raf.current = null
        if (cardRef.current)
          cardRef.current.style.transform = `translate(${point.current.x}px, ${point.current.y}px)`
      })
  }, [])
  return { hoveredId, cardRef, point, onHover }
}
