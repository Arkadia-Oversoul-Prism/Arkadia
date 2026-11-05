/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // ── Arkadia design tokens ────────────────────────────────────────────
        // The shared palette for every surface. Surfaces must not invent their
        // own accents; a page-local hex is styling drift (pinned by
        // tests/test_console_shell_nav_contract.py).
        //
        // "Crystal Glass" (AO-001 beta): the base surfaces are obsidian and
        // cosmic black, the illumination is champagne gold and teal, and the
        // highlights are restrained cyan. The original five tokens keep their
        // exact values so every existing surface and contract test is
        // unaffected; the additions below are the glass layer.
        ink: "#080A11",
        panel: "#0E1120",
        line: "#1B2033",
        gold: "#C9A84C",
        emerald: "#00D4AA",
        azure: "#6A9FD8",
        violet: "#B08DE8",

        // Crystal Glass additions.
        obsidian: "#05060B",
        cosmic: "#0A0C16",
        crystal: "#12162A",
        champagne: "#E4C77B",
        teal: "#2FD9C0",
        cyan: "#7FE3F0",
        mist: "#A8B2C8",
      },
      fontFamily: {
        display: ["Cinzel", "serif"],
        sans: ["Inter", "DM Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      boxShadow: {
        // Layered depth for the glass surfaces: a tight contact shadow, a wide
        // ambient falloff, and an inner top highlight that reads as a lit edge.
        glass: "0 1px 0 0 rgba(255,255,255,0.06) inset, 0 18px 48px -12px rgba(0,0,0,0.72), 0 2px 8px -2px rgba(0,0,0,0.5)",
        "glass-lg":
          "0 1px 0 0 rgba(255,255,255,0.08) inset, 0 32px 80px -20px rgba(0,0,0,0.8), 0 4px 16px -4px rgba(0,0,0,0.55)",
        glow: "0 0 0 1px rgba(201,168,76,0.18), 0 0 32px -6px rgba(201,168,76,0.22)",
        "glow-teal": "0 0 0 1px rgba(47,217,192,0.2), 0 0 32px -6px rgba(47,217,192,0.24)",
      },
      backdropBlur: {
        glass: "18px",
      },
      borderRadius: {
        glass: "18px",
      },
      transitionTimingFunction: {
        crystal: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};
