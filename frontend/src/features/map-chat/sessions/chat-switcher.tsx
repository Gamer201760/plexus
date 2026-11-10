import { useId, useRef, useState } from "react"
import { type ChatSession, chatSessionBusy, chatSessionTitle } from "@/entities/chat"
import { useFormatters, useTranslation } from "@/shared/i18n"
import { Button, Dialog, Popover, ScrollArea, TextField, Tooltip } from "@/shared/ui"
import styles from "./chat-switcher.module.css"

interface ChatSwitcherProps {
  readonly sessions: readonly ChatSession[]
  readonly activeId: string
  readonly onSelect: (id: string) => void
  readonly onDelete: (id: string) => void
  readonly onNew: () => void
}

export function ChatSwitcher({ sessions, activeId, onSelect, onNew, onDelete }: ChatSwitcherProps) {
  const { t } = useTranslation()
  const f = useFormatters()
  const [open, setOpen] = useState(false)
  const [deleting, setDeleting] = useState<ChatSession | null>(null)
  const [query, setQuery] = useState("")
  const anchor = useRef<HTMLButtonElement>(null)
  const id = useId()
  const visible = sessions.filter((session) =>
    chatSessionTitle(session)
      .toLocaleLowerCase("ru-RU")
      .includes(query.trim().toLocaleLowerCase("ru-RU")),
  )
  return (
    <div className={styles.actions}>
      <Tooltip content={t("chat:sessions.title")}>
        <Button
          ref={anchor}
          variant="ghost"
          icon="chat"
          aria-label={t("chat:sessions.title")}
          aria-expanded={open}
          aria-controls={open ? id : undefined}
          aria-haspopup="dialog"
          onClick={() => setOpen(!open)}
        >
          {null}
        </Button>
      </Tooltip>
      <Tooltip content={t("chat:new")}>
        <Button
          variant="ghost"
          icon="plus"
          aria-label={t("chat:new")}
          onClick={() => {
            setOpen(false)
            onNew()
          }}
        >
          {null}
        </Button>
      </Tooltip>
      <Popover
        id={id}
        open={open}
        onClose={() => setOpen(false)}
        anchorRef={anchor}
        align="end"
        focusOnOpen
        label={t("chat:sessions.title")}
        className={styles.picker}
      >
        <div className={styles.heading}>
          <strong>{t("chat:sessions.title")}</strong>
          <span>{t("chat:sessions.local")}</span>
        </div>
        <TextField
          type="search"
          icon="search"
          label={t("chat:sessions.search")}
          hideLabel
          placeholder={t("chat:sessions.search")}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <ScrollArea className={styles.list} label={t("chat:sessions.list")}>
          {visible.map((session) => (
            <div className={styles.row} key={session.id}>
              <Button
                variant="ghost"
                icon={session.id === activeId ? "check" : "chat"}
                wrap
                className={styles.item}
                aria-current={session.id === activeId ? "true" : undefined}
                onClick={() => {
                  onSelect(session.id)
                  setOpen(false)
                  setQuery("")
                }}
              >
                <span className={styles.entry}>
                  <span className={styles.name}>{chatSessionTitle(session) || t("chat:new")}</span>
                  <span className={styles.meta}>
                    {chatSessionBusy(session.status)
                      ? t("chat:sessions.responding")
                      : f.dateTime(session.updatedAt)}
                  </span>
                </span>
              </Button>
              <Tooltip content={t("chat:sessions.delete")}>
                <Button
                  variant="ghost"
                  icon="trash"
                  aria-label={t("chat:sessions.deleteNamed", {
                    name: chatSessionTitle(session) || t("chat:new"),
                  })}
                  onClick={() => {
                    setOpen(false)
                    setDeleting(session)
                  }}
                >
                  {null}
                </Button>
              </Tooltip>
            </div>
          ))}
          {!visible.length ? <p className={styles.empty}>{t("chat:sessions.noMatches")}</p> : null}
        </ScrollArea>
      </Popover>
      <Dialog
        open={deleting !== null}
        onClose={() => setDeleting(null)}
        title={t("chat:sessions.deleteTitle")}
        description={t("chat:sessions.deleteDescription")}
        actions={
          <>
            <Button variant="secondary" onClick={() => setDeleting(null)}>
              {t("chat:sessions.keep")}
            </Button>
            <Button
              icon="trash"
              onClick={() => {
                if (deleting) onDelete(deleting.id)
                setDeleting(null)
                setQuery("")
                setOpen(true)
              }}
            >
              {t("chat:sessions.delete")}
            </Button>
          </>
        }
      >
        <p>{deleting ? chatSessionTitle(deleting) || t("chat:new") : ""}</p>
      </Dialog>
    </div>
  )
}
