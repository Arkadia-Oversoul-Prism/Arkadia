import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownViewerProps {
  content: string;
  compact?: boolean;
}

const base: React.CSSProperties = {
  fontFamily: "'Georgia', 'Times New Roman', serif",
  fontSize: '15px',
  lineHeight: '1.85',
  color: 'rgba(212,201,184,0.9)',
};

export default function MarkdownViewer({ content, compact = false }: MarkdownViewerProps) {
  return (
    <div style={{ ...base, padding: compact ? 0 : '4px 0' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 style={{ fontFamily: "'Cinzel', 'Georgia', serif", fontSize: compact ? '18px' : '22px', fontWeight: 600, color: '#e8c96a', letterSpacing: '0.08em', margin: '0 0 14px', lineHeight: 1.3, borderBottom: '1px solid rgba(201,168,76,0.18)', paddingBottom: '10px' }}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 style={{ fontFamily: "'Cinzel', 'Georgia', serif", fontSize: compact ? '15px' : '17px', fontWeight: 600, color: '#c9a84c', letterSpacing: '0.06em', margin: '22px 0 10px', lineHeight: 1.35, borderLeft: '3px solid rgba(61,232,208,0.5)', paddingLeft: '12px' }}>
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 style={{ fontFamily: "'Cinzel', 'Georgia', serif", fontSize: compact ? '13px' : '14px', fontWeight: 600, color: '#3de8d0', letterSpacing: '0.1em', textTransform: 'uppercase', margin: '18px 0 8px' }}>
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 style={{ fontFamily: 'sans-serif', fontSize: '12px', fontWeight: 600, color: 'rgba(201,168,76,0.7)', letterSpacing: '0.14em', textTransform: 'uppercase', margin: '14px 0 6px' }}>
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 style={{ fontFamily: 'sans-serif', fontSize: '11px', fontWeight: 600, color: 'rgba(232,232,232,0.5)', letterSpacing: '0.12em', textTransform: 'uppercase', margin: '12px 0 5px' }}>
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 style={{ fontFamily: 'sans-serif', fontSize: '10px', fontWeight: 500, color: 'rgba(232,232,232,0.35)', letterSpacing: '0.18em', textTransform: 'uppercase', margin: '10px 0 4px' }}>
              {children}
            </h6>
          ),
          p: ({ children }) => (
            <p style={{ margin: '0 0 12px', color: 'rgba(212,201,184,0.82)', lineHeight: '1.85', fontSize: compact ? '13px' : '15px' }}>
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong style={{ color: 'rgba(232,220,196,0.95)', fontWeight: 600 }}>
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em style={{ color: 'rgba(200,216,232,0.8)', fontStyle: 'italic' }}>
              {children}
            </em>
          ),
          blockquote: ({ children }) => (
            <blockquote style={{ margin: '16px 0', padding: '14px 18px', borderLeft: '3px solid rgba(201,168,76,0.5)', background: 'linear-gradient(90deg, rgba(201,168,76,0.05), transparent)', fontStyle: 'italic', color: 'rgba(200,216,232,0.75)', lineHeight: '1.75', fontSize: compact ? '13px' : '14.5px', borderRadius: '0 6px 6px 0' }}>
              {children}
            </blockquote>
          ),
          ul: ({ children }) => (
            <ul style={{ margin: '0 0 12px', paddingLeft: '20px', listStyle: 'none' }}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol style={{ margin: '0 0 12px', paddingLeft: '20px', listStyle: 'none', counterReset: 'arkadia-ol' }}>
              {children}
            </ol>
          ),
          li: ({ children, ordered }: any) => (
            <li style={{ margin: '4px 0', color: 'rgba(212,201,184,0.78)', fontSize: compact ? '13px' : '14.5px', lineHeight: '1.75', position: 'relative', paddingLeft: '18px' }}>
              <span style={{ position: 'absolute', left: 0, top: '1px', color: 'rgba(61,232,208,0.5)', fontSize: '10px' }}>◆</span>
              {children}
            </li>
          ),
          code: ({ inline, children }: any) => {
            if (inline) {
              return (
                <code style={{ fontFamily: "'Space Mono', 'Courier New', monospace", fontSize: '0.85em', background: 'rgba(61,232,208,0.07)', border: '1px solid rgba(61,232,208,0.15)', borderRadius: '3px', padding: '1px 5px', color: '#3de8d0' }}>
                  {children}
                </code>
              );
            }
            return (
              <pre style={{ margin: '12px 0', padding: '16px', background: 'rgba(7,12,24,0.8)', border: '1px solid rgba(201,168,76,0.12)', borderRadius: '6px', overflow: 'auto', fontFamily: "'Space Mono', monospace", fontSize: '12px', lineHeight: '1.65', color: 'rgba(61,232,208,0.85)' }}>
                <code>{children}</code>
              </pre>
            );
          },
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: '16px 0' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: compact ? '12px' : '13px' }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{ borderBottom: '1px solid rgba(61,232,208,0.25)' }}>
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody>{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr style={{ borderBottom: '1px solid rgba(201,168,76,0.07)' }}>
              {children}
            </tr>
          ),
          th: ({ children }) => (
            <th style={{ padding: '8px 12px', textAlign: 'left', fontFamily: 'sans-serif', fontSize: '10px', letterSpacing: '0.18em', textTransform: 'uppercase', color: 'rgba(61,232,208,0.6)', fontWeight: 500, background: 'rgba(61,232,208,0.03)' }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ padding: '8px 12px', color: 'rgba(212,201,184,0.75)', verticalAlign: 'top', lineHeight: '1.6' }}>
              {children}
            </td>
          ),
          hr: () => (
            <div style={{ margin: '22px 0', height: '1px', background: 'linear-gradient(90deg, transparent, rgba(201,168,76,0.3), transparent)' }} />
          ),
          a: ({ children, href }) => (
            <a href={href} target="_blank" rel="noreferrer" style={{ color: '#3de8d0', textDecoration: 'none', borderBottom: '1px solid rgba(61,232,208,0.3)', transition: 'border-color 0.2s' }}>
              {children}
            </a>
          ),
          img: ({ src, alt }) => (
            <img src={src} alt={alt} style={{ maxWidth: '100%', borderRadius: '6px', margin: '12px 0', border: '1px solid rgba(201,168,76,0.15)' }} />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
