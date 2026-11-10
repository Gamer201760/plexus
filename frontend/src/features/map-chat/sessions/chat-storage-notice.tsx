import { useTranslation } from "@/shared/i18n"
import { Banner, Button } from "@/shared/ui"

export function ChatStorageNotice({
  issue,
  onRetry,
}: {
  readonly issue: "read" | "write" | null
  readonly onRetry: () => void
}) {
  const { t } = useTranslation()
  if (!issue) return null
  return (
    <Banner
      tone="warning"
      title={t(issue === "read" ? "chat:sessions.readError" : "chat:sessions.writeError")}
      action={
        issue === "write" ? (
          <Button icon="retry" variant="ghost" onClick={onRetry}>
            {t("chat:retry")}
          </Button>
        ) : undefined
      }
    />
  )
}
