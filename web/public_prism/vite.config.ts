import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  css: {
    postcss: "./postcss.config.cjs",
  },
  build: {
    outDir: "dist"
  },
  server: {
    host: true,
    port: 5000,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "https://arkadia-n26k.onrender.com",
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
