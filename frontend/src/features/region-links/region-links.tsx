import type { CSSProperties } from "react"
import type { Link, Mode } from "@/entities/link"
import { useTranslation } from "@/shared/i18n"
import { Card, ChipGroup, EmptyState, Skeleton } from "@/shared/ui"
import { TransportIcon } from "@/shared/ui/brand"
import { LinkDetail } from "./link-detail"
import styles from "./region-links.module.css"

const MODES: readonly Mode[] = [
  "bus",
  "air",
  "river",
  "winter_road",
  "ferry",
  "ice_crossing",
  "pontoon_bridge",
]
const SKELETON_ROWS = ["a", "b", "c", "d", "e"]

export interface RegionLinksProps {
  readonly links: readonly Link[] | undefined
  readonly modes: readonly Mode[]
  readonly onModesChange: (modes: Mode[]) => void
  readonly activeId: string | null
  readonly onActive: (id: string | null) => void
}

function LinksSkeleton() {
  return (
    <ul className={styles.list} aria-hidden="true">
      {SKELETON_ROWS.map((key) => (
        <li key={key} className={styles.skeletonRow}>
          <Skeleton lines={2} />
        </li>
      ))}
    </ul>
  )
}

export function RegionLinks({ links, modes, onModesChange, activeId, onActive }: RegionLinksProps) {
  const { t } = useTranslation()
  const all = links ?? []
  const present = MODES.filter((mode) => all.some((l) => l.mode === mode))
  const visible = modes.length === 0 ? all : all.filter((l) => modes.includes(l.mode))
  const active = all.find((l) => l.id === activeId) ?? null
  const body =
    visible.length === 0 ? (
      <EmptyState
        icon="route"
        title={t("region:links.empty")}
        description={t("region:links.emptyText")}
      />
    ) : (
      <ul className={styles.list}>
        {visible.map((link, index) => (
          <li key={link.id} style={{ "--i": Math.min(index, 12) } as CSSProperties}>
            <a
              href={`#link-${link.id}`}
              className={styles.row}
              aria-current={link.id === activeId || undefined}
              onClick={(event) => {
                event.preventDefault()
                onActive(link.id)
              }}
            >
              <TransportIcon mode={link.mode} />
              <span className={styles.route}>
                <span className={styles.ends}>{link.from.name}</span>
                <span className={styles.ends}>{link.to.name}</span>
              </span>
              <span className={styles.season}>
                {link.season ? t(`data:seasonShort.${link.season}`) : t("data:season.unknown")}
              </span>
            </a>
          </li>
        ))}
      </ul>
    )
  return (
    <Card as="section" title={t("region:links.title")} className={styles.card}>
      {present.length > 1 ? (
        <ChipGroup
          label={t("region:links.filterMode")}
          options={present.map((mode) => ({ value: mode, label: t(`data:mode.${mode}`) }))}
          value={modes}
          onChange={onModesChange}
        />
      ) : null}
      {links === undefined ? <LinksSkeleton /> : body}
      <LinkDetail link={active} onClose={() => onActive(null)} />
    </Card>
  )
}
