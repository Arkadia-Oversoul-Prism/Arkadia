import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * presentationMode:
 *  - default: general document/prose reading
 *  - denseConversation: Arkana/Solariun conversation canvas only
 *
 * Dense mode is opt-in and scoped. Global consumers keep default rhythm.
 */
export type MarkdownPresentationMode = 'default' | 'denseConversation';

interface MarkdownViewerProps {
  content: string;
  compact?: boolean;
  presentationMode?: MarkdownPresentationMode;
}

type Scale = {
  base: number;
  line: number;
  h1: number;
  h2: number;
  h3: number;
  h4: number;
  h5: number;
  code: number;
  table: number;
  pMargin: string;
  hMargin: string;
  prePad: string;
  cellPad: string;
  listPad: string;
};

function scaleFor(mode: MarkdownPresentationMode, compact: boolean): Scale {
  if (mode === 'denseConversation') {
    return {
      base: 12,
      line: 1.48,
      h1: compact ? 14.5 : 15.5,
      h2: compact ? 13 : 14,
      h3: compact ? 11.5 : 12,
      h4: compact ? 10.5 : 11,
      h5: 10,
      code: 11,
      table: 11.5,
      pMargin: '0 0 0.42em',
      hMargin: '0.7em 0 0.28em',
      prePad: '10px 12px',
      cellPad: '5px 8px',
      listPad: '0 0 0 1.05em',
    };
  }
  return {
    base: compact ? 12.5 : 13,
    line: compact ? 1.65 : 1.75,
    h1: compact ? 15 : 20,
    h2: compact ? 13 : 16,
    h3: compact ? 11.5 : 13,
    h4: compact ? 10.5 : 12,
    h5: compact ? 10 : 11,
    code: 12,
    table: compact ? 12 : 13,
    pMargin: compact ? '0 0 0.55em' : '0 0 0.75em',
    hMargin: compact ? '0.9em 0 0.4em' : '1.1em 0 0.5em',
    prePad: '16px',
    cellPad: '8px 12px',
    listPad: '0 0 0 1.25em',
  };
}

export default function MarkdownViewer({
  content,
  compact = false,
  presentationMode = 'default',
}: MarkdownViewerProps) {
  const s = scaleFor(presentationMode, compact);
  const dense = presentationMode === 'denseConversation';

  const base: React.CSSProperties = {
    fontFamily: dense
      ? "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif"
      : "'Georgia', 'Times New Roman', serif",
    fontSize: `${s.base}px`,
    lineHeight: s.line,
    color: dense ? 'rgba(233,231,223,0.88)' : 'rgba(212,201,184,0.88)',
    padding: compact || dense ? 0 : '4px 0',
    maxWidth: dense ? '76ch' : undefined,
  };

  return (
    <div
      className={dense ? 'arkadia-md arkadia-md-dense-conversation' : 'arkadia-md'}
      data-md-mode={presentationMode}
      style={base}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1
              style={{
                fontFamily: "'Cinzel', 'Georgia', serif",
                fontSize: `${s.h1}px`,
                fontWeight: 600,
                color: '#e8c96a',
                letterSpacing: '0.06em',
                margin: s.hMargin,
                lineHeight: 1.2,
                borderBottom: dense ? 'none' : '1px solid rgba(201,168,76,0.15)',
                paddingBottom: dense ? 0 : '8px',
              }}
            >
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2
              style={{
                fontFamily: "'Cinzel', 'Georgia', serif",
                fontSize: `${s.h2}px`,
                fontWeight: 600,
                color: '#c9a84c',
                letterSpacing: '0.05em',
                margin: s.hMargin,
                lineHeight: 1.25,
                borderLeft: dense ? 'none' : '2px solid rgba(61,232,208,0.4)',
                paddingLeft: dense ? 0 : '10px',
              }}
            >
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3
              style={{
                fontFamily: "'Cinzel', 'Georgia', serif",
                fontSize: `${s.h3}px`,
                fontWeight: 600,
                color: '#3de8d0',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                margin: s.hMargin,
                lineHeight: 1.25,
              }}
            >
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4
              style={{
                fontFamily: 'sans-serif',
                fontSize: `${s.h4}px`,
                fontWeight: 600,
                color: 'rgba(201,168,76,0.7)',
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
                margin: s.hMargin,
              }}
            >
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5
              style={{
                fontFamily: 'sans-serif',
                fontSize: `${s.h5}px`,
                fontWeight: 600,
                color: 'rgba(232,232,232,0.5)',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                margin: s.hMargin,
              }}
            >
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6
              style={{
                fontFamily: 'sans-serif',
                fontSize: '9.5px',
                fontWeight: 500,
                color: 'rgba(232,232,232,0.4)',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                margin: s.hMargin,
              }}
            >
              {children}
            </h6>
          ),
          p: ({ children }) => (
            <p style={{ margin: s.pMargin, lineHeight: s.line }}>{children}</p>
          ),
          ul: ({ children }) => (
            <ul style={{ margin: s.pMargin, padding: s.listPad }}>{children}</ul>
          ),
          ol: ({ children }) => (
            <ol style={{ margin: s.pMargin, padding: s.listPad }}>{children}</ol>
          ),
          li: ({ children }) => (
            <li style={{ margin: dense ? '0.12em 0' : '0.2em 0', lineHeight: s.line }}>{children}</li>
          ),
          blockquote: ({ children }) => (
            <blockquote
              style={{
                margin: dense ? '0.5em 0' : '0.75em 0',
                padding: dense ? '6px 10px' : '8px 14px',
                borderLeft: '2px solid rgba(0,212,170,0.35)',
                background: 'rgba(0,212,170,0.04)',
                color: 'rgba(233,231,223,0.72)',
                fontSize: dense ? '11.5px' : undefined,
                lineHeight: dense ? 1.44 : undefined,
              }}
            >
              {children}
            </blockquote>
          ),
          code: ({ className, children }) => {
            const isBlock = Boolean(className);
            if (!isBlock) {
              return (
                <code
                  style={{
                    fontFamily: "'Space Mono', ui-monospace, monospace",
                    fontSize: '0.92em',
                    padding: '1px 5px',
                    borderRadius: 4,
                    background: 'rgba(0,212,170,0.08)',
                    color: '#3de8d0',
                  }}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={className} style={{ fontFamily: 'inherit' }}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre
              style={{
                margin: dense ? '0.5em 0' : '12px 0',
                padding: s.prePad,
                background: 'rgba(7,12,24,0.8)',
                border: '1px solid rgba(201,168,76,0.12)',
                borderRadius: 6,
                overflow: 'auto',
                fontFamily: "'Space Mono', monospace",
                fontSize: `${s.code}px`,
                lineHeight: dense ? 1.42 : 1.65,
                color: 'rgba(61,232,208,0.85)',
                WebkitOverflowScrolling: 'touch',
              }}
            >
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: dense ? '0.5em 0' : '16px 0', WebkitOverflowScrolling: 'touch' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: `${s.table}px` }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{ borderBottom: '1px solid rgba(61,232,208,0.25)' }}>{children}</thead>
          ),
          tbody: ({ children }) => <tbody>{children}</tbody>,
          tr: ({ children }) => (
            <tr style={{ borderBottom: '1px solid rgba(201,168,76,0.07)' }}>{children}</tr>
          ),
          th: ({ children }) => (
            <th
              style={{
                padding: s.cellPad,
                textAlign: 'left',
                fontFamily: 'sans-serif',
                fontSize: dense ? '9px' : '10px',
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
                color: 'rgba(61,232,208,0.6)',
                fontWeight: 500,
                background: 'rgba(61,232,208,0.03)',
              }}
            >
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td
              style={{
                padding: s.cellPad,
                color: 'rgba(212,201,184,0.75)',
                verticalAlign: 'top',
                lineHeight: dense ? 1.45 : 1.6,
              }}
            >
              {children}
            </td>
          ),
          hr: () => (
            <div
              style={{
                margin: dense ? '12px 0' : '22px 0',
                height: 1,
                background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.3), transparent)',
              }}
            />
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              style={{
                color: '#3de8d0',
                textDecoration: 'none',
                borderBottom: '1px solid rgba(61,232,208,0.3)',
              }}
            >
              {children}
            </a>
          ),
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              style={{
                maxWidth: '100%',
                borderRadius: 6,
                margin: dense ? '8px 0' : '12px 0',
                border: '1px solid rgba(201,168,76,0.15)',
              }}
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
