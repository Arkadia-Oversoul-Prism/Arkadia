# Arkana Interface Specification 01

**Status:** Proposed design specification. The existing Arkana UI is a basic console page, not this design. No interface implementation is included.

## 1. Experience goal

A refined, calm, conversation-first intelligence environment. The interface should feel premium and distinct within Arkadia without exposing infrastructure complexity by default. Use the existing console's dark visual foundation, emerald/teal interaction color, shared focus treatment and reduced-motion behavior as starting constraints—not as a finished Arkana visual system.

## 2. Design principles

- Quiet hierarchy, generous readable measure and precise typography.
- Conversation is the primary surface; history and workspace are secondary and revealable.
- Show capability controls progressively; do not present unsupported features as active.
- Motion communicates state and remains subtle; honor reduced-motion preferences.
- Desktop may expose a collapsible context/workspace panel. Mobile remains a single-column conversation with a drawer or full-screen artifact view.
- Keyboard navigation, visible focus, semantic labels, contrast and touch-target sizing are required design properties.

## 3. Information architecture

### Default empty state

- Compact Arkana identity and concise welcome.
- One central composer with send affordance and keyboard hint.
- A small set of clearly labeled task starters only when they invoke supported workflows.
- Recent conversations/history available without dominating the canvas.
- A discreet mode/provider indicator that reports the real selected capability; do not label a mode as operational when it has no distinct backend behavior.

### Active conversation

- Header: thread title, status and optional model/provider disclosure.
- Main column: ordered messages with structured Markdown, code blocks and clear user/assistant distinction.
- Assistant response actions: copy and retry/regenerate only when supported; stop while generation is active.
- Provenance: compact source summary with expandable details, distinguishing corpus references from Knowledge OS sources and indicating retrieval status.
- Composer remains anchored near the conversation end, preserving draft and focus appropriately.

### Optional workspace/activity

- Workspace opens for a real document, code, data or research artifact; otherwise remain closed.
- Activity shows real request lifecycle events, provider/capability, sources and approvals. It must not imply tool use that did not occur.
- No speculative dashboard widgets or decorative fake telemetry.

### History

- Searchable, owner-scoped threads with semantic titles and recency.
- Selecting a thread must load its canonical transcript and make it the active conversation; current history viewer is read-only and does not yet meet this behavior.
- New conversation and rename controls must call authorized backend contracts and retain clear loading/error states.

## 4. Composer contract

V1 presents text entry, submit, pending state and stop/cancel if supported by backend. Enter submits; Shift+Enter inserts a newline. Preserve an unsent draft on recoverable failures. Attach, voice, model selection, deep reasoning and agent controls remain hidden or clearly marked unavailable until end-to-end capability exists. File controls must disclose file type/size and privacy behavior when implemented.

## 5. Message rendering

- Render Markdown with safe link behavior; syntax highlighting and copy controls for code.
- Keep long-form responses readable and avoid forcing every answer into a branded template.
- Show provider identity only when the backend reports it.
- Show sources only when actually retrieved/injected. Empty, unavailable and failed retrieval are distinct.
- Display timestamp/turn status where useful; avoid repeating decorative metadata on every message.
- Assistant read-aloud is an existing capability and may be retained if its behavior and state remain clear.

## 6. Required interaction states

| State | UI behavior |
|---|---|
| Identity loading | Avoid issuing owner-scoped reads until authenticated identity is ready. |
| Empty | Welcome and usable composer; no fabricated suggestions. |
| Draft | Keyboard-accessible editable input; submit enabled only for valid non-empty input. |
| Submitting | Optimistic user turn is clearly pending; prevent duplicate submission. |
| Streaming | Append ordered deltas; expose stop and retain the partial response state. |
| Tool/activity | Show only real events and permissions/approval status. |
| Completed | Distinguish generated from durably persisted if those are separate events. |
| Cancelled | Preserve partial text and state whether persistence succeeded. |
| Failed | Explain recoverable cause, preserve draft, offer retry without duplicate turn. |
| Offline/interrupted | Keep local draft; reconnect/recovery must not silently duplicate requests. |
| No context | Say no relevant context was retrieved, only when that is what the backend reports. |
| Context unavailable | State retrieval failure separately from zero relevant results. |
| History empty/unavailable | Distinguish empty, unauthenticated, loading, unavailable and request failure. |

## 7. Responsive behavior

- Wide desktop: centered conversation column; optional history rail and workspace panel, both collapsible.
- Narrow desktop/tablet: conversation first; navigation/workspace become drawers.
- Mobile: full-width messages and composer, safe-area aware, minimum touch targets, full-screen artifacts, no shrunken three-column layout.
- Preserve message order, draft, scroll position and focus across panel toggles and route changes.

## 8. Visual tokens (proposed)

Use semantic tokens for background, raised surface, border, primary text, secondary text, accent, warning and error. The initial concept uses near-black/obsidian with restrained teal and optional muted gold. Exact values, font licensing/loading, contrast ratios and component tokens should be validated during design implementation. Avoid relying on color alone for state.

## 9. Accessibility and motion

Use semantic landmarks, accessible names, live-region announcements for stream completion/errors (without announcing every token), focus management on conversation changes, keyboard-operable controls, reduced-motion support and sufficient contrast. Do not steal focus on each streamed update.

## 10. V1 boundary

Design the surface for text conversation, owner-scoped history, streaming lifecycle, retry/stop where supported, Markdown/code rendering and provenance. Do not present voice conversation, image generation, web search, file analysis, branching, multi-provider routing or agent execution as available merely because the visual system can eventually host them.