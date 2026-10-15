/**
 * Intended-destination memory for the sign-in threshold.
 *
 * A protected surface renders an auth threshold while the address bar still
 * holds the path the user asked for. Without this, both entries into the
 * sign-in surface (the threshold's "Go to sign in" and the shell's "Sign in")
 * dropped the destination: after a successful sign-in the user was left
 * standing on `/login` with no way back except the nav.
 *
 * Two sources are honoured, in order:
 *
 *  1. session memory written on the way *in* (`rememberReturnTo`) — this is
 *     what the in-app entries use, so the SPA never reloads;
 *  2. an explicit `?returnTo=` deep link — so a copied sign-in URL still
 *     returns somewhere sensible.
 *
 * Safety: the target is always resolved through the router's own
 * `resolvePath`. A return target that is not a declared route (an external
 * origin, an invented path) degrades to the router's fallback the same way any
 * unrouted pathname does — this module can never navigate off-origin, and a
 * target that resolves back to the sign-in surface is refused rather than
 * looping. The memory is consumed (cleared) on read, so one sign-in cannot
 * carry a stale destination into a later session.
 */
import { resolvePath, type Route } from "./router";

const RETURN_TO_KEY = "arkadia.returnTo";

/**
 * Remember the path the user was heading to before sign-in interrupted them.
 * Never remembers the sign-in surface itself — there would be nowhere to
 * return to.
 */
export function rememberReturnTo(pathname: string): void {
  const route = resolvePath(pathname);
  if (route.surface === "login") return;
  try {
    window.sessionStorage.setItem(RETURN_TO_KEY, pathname);
  } catch {
    // Storage unavailable (private mode, disabled cookies): the return leg is
    // simply not remembered. Sign-in itself must not fail over this.
  }
}

/**
 * Take the remembered destination, validate it through the router, and clear
 * the memory. Returns `null` when there is nowhere honest to return to: no
 * destination was recorded, storage failed, or the target resolves back to the
 * sign-in surface.
 */
export function consumeReturnTo(search: string): Route | null {
  let stored: string | null = null;
  try {
    stored = window.sessionStorage.getItem(RETURN_TO_KEY);
    window.sessionStorage.removeItem(RETURN_TO_KEY);
  } catch {
    stored = null;
  }
  const fromQuery = new URLSearchParams(search || "").get("returnTo");
  const target = stored ?? fromQuery;
  if (!target) return null;
  const route = resolvePath(target);
  if (route.surface === "login") return null;
  return route;
}
