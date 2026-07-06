# 03 — Frontend Blueprint

Scope: `web/public_prism/src`.

## Routing & Navigation
- **No URL-based routing.** `react-router-dom` is listed as a dependency (v7) but the live navigation system does not use it for page routing — instead `App.tsx` holds a `View` string-union state (`AppInner`, tracked in a local state variable) and `handleNavigate(view)` swaps rendered page components inside an `AnimatePresence` block.
- `ArkadiaNavigation.tsx` renders the persistent sidebar/drawer nav, grouped into **Core / Intelligence / Modules / System**, and is the single global nav surface wrapping every page (including Living Gate) — confirmed via `App.tsx` wrapping `<ArkadiaNavigation>` around the `view === 'gate'` branch.
- Because routing is state-based, there are **no shareable/bookmarkable URLs** for any page (no browser back/forward support, no deep links). This is a structural product limitation, not a bug.

## Pages (`src/pages`)
19+ page components identified, ranging from 34 lines (`IMSArchivePage.tsx`) to 1295 lines (`EncyclopediaGalactica.tsx`). Largest/most complex: `LivingGate.tsx` (1287 lines — onboarding, reset player, IMS booking, calibration tool), `EncyclopediaGalactica.tsx` (1295 lines), `NexusSpiralCodex.tsx` (1105 lines).

## Components (`src/components`)
Nine shared components: `ArkadiaNavigation`, `ArkanaCommune` (chat), `ArkDate`, `MarkdownViewer`, `MoonPhaseRing`, `OracleVoicePlayer`, `ShereSanctuary`, `SonataBar`, `SpiralVault`.

## State Management
- No Redux/Zustand. Global state limited to React Context (`AuthContext.tsx` for Firebase user/profile/personal-codex). All other state is local `useState` + `localStorage` per-page.
- Custom hooks: `useArkadiaAuth`, `useMediaQuery`, `useSpiralQuantumResonance`.

## Styling
- Hybrid: Tailwind CSS (v3.4.4, configured via `tailwind.config.js`) for layout utilities, plus extensive **inline style objects** for dynamic per-page color theming, plus a global `index.css` with custom classes (`.glass-mansion`, `.aurora-bg`) for the "sovereign architecture" aesthetic.
- Animation: `framer-motion` used pervasively for page transitions, drawer physics, pulse effects.

## Forms
- No form library (no react-hook-form observed in this app despite it being a general Replit convention) — forms are native `useState` + `fetch` (e.g. `LoginPage.tsx`, `SettingsPage.tsx`, LivingGate's IMS invitation intake).

## Confirmed Duplication (frontend-only)
- **Encyclopedia Galactica** exists as both a standalone page (`EncyclopediaGalactica.tsx`) and an embedded `EncyclopediaGalacticaMatrix()` component inside `NexusPage.tsx` — different content sets, not the same component reused.
- **IMS Archive** — the standalone `IMSArchivePage.tsx` (34 lines) renders only `IMSArchiveSection()` (Jay/Won/EduLeague, 3 items), while `NexusPage.tsx`'s "ims" tab renders `IMSArchiveSection()` **plus** `EncyclopediaGalacticaMatrix()` (Won/Jessica/Zahrune, 3 more items) — meaning the two entry points to "IMS Archive" show materially different, non-overlapping content. This is the root cause under active repair in this session (see conversation history).
- **Spiral Codex** — split across `NexusSpiralCodex.tsx` (unified feed + Crystal Matrix) and `SpiralCodexFeed.tsx` (simpler scrolling feed) with unconfirmed overlap in purpose.

## Loading / Error / Empty States
Pattern is inconsistent across pages — some use explicit skeleton/spinner states tied to `isLoading`/`isPending` (dashboard pages using React Query), others (older pages like `IMSArchivePage.tsx`) have no loading state because content is static JSX, not fetched.

## Accessibility & Keyboard Shortcuts
- Not systematically audited this session. Known keyboard interaction: LivingGate's calibration mode (Space to mark, ← to step back) — a one-off, not a repo-wide pattern.
