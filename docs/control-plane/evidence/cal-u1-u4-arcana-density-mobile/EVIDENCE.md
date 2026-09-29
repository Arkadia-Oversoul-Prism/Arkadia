# U1 → U4 — Arcana Conversation Density / Mobile Calibration

**Authorization:** Architect verdict — U1–U4 authorized in parallel  
**Branch:** `cal-u1-u4-arcana-density-mobile`  
**Base:** `main` at `7370bd84f80e40e185d70797cf3dee80973c8b82`

## Scope

### U1 — scoped dense renderer
The existing `MarkdownViewer` remains unchanged globally. Arkana conversation content receives a scoped dense-rendering layer under `.arkana-conversation`, reducing prose font size, line height, heading rhythm, list spacing, code-block padding, and table cell padding.

### U2 — compact context pack
The existing display-only Arcana context pack is retained but compressed into a small metadata grid. It remains explicitly non-injected context and does not become conversation content.

### U3 — compact conversation rhythm / metadata
The existing message canvas receives named layout hooks for header, message, response, metadata, separator, toolbar, and composer surfaces. Vertical waste is reduced without changing thread persistence, message semantics, or actions.

### U4 — mobile visual calibration
A mobile-specific density layer tightens reading width, message spacing, response indentation, typography, toolbar controls, and composer padding. The mobile layout remains the same canonical conversation surface rather than introducing another shell.

## Boundaries preserved

- No change to the global `MarkdownViewer` contract.
- No conversation persistence/API changes.
- No new thread store.
- No change to Oracle voice behavior.
- No fabricated metadata or timestamps.
- Existing canonical Arkana thread remains the source of conversation state.

## Verification status

Repository implementation is complete on the branch. Visual verification should be performed against the deployed preview on desktop and mobile before merge.
