const protectedPart =
  /(```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|`+[^`\n]*`+|\$\$[\s\S]*?(?:\$\$|$)|\$[^$\n]+\$)/g
const formula = /\\[a-zA-Z]+|[a-zA-Z](?:_\{?\w|\^)|^[a-zA-Z]$/u

function normalizePart(text: string): string {
  return text
    .replace(/\\\[([\s\S]*?)\\\]/g, (_, math: string) => `\n\n$$\n${math.trim()}\n$$\n\n`)
    .replace(/\\\(([^\n]*?)\\\)/g, (_, math: string) => `$${math.trim()}$`)
    .replace(/(?<![\w\]$])\(((?:[^()\n]|\([^()\n]*\))+)\)(?!\()/g, (match, math: string) =>
      formula.test(math.trim()) ? `$${math.trim()}$` : match,
    )
}

export function normalizeMath(text: string): string {
  return text
    .split(protectedPart)
    .map((part, index) => (index % 2 ? part : normalizePart(part)))
    .join("")
}
