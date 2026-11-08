import { createElement as el } from "react"
export function HansenFormula({ label }: { readonly label: string }) {
  const sub = (a: string, b: string) => el("msub", null, el("mi", null, a), el("mi", null, b))
  return el(
    "math",
    { "aria-label": label, display: "block" },
    sub("A", "i"),
    el("mo", null, "="),
    el("munder", null, el("mo", null, String.fromCodePoint(0x2211)), el("mi", null, "j")),
    sub("M", "j"),
    el(
      "msup",
      null,
      el("mi", null, "e"),
      el(
        "mrow",
        null,
        el("mo", null, String.fromCodePoint(0x2212)),
        el("mi", null, String.fromCodePoint(0x3b2)),
        sub("t", "ij"),
      ),
    ),
  )
}
