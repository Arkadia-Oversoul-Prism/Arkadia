import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import tailwindcss from "tailwindcss"
import autoprefixer from "autoprefixer"

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      plugins: [tailwindcss, autoprefixer],
    },
  },
  build: {
    outDir: "dist"
  },
  server: {
    host: true,
    allowedHosts: true,
    proxy: {
      // Dev only — Replit workflow runs the FastAPI backend on :8000.
      // In production on Vercel, set VITE_API_BASE_URL to the Render URL
      // and the dashboard will hit it directly (CORS already open).
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
