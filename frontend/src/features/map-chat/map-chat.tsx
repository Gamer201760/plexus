import { type ReactNode, useEffect, useId, useRef, useState } from "react"
import { useSearchParams } from "react-router"
import type { ChatContext } from "@/entities/chat"
import { useRegion } from "@/entities/region"
import type { CalculationHandler } from "@/shared/api/chat-calculation"
import type { MapCommandHandler } from "@/shared/api/chat-map"
import { useTranslation } from "@/shared/i18n"
import { Banner, Button, ChatComposer, Icon, ScrollArea, Segmented, Tooltip } from "@/shared/ui"
import { BrandMark } from "@/shared/ui/brand"
import { ChatAnswer } from "./chat-answer"
import { chatErrorKey, chatStatusKey } from "./chat-copy"
import styles from "./map-chat.module.css"
import { useMapChat } from "./use-map-chat"

export interface MapChatProps {
  readonly onCalculation?: CalculationHandler | undefined
  readonly context: ChatContext
  readonly summary: ReactNode
  readonly scenario?: ReactNode
  readonly onMapCommand: MapCommandHandler
}

export function MapChat({ context, summary, scenario, onMapCommand, onCalculation }: MapChatProps) {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState<"chat" | "summary" | "scenario">(initialTab(searchParams))
  const chat = useMapChat(context, onMapCommand)
  const region = useRegion(context.region_id ?? "", context.season ?? "summer")
  const regionName = context.region_id
    ? region.data?.id === context.region_id
      ? region.data.name
      : t("common:state.loading")
    : t("chat:allRegions")
  const titleId = useId()
  const scroll = useRef<HTMLDivElement>(null)
  const follow = useRef(true)
  const tail = chat.messages.at(-1)
  useEffect(() => {
    if (tail !== undefined && follow.current && scroll.current) {
      scroll.current.scrollTop = scroll.current.scrollHeight
    }
  }, [tail])
  const send = (prompt?: string) => {
    follow.current = true
    chat.send(prompt)
  }

  return (
    <aside className={styles.panel} aria-labelledby={titleId}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <BrandMark kind="symbol" size="sm" decorative />
          <p id={titleId} className={styles.title}>
            {t("chat:title")}
          </p>
        </div>
        <Tooltip content={t("chat:new")}>
          <Button
            variant="ghost"
            icon="plus"
            aria-label={t("chat:new")}
            disabled={chat.busy || !chat.messages.length}
            onClick={chat.clear}
          >
            {null}
          </Button>
        </Tooltip>
      </header>
      <div className={styles.tabs}>
        <Segmented
          label={t("chat:panelLabel")}
          value={tab}
          onChange={setTab}
          options={[
            { value: "chat", label: t("chat:tab"), icon: "chat" },
            { value: "summary", label: t("chat:summary"), icon: "list" },
            { value: "scenario", label: t("graph:tab") },
          ]}
        />
      </div>
      <div className={styles.summary} hidden={tab !== "scenario"}>
        {scenario}
      </div>
      <div className={styles.summary} hidden={tab !== "summary"}>
        {summary}
      </div>
      <div className={styles.chat} hidden={tab !== "chat"}>
        <ScrollArea
          ref={scroll}
          className={styles.messages}
          label={t("chat:history")}
          onScroll={() => {
            const node = scroll.current
            if (node) follow.current = node.scrollHeight - node.scrollTop - node.clientHeight < 80
          }}
        >
          {chat.messages.length === 0 ? (
            <div className={styles.empty}>
              <p className={styles.intro}>
                {t("chat:intro")} <em>{t("chat:introAccent")}</em>?
              </p>
              <p className={styles.description}>{t("chat:description")}</p>
              <div className={styles.suggestions}>
                {(["example", "exampleLinks", "exampleMethod"] as const).map((key) => (
                  <Button
                    key={key}
                    variant="ghost"
                    icon="arrow-right"
                    className={styles.suggestion}
                    onClick={() => send(t(`chat:${key}`))}
                  >
                    {t(`chat:${key}`)}
                  </Button>
                ))}
              </div>
            </div>
          ) : null}
          {chat.messages.map((message) => (
            <ChatAnswer
              key={message.id}
              message={message}
              onCalculation={onCalculation}
              onMapCommand={onMapCommand}
            />
          ))}
          {chat.messages.length ? (
            <p role="status" className={styles.status}>
              <Icon name={chat.busy ? "neutral" : chat.error ? "error" : "check"} size="sm" />
              {t(chatStatusKey(chat.status))}
            </p>
          ) : null}
        </ScrollArea>
        <div className={styles.footer}>
          {chat.error ? (
            <Banner
              tone="danger"
              announce
              title={t(chatErrorKey(chat.error))}
              action={
                <Button icon="retry" variant="ghost" onClick={chat.retry}>
                  {t("chat:retry")}
                </Button>
              }
            />
          ) : null}
          <div className={styles.context}>
            <Icon name="map" size="sm" />
            <span>{regionName}</span>
            <span className={styles.contextSeason}>
              {t(`data:season.${context.season ?? "summer"}`)}
            </span>
          </div>
          <ChatComposer
            value={chat.draft}
            onValue={chat.setDraft}
            pending={chat.busy}
            onSend={() => send()}
            onStop={chat.stop}
            label={t("chat:prompt")}
            placeholder={t("chat:placeholder")}
            sendLabel={t("chat:send")}
            stopLabel={t("chat:stop")}
          />
        </div>
      </div>
    </aside>
  )
}

function initialTab(params: URLSearchParams): "chat" | "scenario" {
  return params.has("analysis") || params.get("panel") === "scenario" ? "scenario" : "chat"
}
