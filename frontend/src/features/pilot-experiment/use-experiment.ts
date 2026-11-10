import { useState } from "react"
import {
  type Pilot,
  type PilotAddition,
  type PilotChange,
  type PilotRequest,
  useEvaluatePilot,
} from "@/entities/pilot"

type Season = PilotRequest["season"]
export interface LinkDraft {
  readonly enabled: boolean
  readonly frequency: string
}

export type AdditionMode = "air" | "road" | "river" | "winter_road"

export interface AdditionDraft {
  readonly from: string
  readonly to: string
  readonly mode: AdditionMode
  readonly travel: string
  readonly frequency: string
}

export const ADDITION_LIMIT = 10
const SCHEDULED: readonly AdditionMode[] = ["air", "river"]

export function additionScheduled(mode: AdditionMode): boolean {
  return SCHEDULED.includes(mode)
}

export function parseTravel(value: string): number | null {
  if (!/^\d+([.,]\d+)?$/.test(value.trim())) return null
  const hours = Number(value.trim().replace(",", "."))
  return hours > 0 && hours <= 200 ? hours : null
}

export function additionRequest(draft: AdditionDraft): PilotAddition | null {
  const travel = parseTravel(draft.travel)
  if (travel === null || draft.from === "" || draft.to === "" || draft.from === draft.to)
    return null
  if (additionScheduled(draft.mode)) {
    if (!/^\d+$/.test(draft.frequency)) return null
    const count = Number(draft.frequency)
    if (count < 1 || count > 28) return null
    return {
      from_id: draft.from,
      to_id: draft.to,
      mode: draft.mode,
      travel_h: travel,
      seasons: ["summer", "winter"],
      frequency_per_week: count,
      bidirectional: true,
    }
  }
  return {
    from_id: draft.from,
    to_id: draft.to,
    mode: draft.mode,
    travel_h: travel,
    seasons: ["summer", "winter"],
    bidirectional: true,
  }
}

export function useExperiment(pilot: Pilot) {
  const [season, setSeason] = useState<Season>("summer")
  const [drafts, setDrafts] = useState<Record<string, LinkDraft>>({})
  const [additions, setAdditions] = useState<readonly AdditionDraft[]>([])
  const evaluation = useEvaluatePilot(pilot.id)
  const changes: PilotChange[] = Object.entries(drafts).map(([edge_id, draft]) => ({
    edge_id,
    enabled: draft.enabled,
    ...(draft.frequency === "" ? {} : { frequency_per_week: Number(draft.frequency) }),
  }))
  const parsedAdditions = additions.map(additionRequest)
  const valid =
    Object.values(drafts).every(
      ({ frequency }) =>
        frequency === "" ||
        (/^\d+$/.test(frequency) && Number(frequency) >= 1 && Number(frequency) <= 28),
    ) && parsedAdditions.every((addition) => addition !== null)
  const request: PilotRequest = {
    season,
    model_version: pilot.model_version,
    artifact_version: pilot.artifact_version,
    changes,
    additions: parsedAdditions.filter((addition): addition is PilotAddition => addition !== null),
  }
  const stale =
    evaluation.data !== undefined &&
    JSON.stringify(evaluation.variables) !== JSON.stringify(request)
  return {
    season,
    setSeason,
    drafts,
    additions,
    valid,
    stale,
    evaluation,
    request,
    update: (id: string, draft: LinkDraft) => setDrafts((current) => ({ ...current, [id]: draft })),
    addLink: (draft: AdditionDraft) =>
      setAdditions((current) => (current.length < ADDITION_LIMIT ? [...current, draft] : current)),
    removeLink: (index: number) =>
      setAdditions((current) => current.filter((_, position) => position !== index)),
    calculate: () => {
      if (valid) evaluation.mutate(request)
    },
    reset: () => {
      setDrafts({})
      setAdditions([])
      setSeason("summer")
      evaluation.reset()
    },
  }
}
