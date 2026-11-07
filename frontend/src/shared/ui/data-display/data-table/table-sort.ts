import { INTL_LOCALE } from "../../../i18n"

export type SortDirection = "ascending" | "descending"

export interface TableSort {
  readonly key: string
  readonly direction: SortDirection
}

export type SortValue = string | number | null

const collator = new Intl.Collator(INTL_LOCALE, { numeric: true, sensitivity: "base" })

function compareValues(first: SortValue, second: SortValue): number {
  if (first === second) return 0
  if (first === null) return 1
  if (second === null) return -1
  if (typeof first === "number" && typeof second === "number") return first - second
  return collator.compare(String(first), String(second))
}

export function sortRows<Row>(
  rows: readonly Row[],
  sortValue: ((row: Row) => SortValue) | undefined,
  direction: SortDirection,
): readonly Row[] {
  if (sortValue === undefined) return rows
  const factor = direction === "ascending" ? 1 : -1
  return [...rows].sort((first, second) => {
    const left = sortValue(first)
    const right = sortValue(second)
    if (left === null || right === null) return compareValues(left, right)
    return compareValues(left, right) * factor
  })
}

export function nextSort(current: TableSort | null, key: string, numeric: boolean): TableSort {
  if (current?.key === key)
    return { key, direction: current.direction === "ascending" ? "descending" : "ascending" }
  return { key, direction: numeric ? "descending" : "ascending" }
}
