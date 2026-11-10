import type { ReactNode } from "react"
import Markdown from "react-markdown"
import rehypeKatex from "rehype-katex"
import remarkGfm from "remark-gfm"
import remarkMath from "remark-math"
import { ScrollArea } from "../../layout/scroll-area/scroll-area"
import { Icon } from "../../primitives/icon/icon"
import styles from "./chat-message.module.css"
import { normalizeMath } from "./normalize-math"

export interface ChatMessageProps {
  readonly speaker: "user" | "assistant"
  readonly text: string
  readonly label: string
  readonly children?: ReactNode
  readonly footer?: ReactNode
}

export function ChatMessage({ speaker, text, label, children, footer }: ChatMessageProps) {
  return (
    <article className={styles.message} data-role={speaker} aria-label={label} lang="ru">
      {children}
      {text ? (
        <div className={styles.prose}>
          {speaker === "user" ? (
            text
          ) : (
            <Markdown
              skipHtml
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[[rehypeKatex, { output: "mathml", trust: false, maxExpand: 1000 }]]}
              components={{
                h1: ({ children: heading }) => <h2>{heading}</h2>,
                h2: ({ children: heading }) => <h2>{heading}</h2>,
                h3: ({ children: heading }) => <h2>{heading}</h2>,
                h4: ({ children: heading }) => <h2>{heading}</h2>,
                h5: ({ children: heading }) => <h2>{heading}</h2>,
                h6: ({ children: heading }) => <h2>{heading}</h2>,
                img: () => null,
                input: ({ checked }) => <Icon name={checked ? "check" : "neutral"} size="sm" />,
                table: ({ children: cells }) => (
                  <ScrollArea orientation="horizontal">
                    <table>{cells}</table>
                  </ScrollArea>
                ),
                a: ({ children: content, href }) => (
                  <a href={href} target="_blank" rel="noreferrer">
                    {content}
                  </a>
                ),
              }}
            >
              {normalizeMath(text)}
            </Markdown>
          )}
        </div>
      ) : null}
      {footer}
    </article>
  )
}
