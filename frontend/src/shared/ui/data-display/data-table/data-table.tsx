import { clsx } from "clsx"
import { type ReactNode, useMemo, useState } from "react"
import { Link } from "react-router"
import { ScrollArea } from "../../layout/scroll-area/scroll-area"
import { Icon, type IconName } from "../../primitives/icon/icon"
import styles from "./data-table.module.css"
import {
  nextSort,
  type SortDirection,
  type SortValue,
  sortRows,
  type TableSort,
} from "./table-sort"

export type { SortDirection, SortValue, TableSort } from "./table-sort"

export interface DataTableColumn<Row> {
  readonly key: string
  readonly header: string
  readonly cell: (row: Row) => ReactNode
  readonly numeric?: boolean
  readonly sortable?: boolean
  readonly sortValue?: ((row: Row) => SortValue) | undefined
}

export interface DataTableProps<Row> {
  readonly caption: string
  readonly columns: readonly DataTableColumn<Row>[]
  readonly rows: readonly Row[]
  readonly rowKey: (row: Row) => string
  readonly sort?: TableSort | null | undefined
  readonly defaultSort?: TableSort | null | undefined
  readonly onSortChange?: ((sort: TableSort) => void) | undefined
  readonly onRowClick?: ((row: Row) => void) | undefined
  readonly rowHref?: ((row: Row) => string) | undefined
  readonly selectedKey?: string | null | undefined
  readonly className?: string | undefined
}

const DIRECTION_ICON: Readonly<Record<SortDirection, IconName>> = {
  ascending: "arrow-up",
  descending: "arrow-down",
}

interface HeaderCellProps<Row> {
  readonly column: DataTableColumn<Row>
  readonly direction: SortDirection | null
  readonly onSort: (column: DataTableColumn<Row>) => void
}

function HeaderCell<Row>({ column, direction, onSort }: HeaderCellProps<Row>) {
  const numeric = column.numeric === true && styles.numeric
  if (column.sortable !== true && column.sortValue === undefined)
    return (
      <th scope="col" className={clsx(styles.head, numeric)}>
        {column.header}
      </th>
    )
  return (
    <th
      scope="col"
      aria-sort={direction ?? "none"}
      className={clsx(styles.head, styles.sortable, numeric)}
    >
      <button type="button" className={styles.sort} onClick={() => onSort(column)}>
        <span>{column.header}</span>
        <Icon
          name={direction === null ? "sort" : DIRECTION_ICON[direction]}
          size="sm"
          className={clsx(styles.sortIcon, direction !== null && styles.sortActive)}
        />
      </button>
    </th>
  )
}

interface RowLeadProps {
  readonly href: string | undefined
  readonly clickable: boolean
  readonly children: ReactNode
}

function RowLead({ href, clickable, children }: RowLeadProps) {
  if (href !== undefined) {
    return (
      <Link to={href} viewTransition className={styles.rowButton}>
        {children}
      </Link>
    )
  }
  if (!clickable) return children
  return (
    <button type="button" className={styles.rowButton}>
      {children}
    </button>
  )
}

export function DataTable<Row>({
  caption,
  columns,
  rows,
  rowKey,
  sort,
  defaultSort = null,
  onSortChange,
  onRowClick,
  rowHref,
  selectedKey = null,
  className,
}: DataTableProps<Row>) {
  const [ownSort, setOwnSort] = useState<TableSort | null>(defaultSort)
  const current = sort === undefined ? ownSort : sort
  const sortColumn = columns.find((column) => column.key === current?.key)
  const sorted = useMemo(
    () => (current === null ? rows : sortRows(rows, sortColumn?.sortValue, current.direction)),
    [rows, sortColumn, current],
  )
  const onSort = (column: DataTableColumn<Row>) => {
    const next = nextSort(current, column.key, column.numeric === true)
    setOwnSort(next)
    onSortChange?.(next)
  }
  const clickable = onRowClick !== undefined || rowHref !== undefined

  return (
    <ScrollArea orientation="both" label={caption} className={clsx(styles.frame, className)}>
      <table className={styles.table}>
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <HeaderCell
                key={column.key}
                column={column}
                direction={current?.key === column.key ? current.direction : null}
                onSort={onSort}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => {
            const key = rowKey(row)
            return (
              <tr
                key={key}
                className={clsx(styles.row, clickable && styles.clickable)}
                aria-current={key === selectedKey ? "true" : undefined}
                onClick={onRowClick === undefined ? undefined : () => onRowClick(row)}
              >
                {columns.map((column, index) => (
                  <td
                    key={column.key}
                    className={clsx(styles.cell, column.numeric === true && styles.numeric)}
                  >
                    {index === 0 ? (
                      <RowLead href={rowHref?.(row)} clickable={clickable}>
                        {column.cell(row)}
                      </RowLead>
                    ) : (
                      column.cell(row)
                    )}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </ScrollArea>
  )
}
