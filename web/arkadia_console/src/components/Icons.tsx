/**
 * The Arkadia icon set — minimalist line icons, one stroke weight, one grid.
 *
 * Every icon is drawn on a 24×24 box with a 1.5 stroke, round caps and joins,
 * and `currentColor`, so an icon inherits the colour of the control it sits in
 * and the design system stays the single owner of colour. No icon carries a
 * fill: the set is line-only by design, which is what keeps the navigation
 * reading as one system rather than a collection of borrowed glyphs.
 *
 * Icons are decorative by default (`aria-hidden`), because every one of them
 * sits beside a text label. A control that is icon-only must pass its own
 * accessible name.
 */
import type { SurfaceId } from "../lib/surfaces";

const BASE = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
  focusable: false,
};

function Svg({ children }: { children: React.ReactNode }) {
  return <svg {...BASE}>{children}</svg>;
}

/** Home — a crystal prism: the product's own mark, abstracted. */
export function IconHome() {
  return (
    <Svg>
      <path d="M12 3 4 9.5v8L12 21l8-3.5v-8L12 3Z" />
      <path d="M12 3v18M4 9.5l8 4 8-4" />
    </Svg>
  );
}

/** Arkana — a conversation orbit. */
export function IconArkana() {
  return (
    <Svg>
      <circle cx="12" cy="12" r="3" />
      <ellipse cx="12" cy="12" rx="9" ry="4.5" transform="rotate(-28 12 12)" />
      <circle cx="19.2" cy="8.2" r="1.1" />
    </Svg>
  );
}

/** Projects — layered planes. */
export function IconProjects() {
  return (
    <Svg>
      <path d="M3 8.5 12 4l9 4.5-9 4.5-9-4.5Z" />
      <path d="M3 13.5 12 18l9-4.5" />
      <path d="M3 17.5 12 22l9-4.5" />
    </Svg>
  );
}

/** Engineering Lab — a bounded bracket with a node. */
export function IconLab() {
  return (
    <Svg>
      <path d="M8 4H5v16h3M16 4h3v16h-3" />
      <circle cx="12" cy="12" r="2.4" />
      <path d="M12 9.6V6.5M12 14.4v3.1" />
    </Svg>
  );
}

/** Weaver — interlocking threads. */
export function IconWeaver() {
  return (
    <Svg>
      <path d="M4 7c4 0 4 10 8 10s4-10 8-10" />
      <path d="M4 17c4 0 4-10 8-10s4 10 8 10" />
    </Svg>
  );
}

/** Solariun — a sun over a horizon. */
export function IconSolariun() {
  return (
    <Svg>
      <circle cx="12" cy="10" r="3.4" />
      <path d="M12 2.6v1.8M12 15.6v1.8M4.6 10h1.8M17.6 10h1.8M6.8 4.8l1.3 1.3M15.9 13.9l1.3 1.3M17.2 4.8l-1.3 1.3M8.1 13.9l-1.3 1.3" />
      <path d="M3 20h18" />
    </Svg>
  );
}

/** Knowledge OS — a graph of records. */
export function IconKnowledge() {
  return (
    <Svg>
      <circle cx="6" cy="7" r="2.2" />
      <circle cx="18" cy="7" r="2.2" />
      <circle cx="12" cy="17.5" r="2.2" />
      <path d="M8.2 7h7.6M7.2 9l3.6 6.6M16.8 9l-3.6 6.6" />
    </Svg>
  );
}

/** NovaNet — a transmission field. */
export function IconNovaNet() {
  return (
    <Svg>
      <circle cx="12" cy="12" r="2" />
      <path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7" />
      <path d="M5.6 5.6a9 9 0 0 0 0 12.8M18.4 5.6a9 9 0 0 1 0 12.8" />
    </Svg>
  );
}

/** Settings — a calibrated dial. */
export function IconSettings() {
  return (
    <Svg>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2.8v2.4M12 18.8v2.4M4.5 12H2.1M21.9 12h-2.4M6.7 6.7 5 5M19 19l-1.7-1.7M17.3 6.7 19 5M5 19l1.7-1.7" />
    </Svg>
  );
}

/** SolSpire — an enterprise tower. */
export function IconSolSpire() {
  return (
    <Svg>
      <path d="M12 2.8 6 7v14h12V7l-6-4.2Z" />
      <path d="M9.5 21v-5h5v5M9.5 10h5" />
    </Svg>
  );
}

/** Operator — a boundary inspector. */
export function IconOperator() {
  return (
    <Svg>
      <rect x="3.5" y="3.5" width="17" height="17" rx="2.5" />
      <path d="M3.5 9h17M9 9v11.5" />
    </Svg>
  );
}

/** About — an open book. */
export function IconAbout() {
  return (
    <Svg>
      <path d="M12 6.5C10.4 5.2 8.2 4.6 4.5 4.6v13c3.7 0 5.9.6 7.5 1.9 1.6-1.3 3.8-1.9 7.5-1.9v-13c-3.7 0-5.9.6-7.5 1.9Z" />
      <path d="M12 6.5v13" />
    </Svg>
  );
}

/** Sign in — a threshold. */
export function IconLogin() {
  return (
    <Svg>
      <path d="M14 3.5h4.5A1.5 1.5 0 0 1 20 5v14a1.5 1.5 0 0 1-1.5 1.5H14" />
      <path d="M10 8l4 4-4 4M14 12H3.5" />
    </Svg>
  );
}

/** N-ATLaS — a test probe. */
export function IconProbe() {
  return (
    <Svg>
      <path d="M9 3.5h6M12 3.5v6.2l4.6 8a2 2 0 0 1-1.7 3H9.1a2 2 0 0 1-1.7-3l4.6-8V3.5Z" />
      <path d="M7.6 15.5h8.8" />
    </Svg>
  );
}

/** Chevron — used by disclosure and back controls. */
export function IconChevron({ direction = "right" }: { direction?: "left" | "right" | "down" }) {
  const rotate = direction === "left" ? 180 : direction === "down" ? 90 : 0;
  return (
    <Svg>
      <path d="M9 5l7 7-7 7" transform={`rotate(${rotate} 12 12)`} />
    </Svg>
  );
}

/** Arrow — the "continue into" affordance. */
export function IconArrow() {
  return (
    <Svg>
      <path d="M4 12h15M13 6l6 6-6 6" />
    </Svg>
  );
}

/** Search. */
export function IconSearch() {
  return (
    <Svg>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="M15.4 15.4 21 21" />
    </Svg>
  );
}

/** Shield — governance and authorization. */
export function IconShield() {
  return (
    <Svg>
      <path d="M12 2.8 4.5 6v6.2c0 4.4 3.1 7.6 7.5 9 4.4-1.4 7.5-4.6 7.5-9V6L12 2.8Z" />
      <path d="M9 12.2l2.2 2.2 4-4.2" />
    </Svg>
  );
}

/** Menu — the mobile drawer control. */
export function IconMenu() {
  return (
    <Svg>
      <path d="M4 7h16M4 12h16M4 17h16" />
    </Svg>
  );
}

/** Close. */
export function IconClose() {
  return (
    <Svg>
      <path d="M6 6l12 12M18 6 6 18" />
    </Svg>
  );
}

/** The surface → icon map. One table, so a new surface cannot ship iconless. */
export const SURFACE_ICONS: Record<SurfaceId, () => JSX.Element> = {
  home: IconHome,
  arkana: IconArkana,
  projects: IconProjects,
  "engineering-lab": IconLab,
  weaver: IconWeaver,
  solariun: IconSolariun,
  knowledge: IconKnowledge,
  novanet: IconNovaNet,
  settings: IconSettings,
  solspire: IconSolSpire,
  operator: IconOperator,
  about: IconAbout,
  login: IconLogin,
  "n-atlas": IconProbe,
};
