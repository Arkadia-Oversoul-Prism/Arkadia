/**
 * Knowledge OS — owner-scoped timeline reader.
 *
 * Backed by the *verified* handler contract `GET /api/knowledge/timeline`
 * (`api/knowledge_routes.py::get_timeline` -> `knowledge.timeline.query`); see
 * the capability matrix in this slice's evidence.
 *
 * The ownership predicate on this reader is stricter than the graph/search
 * readers': authenticated `user_id = ?`, anonymous `1 = 0`. There is no public
 * corpus, so a `200 []` means *either* "this owner's log is empty" *or* "this
 * caller owns nothing readable" — the transport cannot tell them apart. The
 * panel therefore derives that distinction from the viewer's identity (a fact
 * the client already holds) and never reports a filtered answer as an empty
 * log. It applies no ownership filter of its own: a client-side filter cannot
 * prove a server-side boundary.
 */
import { useState } from "react";
import { Panel, Facts, ContractState } from "../../components/ui";
import { useAuth } from "../../contexts/AuthContext";
import { useHydration } from "../../lib/useHydration";
import { apiRequest, ApiError } from "../../lib/apiClient";
import { endpoints } from "../../lib/endpoints";
import {
  TIMELINE_EVENT_TYPES,
  classifyTimelineScope,
  emptyTimelineNotice,
  isTimelineEvents,
  timelineEventSummary,
  type TimelineEvent,
  type ViewerKind,
} from "../../pages/knowledge/knowledgeContracts";

async function readTimeline(path: string): Promise<TimelineEvent[]> {
  const payload = await apiRequest<unknown>(path);
  if (!isTimelineEvents(payload)) {
    throw new ApiError("The knowledge timeline contract returned an unrecognised shape.", {
      kind: "UNKNOWN",
      path,
    });
  }
  return payload;
}

export function KnowledgeTimelinePanel() {
  const { isAuthenticated } = useAuth();
  const viewer: ViewerKind = isAuthenticated ? "authenticated" : "anonymous";
  const scope = classifyTimelineScope(viewer);

  const [eventType, setEventType] = useState("");

  // Derived from the declared collection so the base path cannot drift from the
  // registry; the filter is a query parameter, not a second endpoint.
  const timelinePath = eventType
    ? `${endpoints.knowledgeTimeline}?event_type=${encodeURIComponent(eventType)}`
    : endpoints.knowledgeTimeline;

  const timeline = useHydration<TimelineEvent[]>(timelinePath, readTimeline, [isAuthenticated, eventType]);

  return (
    <Panel data-testid="knowledge-timeline-panel">
      <div className="mb-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Timeline</p>
        <p className="mt-1 text-sm text-white/55">
          The immutable event log for this node. Ownership is enforced by the backend.
        </p>
      </div>

      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <label className="sr-only" htmlFor="knowledge-timeline-event-type">Event type</label>
        <select
          id="knowledge-timeline-event-type"
          value={eventType}
          onChange={(event) => setEventType(event.target.value)}
          className="rounded-lg border border-line bg-ink/50 px-3 py-2 text-sm text-white outline-none focus:border-emerald/50"
        >
          <option value="">All event types</option>
          {TIMELINE_EVENT_TYPES.map((type) => (
            <option key={type} value={type}>{type}</option>
          ))}
        </select>
        <p data-testid="knowledge-timeline-scope" className="font-mono text-[10px] uppercase tracking-widest text-white/35">
          scope · {scope}
        </p>
      </div>

      {timeline.state === "ready" && timeline.data ? (
        <TimelineReading events={timeline.data} scope={scope} />
      ) : (
        <ContractState state={timeline.state} error={timeline.error?.message} onRetry={timeline.reload} />
      )}
    </Panel>
  );
}

function TimelineReading({ events, scope }: { events: TimelineEvent[]; scope: ReturnType<typeof classifyTimelineScope> }) {
  if (events.length === 0) {
    return (
      <p data-testid="knowledge-timeline-empty" className="text-sm text-white/50">
        {emptyTimelineNotice(scope)}
      </p>
    );
  }

  const latest = events[events.length - 1];

  return (
    <div className="flex flex-col gap-4" data-testid="knowledge-timeline-events">
      <Facts
        rows={[
          { label: "events", value: String(events.length) },
          { label: "scope", value: scope },
          { label: "first", value: events[0].created_at },
          { label: "latest", value: latest.created_at },
        ]}
      />
      <ol className="flex flex-col gap-2">
        {events.map((event) => (
          <li key={event.id} className="border-l border-line pl-3" data-testid={`knowledge-timeline-event-${event.id}`}>
            <p className="font-mono text-[10px] uppercase tracking-widest text-white/40">
              #{event.id} · {event.event_type}
            </p>
            <p className="mt-1 text-xs text-white/60">{event.created_at}</p>
            <p className="mt-1 text-sm text-white/80">{timelineEventSummary(event)}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
