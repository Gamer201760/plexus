import { isChatAnalysis } from "@/shared/api/chat-analysis"
import { isChatChart, isChatTable } from "@/shared/api/chat-artifacts"
import { isChatCalculation } from "@/shared/api/chat-calculation"
import { isChatMapCommand } from "@/shared/api/chat-map"
import type { AnalysisCommentary, ChatEntry, ChatSession } from "./chat-session"

const record = (value: unknown): value is Record<string, unknown> =>
  value !== null && typeof value === "object"
const array = (value: unknown, check: (item: unknown) => boolean) =>
  Array.isArray(value) && value.every(check)
const optionalArray = (value: unknown, check: (item: unknown) => boolean) =>
  value === undefined || array(value, check)
const text = (value: unknown) => typeof value === "string"

export function isAnalysisCommentary(value: unknown): value is AnalysisCommentary {
  return (
    record(value) &&
    text(value.revision) &&
    text(value.text) &&
    typeof value.complete === "boolean" &&
    (value.error === null || text(value.error))
  )
}

function isEntry(value: unknown): value is ChatEntry {
  if (!record(value)) return false
  const metadata =
    array(value.steps, text) &&
    array(value.tables, isChatTable) &&
    array(value.charts, isChatChart) &&
    array(value.mapCommands, isChatMapCommand)
  const calculations =
    optionalArray(value.analyses, isChatAnalysis) &&
    optionalArray(value.calculations, isChatCalculation)
  const commentaries =
    value.commentaries === undefined ||
    (record(value.commentaries) && Object.values(value.commentaries).every(isAnalysisCommentary))
  return (
    text(value.id) &&
    ["user", "assistant"].includes(String(value.role)) &&
    text(value.content) &&
    typeof value.complete === "boolean" &&
    metadata &&
    calculations &&
    commentaries
  )
}

export function isChatSession(value: unknown): value is ChatSession {
  if (!record(value)) return false
  return (
    value.version === 1 &&
    typeof value.id === "string" &&
    value.id.length > 0 &&
    typeof value.createdAt === "number" &&
    Number.isFinite(new Date(value.createdAt).getTime()) &&
    typeof value.updatedAt === "number" &&
    Number.isFinite(new Date(value.updatedAt).getTime()) &&
    text(value.draft) &&
    text(value.status) &&
    (value.error === null || text(value.error)) &&
    array(value.messages, isEntry)
  )
}
