/** Derive a short session title from the user's first message (matches backend UX). */
export function sessionTitleFromMessage(text: string, maxLen = 20): string {
  const t = text.trim().replace(/\s+/g, ' ')
  if (!t) return 'New chat'
  if (t.length <= maxLen) return t
  return `${t.slice(0, maxLen)}…`
}
