/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-azure': '#001F3F',
        'emerald-gold': '#D4AF37',
        'sky-blue': '#7FDBFF',
      },
    },
  },
  plugins: [],
}