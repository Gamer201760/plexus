import type { CSSProperties } from "react"
import { SYMBOL_PATHS } from "../mark-paths"
import styles from "./network-scene.module.css"
import { HUB, ROUTES } from "./routes"
import terrain from "./terrain.json"

export function NetworkScene({ hidden = false }: { readonly hidden?: boolean }) {
  return (
    <div className={styles.scene} data-hidden={hidden} aria-hidden="true">
      <svg className={styles.terrain} viewBox="0 0 1000 620" aria-hidden="true">
        {terrain.map((d) => (
          <path key={d} d={d} />
        ))}
      </svg>
      {ROUTES.map((points, index) => {
        const point = points[index < 3 ? 0 : 3]
        return (
          <svg
            key={index.toString()}
            className={styles.routeLayer}
            viewBox="0 0 1000 620"
            aria-hidden="true"
            style={{ "--i": index % 3 } as CSSProperties}
          >
            <path
              className={styles.route}
              data-active={index === 0 || index === 4}
              d={`M${points[0].join(" ")}C${points
                .slice(1)
                .map((p) => p.join(" "))
                .join(" ")}`}
            />
            <circle className={styles.halo} cx={point[0]} cy={point[1]} r="9" />
            <circle className={styles.node} cx={point[0]} cy={point[1]} r="4" />
          </svg>
        )
      })}
      {[0, 1, 2].map((i) => (
        <div key={i} className={styles.packet} data-signal={i}>
          <span className={styles.dot} />
        </div>
      ))}
      <svg className={styles.hub} viewBox="0 0 1000 620" aria-hidden="true">
        <circle className={styles.halo} cx={HUB[0]} cy={HUB[1]} r="38" />
        <svg
          aria-hidden="true"
          x={HUB[0] - 26}
          y={HUB[1] - 26}
          width="52"
          height="52"
          viewBox={SYMBOL_PATHS.viewBox}
        >
          {SYMBOL_PATHS.rings.map((d) => (
            <path key={d} d={d} className={styles.ring} fillRule="evenodd" />
          ))}
          <path d={SYMBOL_PATHS.word} className={styles.mark} fillRule="evenodd" />
        </svg>
      </svg>
    </div>
  )
}
