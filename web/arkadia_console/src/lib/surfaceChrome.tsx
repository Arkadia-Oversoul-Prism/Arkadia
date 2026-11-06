/**
 * Surface chrome — how a surface contributes to the one canonical shell.
 *
 * Before this module there were three shells: the global `Shell`, plus
 * `WorkspaceShell` and `ArkanaShell` mounted *inside* it. Each owned its own
 * rail, its own header and its own composer dock, so the product rendered two
 * navigation columns and two headers at once. That is the structural reason the
 * console read as several applications sharing a repository rather than one
 * product.
 *
 * The fix is not to delete the inner layouts — they hold real, working regions —
 * but to move *ownership* of the chrome to the one shell:
 *
 *   - `Shell` owns the primary navigation, the header, the identity block and
 *     the mobile drawer. There is exactly one of each.
 *   - A surface may contribute a **context rail** (orientation for the work in
 *     front of you: projects, capabilities, conversations) and a **status line**
 *     (what the surface is doing right now). The shell renders both.
 *
 * A surface therefore never renders a second rail or a second header; it
 * *publishes* what the shell should show. This is a context, not a store: it
 * owns no persistence and no authority, and a surface's publication is cleared
 * when that surface unmounts so a stale rail can never outlive it.
 *
 * ── Why publication is guarded the way it is (AO4-01 runtime) ────────────────
 *
 * The first version of this module published from an effect whose dependency
 * list included the whole `context` object:
 *
 *     useEffect(() => {
 *       context.publish({ rail, railLabel, status });
 *       return () => context.clear();
 *     }, [context, rail, railLabel, status]);
 *
 * `context` was `useMemo(() => ({ chrome, publish, clear }), [chrome, ...])`, so
 * its identity changed **whenever `chrome` changed** — and `publish` changed
 * `chrome`. Publishing therefore re-created the context value, which re-ran
 * every consumer's effect, which published again: an unbounded React update
 * loop. Two further defects were hiding behind it:
 *
 *   1. each publication was a brand-new object, so even a byte-identical rail
 *      would have re-rendered every consumer, and
 *   2. `clear()` on unmount did not know *which* surface it was clearing. During
 *      a navigation the outgoing surface's cleanup could run after the incoming
 *      surface had already published, erasing the new chrome.
 *
 * The contract below fixes all three while preserving the typed surface:
 *
 *   - **the context value is referentially stable.** It carries `chrome` plus
 *     three `useCallback`s and no per-render object, so an effect that depends
 *     on it never re-fires merely because something was published;
 *   - **the effect depends only on the three chrome fields.** Consumers pass a
 *     freshly created object literal (`{ rail: <X />, ... }`) on every render —
 *     that is idiomatic and must stay allowed — so the object itself is never a
 *     dependency. Only its parts are, and `rail`/`status` are normally stable
 *     values (`setState(null)` identity, a string, a memoised node).
 *   - **publication is deduped by value.** `publish` ignores a call whose
 *     `(rail, railLabel, status)` is identical to what is already published, so
 *     even a re-render with a changed element identity cannot echo a new state
 *     update back through the tree;
 *   - **publication is owned.** Each `useSurfaceChrome` call takes a token at
 *     mount and only that token may publish or clear. A stale cleanup from a
 *     surface that is no longer the active publisher is a no-op, so it cannot
 *     erase the chrome a newly active surface just published.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

export interface SurfaceChrome {
  /** Orientation content for the secondary rail, or null for none. */
  rail: ReactNode | null;
  /** Accessible name for the rail region. */
  railLabel: string;
  /** A short live status line for the header, or null. */
  status: string | null;
}

const EMPTY: SurfaceChrome = { rail: null, railLabel: "Context", status: null };

/** A publication stamped with the identity of the surface that made it. */
interface OwnedChrome extends SurfaceChrome {
  owner: number | null;
}

const EMPTY_OWNED: OwnedChrome = { ...EMPTY, owner: null };

interface SurfaceChromeActions {
  /**
   * Publish `next` as the active surface's chrome.
   *
   * `owner` is the token from `useSurfaceChrome`; a publication from an owner
   * that is not the current one is ignored, which is what stops a late cleanup
   * or re-publish from a departing surface overwriting the arriving one.
   * Returns true when the call actually changed the published chrome.
   */
  publish: (next: SurfaceChrome, owner: number) => boolean;
  /** Clear the chrome, but only if `owner` is still the active publisher. */
  clear: (owner: number) => void;
}

/**
 * Two chrome values are "the same publication" when their rendered content and
 * their accessible name match. This is the dedupe key: it lets a surface
 * re-render freely without pushing an identical value through context.
 */
function sameChrome(a: SurfaceChrome, b: SurfaceChrome): boolean {
  return a.rail === b.rail && a.railLabel === b.railLabel && a.status === b.status;
}

const SurfaceChromeStateContext = createContext<OwnedChrome>(EMPTY_OWNED);
const SurfaceChromeActionsContext = createContext<SurfaceChromeActions | null>(null);

export function SurfaceChromeProvider({ children }: { children: ReactNode }) {
  const [published, setPublished] = useState<OwnedChrome>(EMPTY_OWNED);

  // The publisher reads the current value through a ref so `publish` / `clear`
  // stay `useCallback([])`-stable: they never need to be re-created when the
  // value changes, which is the whole point of splitting state from actions.
  const publishedRef = useRef<OwnedChrome>(EMPTY_OWNED);
  publishedRef.current = published;

  const publish = useCallback((next: SurfaceChrome, owner: number) => {
    const current = publishedRef.current;
    // A surface may publish when it is the active publisher, or when nothing is
    // published yet (the first surface to mount claims the chrome). It may not
    // publish over a *different* live surface's publication.
    if (current.owner !== null && current.owner !== owner) return false;
    if (sameChrome(current, next)) return false; // nothing changed — no update
    const value: OwnedChrome = {
      rail: next.rail,
      railLabel: next.railLabel,
      status: next.status,
      owner,
    };
    publishedRef.current = value;
    setPublished(value);
    return true;
  }, []);

  const clear = useCallback((owner: number) => {
    const current = publishedRef.current;
    if (current.owner !== owner) return; // a newer surface owns the chrome now
    if (current === EMPTY_OWNED) return;
    publishedRef.current = EMPTY_OWNED;
    setPublished(EMPTY_OWNED);
  }, []);

  const actions = useMemo<SurfaceChromeActions>(() => ({ publish, clear }), [publish, clear]);

  // `chrome` (state) is separate from `actions` (stable), so a consumer that
  // only publishes does not re-render when the publication changes.
  return (
    <SurfaceChromeStateContext.Provider value={published}>
      <SurfaceChromeActionsContext.Provider value={actions}>
        {children}
      </SurfaceChromeActionsContext.Provider>
    </SurfaceChromeStateContext.Provider>
  );
}

/** The published chrome without the owner token — the shape a surface renders. */
function toSurfaceChrome({ rail, railLabel, status }: OwnedChrome): SurfaceChrome {
  return { rail, railLabel, status };
}

/**
 * Publish this surface's chrome to the shell.
 *
 * Called from a surface component with a `SurfaceChrome` object. The caller may
 * (and normally does) build that object inline on every render; the effect
 * depends only on its three fields, so a new object identity alone can never
 * re-trigger publication.
 *
 * Publication is deduped by value and scoped to this surface's ownership token:
 * an unmount clears the chrome only while this surface is still the active
 * publisher, so navigating from one surface to another cannot have the outgoing
 * cleanup erase the incoming rail.
 */
export function useSurfaceChrome(chrome: SurfaceChrome) {
  const actions = useContext(SurfaceChromeActionsContext);
  const { rail, railLabel, status } = chrome;

  // The latest value, read by the effect without being a dependency: this keeps
  // the effect from re-firing just because the surface re-rendered with an equal
  // but freshly allocated node.
  const latest = useRef<SurfaceChrome>({ rail, railLabel, status });
  latest.current = { rail, railLabel, status };

  // One stable token per mounted hook instance. `0` means "not yet registered";
  // the real token is assigned on the first effect run.
  const ownerRef = useRef(0);

  useEffect(() => {
    if (!actions) return;
    if (ownerRef.current === 0) {
      ownerRef.current = OWNER_SEQUENCE++;
    }
    const owner = ownerRef.current;
    actions.publish(latest.current, owner);
    // Cleanup clears *this surface's* publication, and only if it is still the
    // active one — a departing surface must not clear its successor's chrome.
  }, [actions, rail, railLabel, status]);

  useEffect(() => {
    if (!actions) return;
    return () => {
      if (ownerRef.current !== 0) actions.clear(ownerRef.current);
    };
  }, [actions]);
}

/**
 * The current published chrome, without the owner token.
 *
 * Only the shell and tests read this. It is derived from the state context, so
 * a component that calls it *does* re-render when the publication changes —
 * which is correct: it is the thing being rendered.
 */
export function usePublishedChrome(): SurfaceChrome {
  const published = useContext(SurfaceChromeStateContext);
  return useMemo(() => toSurfaceChrome(published), [published]);
}

/**
 * Monotonic owner-token source.
 *
 * Deliberately module-level and not `useId`: the token only has to be unique
 * among live hook instances in one renderer, and a module counter is stable
 * across StrictMode's double-invoked effects (which reuse the same ref) while
 * still never colliding between two surfaces.
 */
let OWNER_SEQUENCE = 1;
