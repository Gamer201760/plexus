import { useState } from "react"
import { type Pilot, type PilotChange, type PilotRequest, useEvaluatePilot } from "@/entities/pilot"

type Season = PilotRequest["season"]
export interface LinkDraft {
  readonly enabled: boolean
  readonly frequency: string
}

export function useExperiment(pilot: Pilot) {
  const [season, setSeason] = useState<Season>("summer")
  const [drafts, setDrafts] = useState<Record<string, LinkDraft>>({})
  const evaluation = useEvaluatePilot(pilot.id)
  const changes: PilotChange[] = Object.entries(drafts).map(([edge_id, draft]) => ({
    edge_id,
    enabled: draft.enabled,
    ...(draft.frequency === "" ? {} : { frequency_per_week: Number(draft.frequency) }),
  }))
  const valid = Object.values(drafts).every(
    ({ frequency }) =>
      frequency === "" ||
      (/^\d+$/.test(frequency) && Number(frequency) >= 1 && Number(frequency) <= 28),
  )
  const request: PilotRequest = {
    season,
    model_version: pilot.model_version,
    artifact_version: pilot.artifact_version,
    changes,
  }
  const stale =
    evaluation.data !== undefined &&
    JSON.stringify(evaluation.variables) !== JSON.stringify(request)
  return {
    season,
    setSeason,
    drafts,
    valid,
    stale,
    evaluation,
    request,
    update: (id: string, draft: LinkDraft) => setDrafts((current) => ({ ...current, [id]: draft })),
    calculate: () => {
      if (valid) evaluation.mutate(request)
    },
    reset: () => {
      setDrafts({})
      setSeason("summer")
      evaluation.reset()
    },
  }
}
