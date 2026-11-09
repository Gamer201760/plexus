import { usePilot } from "@/entities/pilot"
import { useErrorText } from "@/shared/i18n"
import { ErrorState, Skeleton } from "@/shared/ui"
import { PilotExperiment } from "./pilot-experiment"

export interface PilotScenariosProps {
  readonly pilotId: string
}

export function PilotScenarios({ pilotId }: PilotScenariosProps) {
  const query = usePilot(pilotId)
  const errorText = useErrorText()
  if (query.data)
    return (
      <PilotExperiment
        key={query.data.artifact_version}
        pilot={query.data}
        onReload={() => query.refetch().then((result) => !result.isError)}
      />
    )
  if (query.isError)
    return <ErrorState title={errorText(query.error)} onRetry={() => void query.refetch()} />
  return <Skeleton lines={12} />
}
