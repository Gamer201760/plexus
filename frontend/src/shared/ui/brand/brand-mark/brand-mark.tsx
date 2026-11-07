import clsx from "clsx"
import type { CSSProperties } from "react"
import { useTranslation } from "@/shared/i18n"
import { type MarkPaths, SYMBOL_FULL_PATHS, SYMBOL_PATHS, WORDMARK_PATHS } from "../mark-paths"
import styles from "./brand-mark.module.css"

export type BrandMarkKind = "wordmark" | "symbol" | "symbol-full"
export type BrandMarkTone = "default" | "inverse"
export type BrandMarkMotion = "none" | "enter" | "pulse"
export type BrandMarkSize = "xs" | "sm" | "md" | "lg" | "xl" | "fill"

const PATHS: Record<BrandMarkKind, MarkPaths> = {
  wordmark: WORDMARK_PATHS,
  symbol: SYMBOL_PATHS,
  "symbol-full": SYMBOL_FULL_PATHS,
}

const TONES: Record<BrandMarkTone, string | undefined> = {
  default: styles.toneDefault,
  inverse: styles.toneInverse,
}

const RING_MOTIONS: Record<BrandMarkMotion, string | undefined> = {
  none: undefined,
  enter: styles.ringEnter,
  pulse: styles.ringPulse,
}

const SIZES: Record<BrandMarkSize, string | undefined> = {
  xs: styles.xs,
  sm: styles.sm,
  md: styles.md,
  lg: styles.lg,
  xl: styles.xl,
  fill: styles.fill,
}

export interface BrandMarkProps {
  readonly kind?: BrandMarkKind
  readonly tone?: BrandMarkTone
  readonly motion?: BrandMarkMotion
  readonly size?: BrandMarkSize
  readonly decorative?: boolean
  readonly broken?: boolean
  readonly className?: string | undefined
}

export function BrandMark({
  kind = "wordmark",
  tone = "default",
  motion = "none",
  size = "md",
  decorative = false,
  broken = false,
  className,
}: BrandMarkProps) {
  const { t } = useTranslation()
  const paths = PATHS[kind]
  return (
    <svg
      className={clsx(styles.mark, TONES[tone], SIZES[size], broken && styles.broken, className)}
      viewBox={paths.viewBox}
      role={decorative ? undefined : "img"}
      aria-hidden={decorative ? true : undefined}
      aria-label={decorative ? undefined : t("common:app.name")}
    >
      {paths.rings.map((d, index) => (
        <path
          key={d.slice(0, 32)}
          className={clsx(styles.ring, RING_MOTIONS[motion])}
          data-ring={index + 1}
          style={{ "--i": index } as CSSProperties}
          d={d}
          fillRule="evenodd"
        />
      ))}
      <path
        className={clsx(styles.word, motion === "enter" && styles.wordEnter)}
        d={paths.word}
        fillRule="evenodd"
      />
    </svg>
  )
}
