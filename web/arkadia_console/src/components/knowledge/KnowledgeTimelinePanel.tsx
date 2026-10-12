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
  TIMELINE_WINDOW_LIMIT,
  classifyOlderPage,
  classifyTimelineScope,
  emptyTimelineNotice,
  isTimelineEvents,
  isWindowSaturated,
  mergeOlderEvents,
  olderEventsNotice,
  olderOffset,
  timelineEventSummary,
  timelineWindowNotice,
  type OlderPage,
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
  // registry; the limit and filter are query parameters, not a second endpoint.
  const timelinePath = `${endpoints.knowledgeTimeline}?limit=${TIMELINE_WINDOW_LIMIT}${
    eventType ? `&event_type=${encodeURIComponent(eventType)}` : ""
  }`;

  const timeline = useHydration<TimelineEvent[]>(timelinePath, readTimeline, [isAuthenticated, eventType]);

  // Older pages accumulate *beneath* the newest window. `pageState` is null until
  // the reader has probed for more, so its first render derives "more"/"start"
  // from the window's own saturation rather than asserting history exists.
  const [older, setOlder] = useState<TimelineEvent[]>([]);
  const [pageState, setPageState] = useState<OlderPage | null>(null);
  const [paging, setPaging] = useState<"idle" | "loading" | "error">("idle");

  function resetPaging() {
    setOlder([]);
    setPageState(null);
    setPaging("idle");
  }

  async function loadOlder(shown: number) {
    if (!timeline.data) return;
    const filter = eventType ? `&event_type=${encodeURIComponent(eventType)}` : "";
    const path = `${endpoints.knowledgeTimeline}?limit=${TIMELINE_WINDOW_LIMIT}&offset=${olderOffset(shown)}${filter}`;
    setPaging("loading");
    try {
      const page = await readTimeline(path);
      setOlder((prev) => mergeOlderEvents(prev, page));
      setPageState(classifyOlderPage(page.length, TIMELINE_WINDOW_LIMIT));
      setPaging("idle");
    } catch {
      // A failed older page leaves the rows already shown intact; the reader
      // states the failure instead of silently dropping history.
      setPaging("error");
    }
  }

  return (
    <Panel data-testid="knowledge-timeline-panel">
      <div className="mb-3">
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/40">Timeline</p>
        <p className="mt-1 text-sm text-white/55">
          The latest events from this node's immutable log. This is a bounded recent window; older events require an explicit offset query. Ownership is enforced by the backend.
        </p>
      </div>

      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <label className="sr-only" htmlFor="knowledge-timeline-event-type">Event type</label>
        <select
          id="knowledge-timeline-event-type"
          value={eventType}
          onChange={(event) => {
            setEventType(event.target.value);
            resetPaging();
          }}
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
        <TimelineReading
          newest={timeline.data}
          older={older}
          scope={scope}
          pageState={pageState}
          paging={paging}
          onLoadOlder={loadOlder}
        />
      ) : (
        <ContractState state={timeline.state} error={timeline.error?.message} onRetry={timeline.reload} />
      )}
    </Panel>
  );
}

function TimelineReading({
  newest,
  older,
  scope,
  pageState,
  paging,
  onLoadOlder,
}: {
  newest: TimelineEvent[];
  older: TimelineEvent[];
  scope: ReturnType<typeof classifyTimelineScope>;
  pageState: OlderPage | null;
  paging: "idle" | "loading" | "error";
  onLoadOlder: (shown: number) => void;
}) {
  // The rendered list is the newest window with older pages merged *beneath* it.
  const events = mergeOlderEvents(newest, older);
  if (events.length === 0) {
    return (
      <p data-testid="knowledge-timeline-empty" className="text-sm text-white/50">
        {emptyTimelineNotice(scope)}
      </p>
    );
  }

  const latest = events[events.length - 1];
  const window = { limit: TIMELINE_WINDOW_LIMIT, returned: newest.length };
  // Until a page has been probed, the window's own saturation decides whether
  // more history is offered; afterwards the backend's last response governs.
  const resolvedPage: OlderPage = pageState ?? (isWindowSaturated(window) ? "more" : "start");

  return (
    <div className="flex flex-col gap-4" data-testid="knowledge-timeline-events">
      <Facts
        rows={[
          { label: "events shown", value: String(events.length) },
          { label: "scope", value: scope },
          { label: "window", value: isWindowSaturated(window) ? "newest" : "complete" },
          { label: "oldest shown", value: events[0].created_at },
          { label: "latest", value: latest.created_at },
        ]}
      />
      <p data-testid="knowledge-timeline-window" className="text-xs text-white/45">
        {timelineWindowNotice(window)}
      </p>
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
      <div className="flex flex-col gap-1 border-t border-line pt-3" data-testid="knowledge-timeline-paging">
        <p data-testid="knowledge-timeline-older-notice" className="text-xs text-white/45">
          {olderEventsNotice(resolvedPage)}
        </p>
        {paging === "error" ? (
          <p data-testid="knowledge-timeline-older-error" className="text-xs text-amber-300/80">
            The older page could not be read. The events already shown are unchanged.
          </p>
        ) : null}
        <button
          type="button"
          data-testid="knowledge-timeline-load-older"
          disabled={resolvedPage === "start" || paging === "loading"}
          onClick={() => onLoadOlder(events.length)}
          className="mt-1 self-start rounded-lg border border-line px-3 py-1.5 text-xs text-white/80 disabled:cursor-not-allowed disabled:opacity-40 enabled:hover:border-emerald/50"
        >
          {paging === "loading" ? "Loading older events…" : "Load older events"}
        </button>
      </div>
    </div>
  );
}
