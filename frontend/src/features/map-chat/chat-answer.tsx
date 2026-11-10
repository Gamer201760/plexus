import type { AnalysisCommentary } from "@/entities/chat"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Button, ChatMessage, Disclosure } from "@/shared/ui"
import { ChatAnalysisCard } from "./analysis/chat-analysis-card"
import { ChatArtifacts } from "./chat-artifacts"
import { ChatCalculationCard } from "./chat-calculation-card"
import { chatStatusKey } from "./chat-copy"
import { presentMessage } from "./message-presentation"
import type { ChatEntry } from "./use-map-chat"

export function ChatAnswer({
  message,
  autoFocus = false,
  onCommentary,
  onMapCommand,
  onCalculation,
}: {
  readonly autoFocus?: boolean
  readonly onCommentary?:
    | ((messageId: string, analysisId: string, value: AnalysisCommentary) => void)
    | undefined
  readonly onCalculation?: CalculationHandler | undefined
  readonly message: ChatEntry
  readonly onMapCommand: MapCommandHandler
}) {
  const { t } = useTranslation()
  const presentation =
    message.role === "assistant"
      ? presentMessage(message.content)
      : { text: message.content, details: "" }
  return (
    <ChatMessage
      speaker={message.role}
      text={presentation.text}
      label={t(`chat:roles.${message.role}`)}
      footer={
        <>
          {message.mapCommands.map((command) => (
            <Button
              key={JSON.stringify(command)}
              variant="ghost"
              icon="map"
              onClick={() => onMapCommand(command)}
            >
              {t(`chat:mapActions.${command.action}`)}
            </Button>
          ))}
          {message.calculations?.map((calculation) => (
            <ChatCalculationCard
              key={calculation.corridor.id}
              calculation={calculation}
              autoFocus={autoFocus}
              onShow={onCalculation}
            />
          ))}
          {message.analyses?.map((analysis) => (
            <ChatAnalysisCard
              key={analysis.id}
              analysis={analysis}
              commentary={message.commentaries?.[analysis.id]}
              onCommentary={(value) => onCommentary?.(message.id, analysis.id, value)}
            />
          ))}
          <ChatArtifacts tables={message.tables} charts={message.charts} />
          {presentation.details ? (
            <Disclosure title={t("chat:details")}>
              <ChatMessage
                speaker="assistant"
                text={presentation.details}
                label={t("chat:details")}
              />
            </Disclosure>
          ) : null}
        </>
      }
    >
      {message.steps.length ? (
        <Disclosure title={t("chat:steps", { count: message.steps.length })}>
          <ol>
            {message.steps.map((step) => (
              <li key={step}>{t(chatStatusKey(step))}</li>
            ))}
          </ol>
        </Disclosure>
      ) : null}
    </ChatMessage>
  )
}
