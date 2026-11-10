import type { FormEvent } from "react"
import { Tooltip } from "../../overlays/tooltip/tooltip"
import { Button } from "../../primitives/button/button"
import styles from "./chat-composer.module.css"

export interface ChatComposerProps {
  readonly value: string
  readonly pending: boolean
  readonly label: string
  readonly placeholder: string
  readonly sendLabel: string
  readonly stopLabel: string
  readonly onValue: (value: string) => void
  readonly onSend: () => void
  readonly onStop: () => void
}

export function ChatComposer(props: ChatComposerProps) {
  const action = props.pending ? props.stopLabel : props.sendLabel
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!props.pending && props.value.trim()) props.onSend()
  }
  return (
    <form className={styles.composer} onSubmit={submit}>
      <textarea
        className={styles.input}
        aria-label={props.label}
        placeholder={props.placeholder}
        rows={1}
        maxLength={4000}
        value={props.value}
        onChange={(event) => props.onValue(event.target.value)}
        onKeyDown={(event) => {
          if (
            event.key === "Enter" &&
            !event.shiftKey &&
            !event.nativeEvent.isComposing &&
            event.nativeEvent.keyCode !== 229
          ) {
            event.preventDefault()
            event.currentTarget.form?.requestSubmit()
          }
        }}
      />
      <Tooltip content={action}>
        <Button
          className={styles.send}
          type={props.pending ? "button" : "submit"}
          icon={props.pending ? "stop" : "arrow-up"}
          aria-label={action}
          disabled={!props.pending && !props.value.trim()}
          onClick={props.pending ? props.onStop : undefined}
        >
          {null}
        </Button>
      </Tooltip>
    </form>
  )
}
