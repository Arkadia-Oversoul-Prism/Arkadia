import { useEffect, useState } from "react"

/**
 * Tiny matchMedia subscription. SSR-safe (defaults to false on server).
 * Re-renders when the breakpoint flips.
 */
export function useMediaQuery(query: string): boolean {
  const get = () =>
    typeof window !== "undefined" && window.matchMedia
      ? window.matchMedia(query).matches
      : false

  const [matches, setMatches] = useState<boolean>(get)

  useEffect(() => {
    if (typeof window === "undefined" || !window.matchMedia) return
    const mql = window.matchMedia(query)
    const onChange = () => setMatches(mql.matches)
    setMatches(mql.matches)
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [query])

  return matches
}
