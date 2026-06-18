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
    port: 5000,
    allowedHosts: true,
    proxy: {
      // Routes all /api calls to the live Oracle on Render.
      // This means Replit dev is always synced to production backend.
      "/api": {
        target: "https://arkadia-n26k.onrender.com",
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
