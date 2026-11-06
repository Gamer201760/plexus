import {
  CircleCheck,
  House,
  Inbox,
  LoaderCircle,
  type LucideProps,
  Moon,
  RefreshCw,
  RotateCcw,
  Sun,
  TriangleAlert,
} from "lucide-react"
import type { ComponentType } from "react"

export const ICONS = {
  alert: TriangleAlert,
  success: CircleCheck,
  empty: Inbox,
  home: House,
  loader: LoaderCircle,
  refresh: RefreshCw,
  retry: RotateCcw,
  "theme-light": Sun,
  "theme-dark": Moon,
} as const satisfies Record<string, ComponentType<LucideProps>>

export type IconName = keyof typeof ICONS
