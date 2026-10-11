/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Arkadia design tokens. These are the shared palette for every surface;
        // surfaces must not invent their own accents.
        ink: "#080A11",
        panel: "#0E1120",
        line: "#1B2033",
        gold: "#C9A84C",
        emerald: "#00D4AA",
        azure: "#6A9FD8",
        violet: "#B08DE8",
      },
      fontFamily: {
        display: ["Cinzel", "serif"],
        sans: ["Inter", "DM Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
