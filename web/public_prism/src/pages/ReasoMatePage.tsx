/**
 * ReasoMate — the private authenticated conversational messenger lens.
 *
 * M02: this route resolves to ReasoMate, never to Oracle. The surface is shared
 * with the NovaNet hub's ReasoMate tab (components/ReasoMateSurface) so both
 * entry points render the same lens over the same runtime and substrate.
 *
 * Marker `data-testid="reasomate-private-surface"` is asserted by
 * tests/test_m02_reasomate_truth.py.
 */
export { default } from '../components/ReasoMateSurface'
