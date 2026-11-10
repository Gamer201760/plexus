import { useState } from "react"
import {
  type ScenarioCatalog,
  type ScenarioLink,
  type ScenarioMode,
  type ScenarioRequest,
  type ScenarioSeason,
  useEvaluateScenario,
} from "@/entities/scenario"

export interface LinkDraft {
  readonly from: string
  readonly to: string
  readonly mode: ScenarioMode
  readonly travel: string
  readonly frequency: string
}

export const LINK_LIMIT = 5
const SCHEDULED: readonly ScenarioMode[] = ["air", "rail"]

export function isScheduled(mode: ScenarioMode): boolean {
  return SCHEDULED.includes(mode)
}

export function parseTravel(value: string): number | null {
  if (!/^\d+([.,]\d+)?$/.test(value.trim())) return null
  const hours = Number(value.trim().replace(",", "."))
  return hours > 0 && hours <= 200 ? hours : null
}

export function validFrequency(draft: LinkDraft): boolean {
  if (!isScheduled(draft.mode) || draft.frequency === "") return true
  if (!/^\d+$/.test(draft.frequency)) return false
  const count = Number(draft.frequency)
  return count >= 1 && count <= 28
}

export function draftLink(draft: LinkDraft): ScenarioLink | null {
  const travel = parseTravel(draft.travel)
  if (travel === null || !validFrequency(draft)) return null
  if (draft.from === "" || draft.to === "" || draft.from === draft.to) return null
  const frequency =
    isScheduled(draft.mode) && draft.frequency !== "" ? Number(draft.frequency) : null
  return {
    from_city: draft.from,
    to_city: draft.to,
    mode: draft.mode,
    travel_h: travel,
    frequency_per_week: frequency,
  }
}

export function useScenarioLab(catalog: ScenarioCatalog) {
  const [season, setSeason] = useState<ScenarioSeason>("road")
  const [links, setLinks] = useState<readonly LinkDraft[]>([])
  const evaluation = useEvaluateScenario()
  const parsed = links.map(draftLink)
  const valid = links.length > 0 && parsed.every((link) => link !== null)
  const request: ScenarioRequest = {
    season,
    model_version: catalog.model_version,
    artifact_version: catalog.artifact_version,
    links: parsed.filter((link): link is ScenarioLink => link !== null),
  }
  const stale =
    evaluation.data !== undefined &&
    JSON.stringify(evaluation.variables) !== JSON.stringify(request)
  return {
    season,
    setSeason,
    links,
    valid,
    stale,
    evaluation,
    request,
    add: (draft: LinkDraft) =>
      setLinks((current) => (current.length < LINK_LIMIT ? [...current, draft] : current)),
    remove: (index: number) =>
      setLinks((current) => current.filter((_, position) => position !== index)),
    calculate: () => {
      if (valid) evaluation.mutate(request)
    },
    reset: () => {
      setLinks([])
      setSeason("road")
      evaluation.reset()
    },
  }
}
