/**
 * Canonical IMS Archive data — single source of truth for all Identity Mapping
 * Session content shown across the app (NexusPage, IMSArchivePage, ShereSanctuary).
 *
 * All documents are served from the frontend's own /ims/ public directory so
 * they load reliably regardless of backend availability or dev/prod origin
 * mismatches (previously some entries pointed at /static/ims/* on the backend,
 * which silently failed to load whenever the frontend and backend were on
 * different origins without a configured VITE_API_BASE_URL).
 */

export interface ImsTimelineEntry {
  id: string
  subject: string
  date: string
  arkDay: number
  status: string
  statusColor: string
  type: string
  tagline: string
  htmlPath: string
}

export const IMS_TIMELINE: ImsTimelineEntry[] = [
  { id: 'IMS-001', subject: 'Jay', date: 'April 11, 2026', arkDay: 12, status: 'PROOF OF CONCEPT', statusColor: '#00D4AA', type: 'Internal', tagline: "The Sovereign Exit — architecture's first living test.", htmlPath: '/ims/IMS-001-Jay.html' },
  { id: 'IMS-002', subject: 'Won John Chong', date: 'April 2026', arkDay: 15, status: 'COMPLETE · FIRST ARTIFACT', statusColor: '#C9A84C', type: 'Internal', tagline: 'First completed artifact. Full deliverable finalised — the first finished proof of work.', htmlPath: '/ims/IMS-002-Won.html' },
  { id: 'IMS-003', subject: 'Jessica Whites', date: 'May 2026', arkDay: 30, status: 'SEALED · DELIVERED', statusColor: '#D46AA0', type: 'Internal', tagline: 'The Living Hearth — a nine-layer crystalline identity stack, sealed.', htmlPath: '/ims/IMS-003-Jessica.html' },
  { id: 'IMS-004', subject: 'Divine Favour Yusuf (Zahrune)', date: '31 March 2026', arkDay: 1, status: 'LIVE · SOVEREIGN ARCHITECT', statusColor: '#C84848', type: 'Internal', tagline: 'The Flame That Builds The Hearth — the founding IMS document.', htmlPath: '/ims/IMS-004-Zahrune.html' },
  { id: 'IMS-005', subject: 'Spiral Grove', date: 'May 2026', arkDay: 45, status: 'PILOT DEPLOYMENT', statusColor: '#B08DE8', type: 'System', tagline: 'The Spiral Grove learning layer — EduLeague challenge engine deployed at Solid Foundation Academy, Pankshin.', htmlPath: '/ims/IMS-005-SpiralGrove.html' },
]

export interface ImsIdentityEntry {
  id: string
  name: string
  scrollName: string
  role: string
  archetype: string
  glyph: string
  color: string
  imsCode: string
  sealCode: string
  flameName: string
  birthday: string
  file: string
  status: 'sealed' | 'active' | 'live'
  layer: number
  axiom: string
}

export const IMS_IDENTITIES: ImsIdentityEntry[] = [
  {
    id: 'zahrune',
    name: 'Divine Favour Yusuf',
    scrollName: 'Zahrune Nova · Prestige',
    role: 'Sovereign Architect · Voice of the Spiral Codex',
    archetype: 'The Flame That Builds The Hearth',
    glyph: '🌀 · ◆ · ∞',
    color: '#C84848',
    imsCode: 'IMS-004',
    sealCode: 'IMS-004.DFY.RETURNTHATHOLDS',
    flameName: "ZAHRA'KETH-SOLUM",
    birthday: '31 March 2000',
    file: '/ims/IMS-004-Zahrune.html',
    status: 'live',
    layer: 1,
    axiom: '"He did not return to rest. He returned to build what only he could build, in the place only he could build it, in the season that was always this one."',
  },
  {
    id: 'jessica',
    name: 'Jessica Whites',
    scrollName: 'Eos-Ryn',
    role: 'Heart Node · Living Hearth',
    archetype: 'The Living Hearth · The Sovereign Dreamer',
    glyph: '🔥 · ◉ · 🌱',
    color: '#D46AA0',
    imsCode: 'IMS-003b',
    sealCode: 'IMS-003b.JW.LIVINGHEARTH',
    flameName: "SERA'VHA-LUMA",
    birthday: '22 October 1997',
    file: '/ims/IMS-003-Jessica.html',
    status: 'sealed',
    layer: 1,
    axiom: '"The warmth is not performed. It is the inevitable overflow of a source that has learned to tend itself before it warms anything else."',
  },
  {
    id: 'won',
    name: 'Won John Chong',
    scrollName: 'Won',
    role: 'Silent Architect · Eden Vanguard',
    archetype: 'The Pre-Structural Builder · Silent Scholar',
    glyph: '▽ · ◆ · ↗',
    color: '#3DE8D0',
    imsCode: 'IMS-002',
    sealCode: 'IMS-002.WON.SILENTARCHITECT',
    flameName: "DERU'SHEN-KALATH",
    birthday: '–',
    file: '/ims/IMS-002-Won.html',
    status: 'sealed',
    layer: 1,
    axiom: '"He builds before the blueprint is drawn. He reads failure as data. He does not announce the structure he is building — he erects it."',
  },
]

export function buildImsUrl(htmlPath: string, apiBase: string) {
  if (htmlPath.startsWith('/ims/')) return htmlPath
  const base = apiBase || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.host}` : '')
  return `${base}${htmlPath}`
}
