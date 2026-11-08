import type { BadgeSpec, ButtonSpec } from "./content.ts"

export interface ReadmeTheme {
  readonly text: string
  readonly muted: string
  readonly label: string
  readonly labelSurface: string
  readonly valueSurface: string
  readonly border: string
  readonly accent: string
  readonly onAccent: string
  readonly warning: string
}

export interface PageInput {
  readonly theme: ReadmeTheme
  readonly fonts: string
  readonly family: string
  readonly wordmark: string
}

const ICONS: Readonly<Record<ButtonSpec["icon"], string>> = {
  terminal: '<polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/>',
  "book-open":
    '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
}

function escapeHtml(text: string): string {
  return text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
}

function shell(input: PageInput, body: string): string {
  const t = input.theme
  return `<!doctype html><html><head><meta charset="utf-8"><style>
${input.fonts}
* { box-sizing: border-box; margin: 0; }
body { font-family: ${input.family}; color: ${t.text}; background: transparent; padding: 8px; }
#asset { display: inline-flex; }
.banner { flex-direction: column; align-items: center; gap: 18px; width: 880px; padding: 28px 0 24px; text-align: center; }
.banner svg { height: 132px; width: auto; overflow: visible; }
.promise { font-size: 28px; font-weight: 650; letter-spacing: -0.02em; line-height: 1.2; max-width: 720px; text-wrap: balance; }
.note { font-size: 16px; color: ${t.muted}; }
.footer svg { height: 44px; width: auto; overflow: visible; }
.button { align-items: center; gap: 10px; height: 44px; padding: 0 20px; border-radius: 6px; font-size: 15px; font-weight: 600; white-space: nowrap; }
.button svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.primary { background: ${t.accent}; color: ${t.onAccent}; }
.secondary { box-shadow: inset 0 0 0 1px ${t.border}; color: ${t.text}; }
.badge { height: 28px; border-radius: 4px; overflow: hidden; border: 1px solid ${t.border}; font-size: 13px; font-weight: 500; white-space: nowrap; font-variant-numeric: tabular-nums; }
.badge span { display: inline-flex; align-items: center; padding: 0 10px; }
.part-label { background: ${t.labelSurface}; color: ${t.label}; }
.part-value { background: ${t.valueSurface}; color: ${t.text}; font-weight: 600; }
.accent { border-color: ${t.accent}; }
.accent .part-value { background: ${t.accent}; color: ${t.onAccent}; }
.warning .part-value { color: ${t.warning}; }
.solo .part-value { font-weight: 500; }
</style></head><body>${body}</body></html>`
}

export function bannerPage(input: PageInput, promise: string, note: string): string {
  return shell(
    input,
    `<div id="asset" class="banner">${input.wordmark}<p class="promise">${escapeHtml(promise)}</p><p class="note">${escapeHtml(note)}</p></div>`,
  )
}

export function footerPage(input: PageInput): string {
  return shell(input, `<div id="asset" class="footer">${input.wordmark}</div>`)
}

export function buttonPage(input: PageInput, button: ButtonSpec): string {
  const kind = button.primary ? "primary" : "secondary"
  const icon = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[button.icon]}</svg>`
  return shell(
    input,
    `<div id="asset" class="button ${kind}">${icon}<span>${escapeHtml(button.label)}</span></div>`,
  )
}

export function badgePage(input: PageInput, badge: BadgeSpec): string {
  const tone = badge.tone ?? "neutral"
  const label =
    badge.label === undefined ? "" : `<span class="part-label">${escapeHtml(badge.label)}</span>`
  const solo = badge.label === undefined ? " solo" : ""
  return shell(
    input,
    `<div id="asset" class="badge ${tone}${solo}">${label}<span class="part-value">${escapeHtml(badge.value)}</span></div>`,
  )
}
