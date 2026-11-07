import {
  CircleCheck,
  House,
  Inbox,
  LoaderCircle,
  type LucideProps,
  RefreshCw,
  RotateCcw,
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
} as const satisfies Record<string, ComponentType<LucideProps>>

export type IconName = keyof typeof ICONS
