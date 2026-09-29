/**
 * Solariun visual grammar — composition over existing SolSpire data shapes.
 * X02 object · X04 sheet · X05 relationship · X06 activity · X08 weaver visibility
 * No new persistence. No fabricated fields. Unsupported slots stay empty.
 */
import React from 'react';

export type SolariunObject = {
  id: string;
  type: string;
  title: string;
  summary?: string;
  status?: string;
  projectId?: string;
  source?: string;
  updatedAt?: string | number;
};

export type SolariunRelation = {
  type: 'CONNECTED TO' | 'DERIVED FROM' | 'REFERENCES' | 'BELONGS TO' | 'FOLLOW-UP FOR' | 'GENERATED FROM';
  sourceId: string;
  targetId: string;
};

const WEAVER_LIFECYCLE = [
  'PROPOSED',
  'AUTHORIZED',
  'QUEUED',
  'RUNNING',
  'CHECKPOINTED',
  'VERIFYING',
  'READY FOR REVIEW',
  'COMPLETED',
  'ACCEPTED',
] as const;

export function ObjectMetaRow({ object }: { object: SolariunObject }) {
  return (
    <div className="solariun-object-meta-row solariun-type-meta" data-solariun-grammar="object-meta">
      <span>{object.type}</span>
      {object.status ? <span>{object.status}</span> : null}
      {object.source ? <span>{object.source}</span> : null}
      {object.updatedAt != null ? <span>updated {String(object.updatedAt)}</span> : null}
      <span className="solariun-object-id">{object.id}</span>
    </div>
  );
}

export function SolariunObjectCard({
  object,
  accent = '#C9A84C',
  onOpen,
}: {
  object: SolariunObject;
  accent?: string;
  onOpen?: () => void;
}) {
  return (
    <article
      className="solspire-object solariun-object-card"
      data-solariun-grammar="object"
      onClick={onOpen}
      role={onOpen ? 'button' : undefined}
      tabIndex={onOpen ? 0 : undefined}
      onKeyDown={(e) => {
        if (onOpen && (e.key === 'Enter' || e.key === ' ')) onOpen();
      }}
    >
      <div className="solspire-kicker" style={{ color: `${accent}aa` }}>
        {object.type}
      </div>
      <h3 className="solspire-title">{object.title}</h3>
      {object.summary ? <p className="solspire-object-summary">{object.summary}</p> : null}
      <div className="solspire-object-meta">
        <span>{object.status || 'ACTIVE'}</span>
        {object.projectId ? <span>{object.projectId}</span> : null}
      </div>
      <div className="solspire-id">{object.id}</div>
    </article>
  );
}

export function RelationChip({ relation, label }: { relation: SolariunRelation; label?: string }) {
  return (
    <span className="solspire-relation" title={`${relation.type} ${relation.targetId}`}>
      {relation.type}
      {label ? ` · ${label}` : ''}
    </span>
  );
}

export function SolariunObjectView({
  object,
  accent,
  relationships,
  onOpen,
}: {
  object: SolariunObject;
  accent?: string;
  relationships?: SolariunRelation[];
  onOpen?: () => void;
}) {
  return (
    <div className="solariun-object-view" data-solariun-grammar="object-view">
      <SolariunObjectCard object={object} accent={accent} onOpen={onOpen} />
      <ObjectMetaRow object={object} />
      {relationships && relationships.length > 0 ? (
        <div className="solariun-relation-row" data-solariun-grammar="relationships">
          {relationships.map((r, i) => (
            <RelationChip key={`${r.type}-${r.targetId}-${i}`} relation={r} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function SolariunObjectSheet({
  object,
  relationships = [],
  activity = [],
  sourceNote,
  actions,
  onClose,
}: {
  object: SolariunObject;
  relationships?: SolariunRelation[];
  activity?: Array<{ type: string; title: string; context?: string; time?: string; id?: string }>;
  sourceNote?: string;
  actions?: React.ReactNode;
  onClose?: () => void;
}) {
  return (
    <aside
      className="solariun-object-sheet"
      data-solariun-grammar="object-sheet"
      role="complementary"
      aria-label={`${object.type} inspector`}
    >
      <header className="solariun-object-sheet-header">
        <div>
          <div className="solariun-type-meta">{object.type}</div>
          <h2 className="solariun-type-env">{object.title}</h2>
        </div>
        {onClose ? (
          <button type="button" className="solspire-quiet-button" onClick={onClose} aria-label="Close object sheet">
            Close
          </button>
        ) : null}
      </header>
      <section data-sheet-section="overview">
        {object.summary ? (
          <p className="solariun-type-object">{object.summary}</p>
        ) : (
          <p className="solariun-type-meta">No summary provided by substrate.</p>
        )}
        <ObjectMetaRow object={object} />
      </section>
      <section data-sheet-section="relationships">
        <div className="solariun-type-meta">Relationships</div>
        {relationships.length ? (
          <div className="solariun-relation-row">
            {relationships.map((r, i) => (
              <RelationChip key={`${r.type}-${r.targetId}-${i}`} relation={r} />
            ))}
          </div>
        ) : (
          <p className="solariun-type-meta">No supported relationship evidence for this object.</p>
        )}
      </section>
      <section data-sheet-section="activity">
        <div className="solariun-type-meta">Activity</div>
        {activity.length ? (
          <div className="solariun-activity-stream" data-solariun-grammar="activity">
            {activity.map((a, i) => (
              <div key={a.id || `${a.type}-${i}`} className="solspire-activity-item">
                <span className="solspire-activity-dot" />
                <div>
                  <div className="solspire-kicker">{a.type}</div>
                  <div className="solspire-activity-title">{a.title}</div>
                  {a.context ? <div className="solspire-activity-context">{a.context}</div> : null}
                </div>
                <div className="solspire-activity-time">
                  {a.time || ''}
                  {a.id ? <small>{a.id}</small> : null}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="solariun-type-meta">No activity events supplied.</p>
        )}
      </section>
      <section data-sheet-section="source">
        <div className="solariun-type-meta">Source / context</div>
        <p className="solariun-type-object">
          {sourceNote || object.source || 'Source limited to fields returned by existing APIs.'}
        </p>
      </section>
      {actions ? (
        <section data-sheet-section="actions">
          <div className="solariun-type-meta">Actions</div>
          <div className="solariun-object-actions">{actions}</div>
        </section>
      ) : null}
    </aside>
  );
}

export function SolariunActivityStream({
  items,
  emptyLabel = 'No activity recorded.',
}: {
  items: Array<{ type: string; title: string; context?: string; time?: string; id?: string }>;
  emptyLabel?: string;
}) {
  if (!items.length) {
    return <div className="solariun-activity-empty solariun-type-meta">{emptyLabel}</div>;
  }
  return (
    <div className="solariun-activity-stream" data-solariun-grammar="activity-stream" role="list">
      {items.map((a, i) => (
        <div key={a.id || `${a.type}-${i}`} role="listitem" className="solspire-activity-item">
          <span className="solspire-activity-dot" />
          <div>
            <div className="solspire-kicker">{a.type}</div>
            <div className="solspire-activity-title">{a.title}</div>
            {a.context ? <div className="solspire-activity-context">{a.context}</div> : null}
          </div>
          <div className="solspire-activity-time">{a.time || ''}</div>
        </div>
      ))}
    </div>
  );
}

export function WeaverLifecycleLegend({ current }: { current?: string | null }) {
  return (
    <div
      className="solariun-weaver-lifecycle"
      data-solariun-grammar="weaver-lifecycle"
      aria-label="Weaver lifecycle visibility"
    >
      <div className="solariun-type-meta">Governed path (visibility only)</div>
      <ol className="solariun-weaver-steps">
        {WEAVER_LIFECYCLE.map((step) => {
          const active = Boolean(current && current.toUpperCase() === step);
          return (
            <li key={step} data-active={active ? 'true' : 'false'} className={active ? 'is-current' : undefined}>
              {step}
            </li>
          );
        })}
      </ol>
      <p className="solariun-type-meta">
        HUMAN → AUTHORIZATION → WEAVER → VERIFICATION. Display does not authorize execution.
      </p>
    </div>
  );
}

export { WEAVER_LIFECYCLE };
