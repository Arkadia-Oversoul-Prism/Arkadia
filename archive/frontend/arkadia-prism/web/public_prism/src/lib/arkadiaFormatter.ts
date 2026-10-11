/**
 * Arkadia Universal Text Formatter
 *
 * Every file, paste, or message that enters the Arkadia field is
 * normalised into clean Markdown before it is stored, indexed, or
 * displayed.  The field speaks one language: .md
 *
 * Accepts: raw plaintext, messy copy-paste, partial markdown,
 *          emoji-heavy notes, docx/pdf extracted text, social posts.
 * Returns: coherent, consistently formatted Markdown.
 */

// ─── CONSTANTS ─────────────────────────────────────────────────────────────────

const HEADING_CAPS_RE = /^([A-Z][A-Z\s\-_:]{2,})$/
const LIKELY_LIST_RE  = /^[\-\*\•\–\—]\s+/
const NUMBERED_RE     = /^\d+[\.\)]\s+/

// ─── HELPERS ───────────────────────────────────────────────────────────────────

/** Trim trailing whitespace from every line */
function trimLines(text: string): string {
  return text.split('\n').map(l => l.trimEnd()).join('\n')
}

/** Collapse sequences of 3+ blank lines into exactly 2 (one paragraph break) */
function collapseBlankLines(text: string): string {
  return text.replace(/\n{3,}/g, '\n\n')
}

/** Fix missing space after common punctuation */
function fixSpacing(text: string): string {
  return text
    .replace(/([,;:])([^\s\n\d"'\)\]\}])/g, '$1 $2')   // comma/semi/colon without space
    .replace(/([.!?])([A-Z])/g, '$1 $2')                 // sentence join
    .replace(/[ \t]{2,}/g, ' ')                          // multiple spaces → one
}

/** Remove zero-width characters and other invisible noise */
function stripInvisible(text: string): string {
  // eslint-disable-next-line no-control-regex
  return text.replace(/[\u200B-\u200D\uFEFF\u00AD]/g, '')
}

/** Normalise Windows and old Mac line endings */
function normaliseLineEndings(text: string): string {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

/** Promote ALL-CAPS headings that aren't already markdown headings */
function promoteAllCapsHeadings(text: string): string {
  return text.replace(/^(?!#)(.+)$/gm, (line) => {
    const stripped = line.trim()
    const wordCount = stripped.split(/\s+/).length
    if (HEADING_CAPS_RE.test(stripped) && wordCount <= 7 && wordCount >= 1) {
      // Use h2 for short ALL-CAPS lines that look like section titles
      return `## ${stripped.replace(/:$/, '').trim()}`
    }
    return line
  })
}

/** Normalise loose bullet characters to standard markdown `- ` */
function normaliseBullets(text: string): string {
  return text.replace(/^[\•\–\—]\s+/gm, '- ')
}

/** If a line starts with an emoji and is short, treat it as a h3 sigil header */
function emojiHeadings(text: string): string {
  const EMOJI_RE = /^([\u{1F300}-\u{1FFFF}][\u{1F300}-\u{1FFFF}\s]*)\s+(.{3,60})$/mu
  return text.replace(new RegExp(`^${EMOJI_RE.source}`, 'gmu'), (_m, emoji, rest) => {
    if (rest.trim().split(/\s+/).length <= 8) return `### ${emoji.trim()} ${rest.trim()}`
    return _m
  })
}

/** Wrap unstructured text lines that look like paragraphs */
function ensureParagraphBreaks(text: string): string {
  // Lines that end without punctuation and are immediately followed by
  // another text line (not a heading/list) get a blank line inserted.
  const lines = text.split('\n')
  const out: string[] = []
  for (let i = 0; i < lines.length; i++) {
    out.push(lines[i])
    const cur  = lines[i].trim()
    const next = lines[i + 1]?.trim() ?? ''
    if (
      cur.length > 0 &&
      next.length > 0 &&
      !next.startsWith('#') &&
      !LIKELY_LIST_RE.test(next) &&
      !NUMBERED_RE.test(next) &&
      !cur.startsWith('#') &&
      !cur.startsWith('```') &&
      !next.startsWith('```') &&
      // Only insert when the current line doesn't already end the para
      lines[i + 1] !== ''
    ) {
      // If the current line ends with sentence-ending punctuation, add break
      if (/[.!?:]\s*$/.test(cur)) {
        out.push('')
      }
    }
  }
  return out.join('\n')
}

// ─── MAIN EXPORT ───────────────────────────────────────────────────────────────

/**
 * formatToArkadiaMarkdown
 *
 * Idempotent: running it twice on already-clean markdown returns the same string.
 */
export function formatToArkadiaMarkdown(raw: string): string {
  if (!raw || typeof raw !== 'string') return ''

  let text = raw

  // 1. Invisible/encoding noise
  text = stripInvisible(text)
  text = normaliseLineEndings(text)

  // 2. Whitespace
  text = trimLines(text)
  text = collapseBlankLines(text)

  // 3. Bullets before spacing so we don't corrupt list prefixes
  text = normaliseBullets(text)

  // 4. Promote structural patterns
  text = promoteAllCapsHeadings(text)
  text = emojiHeadings(text)

  // 5. Prose spacing
  text = fixSpacing(text)
  text = ensureParagraphBreaks(text)

  // 6. Final trim
  text = collapseBlankLines(text)
  text = text.trim()

  return text
}

/**
 * previewFromMarkdown
 * Returns a plain-text preview string (first N chars, no markdown syntax).
 */
export function previewFromMarkdown(md: string, maxChars = 180): string {
  const plain = md
    .replace(/^#{1,6}\s+/gm, '')         // headings
    .replace(/\*\*(.+?)\*\*/g, '$1')     // bold
    .replace(/\*(.+?)\*/g, '$1')         // italic
    .replace(/`(.+?)`/g, '$1')           // inline code
    .replace(/\[(.+?)\]\(.+?\)/g, '$1') // links
    .replace(/^[-*>]\s+/gm, '')          // lists / blockquotes
    .replace(/\n+/g, ' ')
    .trim()
  return plain.length > maxChars ? plain.slice(0, maxChars).trimEnd() + '…' : plain
}

/**
 * detectFormat — sniff what kind of raw text we received.
 * Useful for deciding how aggressively to clean it.
 */
export type InputFormat = 'markdown' | 'plaintext' | 'html' | 'unknown'

export function detectFormat(raw: string): InputFormat {
  if (/<[a-z][\s\S]*>/i.test(raw)) return 'html'
  if (/^#{1,6}\s+/m.test(raw) || /\*\*.+\*\*/s.test(raw)) return 'markdown'
  if (/[^\x00-\x7F]/.test(raw) && !/[\u{1F300}-\u{1FFFF}]/mu.test(raw)) return 'plaintext'
  return 'plaintext'
}
