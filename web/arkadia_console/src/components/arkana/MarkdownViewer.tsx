import { createElement, Fragment, type ReactNode } from "react";

export type MarkdownPresentationMode = "default" | "denseConversation";
interface MarkdownViewerProps {
  content: string;
  compact?: boolean;
  presentationMode?: MarkdownPresentationMode;
}

function inlineContent(source: string, keyPrefix: string): ReactNode[] {
  const tokenPattern = /\x60[^\x60]+\x60|\*\*[^*]+\*\*|__[^_]+__|~~[^~]+~~|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\)/g;
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let index = 0;
  for (const match of source.matchAll(tokenPattern)) {
    const start = match.index ?? 0;
    if (start > cursor) nodes.push(source.slice(cursor, start));
    const token = match[0];
    let node: ReactNode = token;
    if (token.startsWith(String.fromCharCode(96))) {
      node = createElement("code", { key: keyPrefix + index }, token.slice(1, -1));
    } else if (token.startsWith("**") || token.startsWith("__")) {
      node = createElement("strong", { key: keyPrefix + index }, token.slice(2, -2));
    } else if (token.startsWith("~~")) {
      node = createElement("del", { key: keyPrefix + index }, token.slice(2, -2));
    } else if (token.startsWith("*") || token.startsWith("_")) {
      node = createElement("em", { key: keyPrefix + index }, token.slice(1, -1));
    } else {
      const link = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (link) {
        const href = link[2].trim();
        const protocol = href.split(":")[0].toLowerCase();
        const safe = protocol === "http" || protocol === "https" || (href.startsWith("/") && !href.startsWith("//")) || href.startsWith("#");
        node = safe
          ? createElement("a", { key: keyPrefix + index, href, target: "_blank", rel: "noreferrer" }, link[1])
          : link[1];
      }
    }
    nodes.push(createElement(Fragment, { key: keyPrefix + index }, node));
    cursor = start + token.length;
    index += 1;
  }
  if (cursor < source.length) nodes.push(source.slice(cursor));
  return nodes;
}

function isBlockStart(line: string): boolean {
  return /^(#{1,6})\s+/.test(line) ||
    /^\s*([-*+]|[0-9]+\.)\s+/.test(line) ||
    /^\s*\x60\x60\x60/.test(line) ||
    /^\s*>/.test(line) ||
    /^\s*(-{3,}|_{3,}|\*{3,})\s*$/.test(line);
}

function parseBlocks(lines: string[], prefix: string): ReactNode[] {
  const output: ReactNode[] = [];
  let i = 0;
  let key = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }

    const fence = line.match(/^\s*\x60\x60\x60([\w-]*)\s*$/);
    if (fence) {
      const language = fence[1];
      i += 1;
      const code: string[] = [];
      while (i < lines.length && !/^\s*\x60\x60\x60\s*$/.test(lines[i])) {
        code.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      output.push(createElement("pre", { key: prefix + key++ },
        createElement("code", { className: language ? "language-" + language : undefined }, code.join("\n"))
      ));
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      output.push(createElement("h" + level, { key: prefix + key++ }, ...inlineContent(heading[2], prefix + key + "-")));
      i += 1;
      continue;
    }

    if (/^\s*(-{3,}|_{3,}|\*{3,})\s*$/.test(line)) {
      output.push(createElement("hr", { key: prefix + key++ }));
      i += 1;
      continue;
    }

    if (/^\s*>/.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        quote.push(lines[i].replace(/^\s*>\s?/, ""));
        i += 1;
      }
      output.push(createElement("blockquote", { key: prefix + key++ }, ...parseBlocks(quote, prefix + "q" + key)));
      continue;
    }

    const isTable = line.includes("|") && i + 1 < lines.length &&
      /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(lines[i + 1]);
    if (isTable) {
      const cells = (value: string) => value.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
      const header = cells(line);
      i += 2;
      const rows: string[][] = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim()) {
        rows.push(cells(lines[i]));
        i += 1;
      }
      output.push(createElement("div", { key: prefix + key++, className: "arkana-markdown-table-wrap" },
        createElement("table", null,
          createElement("thead", null, createElement("tr", null, ...header.map((cell, n) =>
            createElement("th", { key: n }, ...inlineContent(cell, prefix + "th" + n))
          ))),
          createElement("tbody", null, ...rows.map((row, ri) =>
            createElement("tr", { key: ri }, ...header.map((_, ci) =>
              createElement("td", { key: ci }, ...inlineContent(row[ci] ?? "", prefix + "td" + ri + "-" + ci))
            ))
          ))
        )
      ));
      continue;
    }

    const listMatch = line.match(/^\s*([-*+]|[0-9]+\.)\s+(.+)$/);
    if (listMatch) {
      const ordered = /^[0-9]+\./.test(listMatch[1]);
      const items: ReactNode[] = [];
      while (i < lines.length) {
        const item = lines[i].match(/^\s*([-*+]|[0-9]+\.)\s+(.+)$/);
        if (!item || /^[0-9]+\./.test(item[1]) !== ordered) break;
        let text = item[2];
        const task = text.match(/^\[([ xX])\]\s+(.*)$/);
        const children: ReactNode[] = [];
        if (task) {
          children.push(createElement("input", {
            key: "task", type: "checkbox", checked: task[1].toLowerCase() === "x", disabled: true,
            "aria-label": task[1].toLowerCase() === "x" ? "Completed task" : "Incomplete task",
          }));
          text = task[2];
        }
        children.push(...inlineContent(text, prefix + "li" + i));
        items.push(createElement("li", { key: prefix + "li" + i }, ...children));
        i += 1;
      }
      output.push(createElement(ordered ? "ol" : "ul", { key: prefix + key++ }, ...items));
      continue;
    }

    const paragraph: string[] = [];
    while (i < lines.length && lines[i].trim() && !isBlockStart(lines[i])) {
      paragraph.push(lines[i]);
      i += 1;
    }
    if (!paragraph.length) {
      paragraph.push(lines[i]);
      i += 1;
    }
    output.push(createElement("p", { key: prefix + key++ },
      ...paragraph.flatMap((part, n) => n
        ? [createElement("br", { key: "br" + n }), ...inlineContent(part, prefix + key + "-" + n)]
        : inlineContent(part, prefix + key + "-" + n))
    ));
  }
  return output;
}

/** Lightweight, dependency-free Markdown renderer adapted to Arkana's bounded shell. */
export default function MarkdownViewer({
  content,
  compact = false,
  presentationMode = "default",
}: MarkdownViewerProps) {
  return createElement("div", {
    className: [
      "arkana-markdown",
      presentationMode === "denseConversation" ? "arkana-markdown-dense" : "",
      compact ? "arkana-markdown-compact" : "",
    ].filter(Boolean).join(" "),
    "data-md-mode": presentationMode,
    "data-testid": "arkana-markdown",
  }, ...parseBlocks(content.replace(/\r/g, "").split("\n"), "md-"));
}
