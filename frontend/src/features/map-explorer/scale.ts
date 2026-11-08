import type { MapStep } from "@/entities/region"

export interface ScaleBin {
  readonly step: MapStep
  readonly from: number
}

export interface MetricScale {
  readonly hasZero: boolean
  readonly bins: readonly ScaleBin[]
  readonly stepOf: (value: number | null) => MapStep
}

interface Group {
  readonly value: number
  readonly count: number
}

const TOP_STEP = 7

function groupValues(sorted: readonly number[]): Group[] {
  const groups: Group[] = []
  for (const value of sorted) {
    const last = groups.at(-1)
    if (last && last.value === value) groups[groups.length - 1] = { value, count: last.count + 1 }
    else groups.push({ value, count: 1 })
  }
  return groups
}

function prefixSums(groups: readonly Group[]) {
  const count = [0]
  const sum = [0]
  const square = [0]
  groups.forEach((group, index) => {
    count.push((count[index] ?? 0) + group.count)
    sum.push((sum[index] ?? 0) + group.value * group.count)
    square.push((square[index] ?? 0) + group.value * group.value * group.count)
  })
  return (from: number, to: number): number => {
    const n = (count[to + 1] ?? 0) - (count[from] ?? 0)
    const s = (sum[to + 1] ?? 0) - (sum[from] ?? 0)
    return (square[to + 1] ?? 0) - (square[from] ?? 0) - (s * s) / n
  }
}

function bestSplit(
  previous: readonly number[],
  deviation: (from: number, to: number) => number,
  end: number,
  classIndex: number,
) {
  let cost = Number.POSITIVE_INFINITY
  let start = classIndex
  for (let candidate = classIndex; candidate <= end; candidate += 1) {
    const total = (previous[candidate - 1] ?? Number.POSITIVE_INFINITY) + deviation(candidate, end)
    if (total < cost) {
      cost = total
      start = candidate
    }
  }
  return { cost, start }
}

export function naturalStarts(groups: readonly Group[], classes: number): number[] {
  const size = groups.length
  if (size === 0 || classes <= 0) return []
  const deviation = prefixSums(
    groups.map((group) => ({ value: Math.log(group.value), count: group.count })),
  )
  let costs = groups.map((_, end) => deviation(0, end))
  const starts: number[][] = [groups.map(() => 0)]
  for (let classIndex = 1; classIndex < classes; classIndex += 1) {
    const nextCosts = groups.map(() => Number.POSITIVE_INFINITY)
    const nextStarts = groups.map(() => 0)
    for (let end = classIndex; end < size; end += 1) {
      const split = bestSplit(costs, deviation, end, classIndex)
      nextCosts[end] = split.cost
      nextStarts[end] = split.start
    }
    costs = nextCosts
    starts.push(nextStarts)
  }
  const result: number[] = []
  let end = size - 1
  for (let classIndex = classes - 1; classIndex >= 0; classIndex -= 1) {
    const start = starts[classIndex]?.[end] ?? 0
    result.unshift(start)
    end = start - 1
  }
  return result
}

export function roundest(above: number, atMost: number): number {
  const exponent = Math.floor(Math.log10(atMost))
  const units = [1, 0.5, 0.2, 0.1].map((factor) => factor * 10 ** exponent)
  for (const unit of units) {
    const candidate = Math.round(Math.floor(atMost / unit) * unit * 1e6) / 1e6
    if (candidate > above && candidate <= atMost) return candidate
  }
  return atMost
}

function stepFor(index: number, count: number, first: number): MapStep {
  if (count <= 1) return TOP_STEP as MapStep
  return (first + Math.round((index * (TOP_STEP - first)) / (count - 1))) as MapStep
}

export function buildScale(values: readonly (number | null)[]): MetricScale {
  const present = values.filter((value): value is number => value !== null)
  const hasZero = present.some((value) => value <= 0)
  const groups = groupValues(present.filter((value) => value > 0).sort((a, b) => a - b))
  const first = hasZero ? 3 : 2
  const starts = naturalStarts(groups, Math.min(TOP_STEP - first + 1, groups.length))
  const bins = starts.map((start, index) => ({
    from: roundest(groups[start - 1]?.value ?? 0, groups[start]?.value ?? 0),
    step: stepFor(index, starts.length, first),
  }))
  const stepOf = (value: number | null): MapStep => {
    if (value === null) return 0
    if (value <= 0) return 1
    const bin = bins.findLast((candidate) => candidate.from <= value) ?? bins[0]
    return bin?.step ?? 0
  }
  return { hasZero, bins, stepOf }
}
