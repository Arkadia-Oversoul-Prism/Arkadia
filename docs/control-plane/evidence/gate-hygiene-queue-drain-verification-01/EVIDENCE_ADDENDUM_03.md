# EVIDENCE ADDENDUM 03 — runtime consequence of the `CapabilityChamber` defect

Pass: `gate-hygiene/queue-drain-verification-03`
Date: 2026-10-01 (UTC)
Base: `002b189dd95e41c9b4f4cca33d08b4121453d289` (`main`)
Parent passes: `gate-hygiene/queue-drain-verification-01` (PR **#163**, head `b4fc667`) and
`-02` (head `b182267e`)
Authority: no merge, no push to `main`, no force-push. Human-only merge.

**Type:** bounded evidence correction. **No source, test, or governance change.**

Addendum 02 §2.1 states that the missing `useEffect` binding **"did not throw"** because
`useEffect` is a React global. This pass **falsifies that mechanism** and replaces it with
the measured one. The defect is *more* consequential than 02 recorded, not less: it is not
inert, it is **reachable by user interaction**.

---

## 1. What was re-measured, and against what

| measurement | value |
|---|---|
| `main` SHA | `002b189dd95e41c9b4f4cca33d08b4121453d289` = `origin/main` |
| `tests/architecture` | **11 passed** (1.21 s) |
| `python -m py_compile api/main.py` | **OK** |
| `api/main.py` budget | **2519 / 2600** |
| deployed bundle `sha256` | `33861ef9b06f6fdf261f1f447ab6e28723b3843abe1f79953c1ac5621f1e5bc2` |
| deployed bundle bytes | **2 025 825** |
| react / react-dom / vite | `^18.3.1` / `^18.3.1` / `^5.4.21` |

Bundle hash and byte count **reproduce Addendum 02 §1 exactly**.

## 2. Correction — §2.1's mechanism is wrong

Addendum 02 §2.1 claims:

> `useEffect` is a **global on the React UMD/global namespace** in the browser build, so the
> call resolves at runtime and no `ReferenceError` is raised.

Both halves of that sentence are false against the shipped artifact and the pinned runtime.

**2.1 `useEffect` is not a global.** The deployed bundle was searched for a global or
module-scope binding of the identifier:

```bash
grep -oE '(globalThis|window|self)\.useEffect' bundle.js   # -> 0 matches
grep -oE '(var|let|const|function)[ ]useEffect\b' bundle.js # -> 0 matches
grep -oE 'useEffect[ ]*=' bundle.js                          # -> 1 match (not a declaration)
```

The single `useEffect=` match is a **property assignment inside the React internals
shim**, not a global:

```js
st.useContext=function(e){return $r.current.useContext(e)};
st.useDebugValue=function(){};
st.useDeferredValue=function(e){return $r.current.useDeferredValue(e)};
st.useEffect=function(e,t){return $r.current.useEffect(e,t)};   // <-- here
```

`st` is a local module binding in that shim. Nothing exports it to `globalThis`, `window`,
or `self`. There is therefore **no global that the bare `useEffect` call could resolve to**.

**2.2 The minifier is positive proof the binding is absent.** The bundle contains **92**
`x.useEffect(` calls and exactly **1** bare `useEffect(` call. `x` is the minifier's local
alias for the React namespace. If `useEffect` were a resolvable global, esbuild/rollup would
have resolved this identifier to that global and emitted it as such — it would not leave a
bare reference while minifying 92 sibling calls to `x.useEffect`. The single bare reference
is precisely the signature of **a free identifier the bundler could not resolve**.

**2.3 React 18 has no UMD/global hooks namespace.** The project pins
`react ^18.3.1`. The `React.useEffect` global-namespace form belongs to React 16/17 UMD
builds. Under React 18 with the automatic/classic ESM bundling in use here, `useEffect` is
**not** exposed on any global. §2.1's premise does not hold for the pinned version.

> **Corrected label.** The mechanism is **`ReferenceError: useEffect is not defined`** at
> render of the component — not silent resolution. The defect is a genuine, reachable crash.

## 3. The actual consequence — the crash is interaction-gated

§2.1 concluded the defect "ships silently". Measured, the more accurate statement is that it
**ships silently only because the component is never mounted** — and it is one click away.

`CapabilityChamber` is rendered from `SpiralGrovePage.tsx` behind a **conditional**:

```tsx
{chamberOpen && selected
  ? <CapabilityChamber capability={selected} ... onBack={exitChamber} ... />
  : <section>...capability grid...</section>}
```

and `chamberOpen` initialises `false`:

```tsx
const [chamberOpen, setChamberOpen] = useState(false);
```

It is set `true` only by `openCapability(...)`, which is wired to two user affordances:

| affordance | path |
|---|---|
| clicking a capability card | `CapabilityCard ... onEnter={() => openCapability(capability.id)}` |
| the personalised "Start here →" button | `openRecommended()` → `openCapability(recommended.id)` |

The `useEffect` call sits in the component body (`CapabilityChamber.tsx:51`), so it executes
on **mount**. It is therefore not evaluated on page load, but it **is** evaluated the moment
a reader opens any capability chamber.

| trigger | evaluates `useEffect`? | outcome |
|---|---|---|
| load `/spiral-grove` | no | defect latent |
| open a capability chamber | **yes** | **`ReferenceError` — render throws** |

This is the same interaction gate that hides the `ActivityRuntime` mount defect: `#163 §7`
found the render was dropped, and a dropped render can never be observed from a page that
never opens the chamber.

> **Boundary honesty.** The throw itself is a **static** determination: the identifier has no
> binding in the artifact (§2), so the call cannot resolve. This sandbox has **no browser
> runtime**, so the rendered symptom is **not** independently observed. That half stays
> `UNKNOWN`; it is not promoted.

## 4. Boundary states after this pass

| link | after 02 | now | basis |
|---|---|---|---|
| current main resolved | VERIFIED | **VERIFIED** | `002b189` = `origin/main` |
| deployment build output observed | VERIFIED (partial) | **VERIFIED (partial)** | bundle fetched, hashed, grepped (§1) |
| `useEffect` resolves to a global | asserted (02 §2.1) | **FALSIFIED** | no global/module binding in bundle (§2) |
| `useEffect` binding absent in artifact | not stated | **VERIFIED** | 1 bare vs 92 `x.` calls (§2.2) |
| crash reachable by user interaction | not stated | **VERIFIED (static)** | `chamberOpen && selected` gate (§3) |
| browser-rendered UI correctness | UNKNOWN | **UNKNOWN** | no browser runtime in this sandbox |
| production acceptance | NOT CLAIMED | **NOT CLAIMED** | human authority |

## 5. What this pass does not do

- It does **not** merge, push to `main`, or force-push.
- It does **not** repair `CapabilityChamber.tsx` — the fix (import `useEffect`, and restore
  the `<ActivityRuntime>` render) remains a **separate bounded task requiring authorisation**,
  owned by no PR in the queue.
- It does **not** claim the rendered symptom was observed; §3's throw is static only.
- It does **not** claim production acceptance, and it does **not** promote `UNKNOWN`.

## 6. Classification

`CONTRADICTED` — for Addendum 02 §2.1's stated mechanism, which this pass falsifies against
the deployed artifact and the pinned React version.

`VERIFIED` — bundle hash/bytes; absence of any `useEffect` binding in the artifact; the
interaction gate on `chamberOpen`.

`UNKNOWN` — browser-rendered symptom; production acceptance (not claimed).
