import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Arkadia backend owns the route surface. The dev server proxies API traffic
// to a locally booted `uvicorn api.main:app` (default http://localhost:8080).
// Anchored regex keys so the SPA's own routes are never shadowed by a broad
// "/api" prefix match.
const BACKEND = process.env.ARKADIA_BACKEND ?? "http://localhost:8080";

export default defineConfig({
  base: "/operator/",
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    allowedHosts: true,
    proxy: {
      "^/api(?:/|$)": { target: BACKEND, changeOrigin: true },
      "^/solspire(?:/|$)": { target: BACKEND, changeOrigin: true },
      "^/health$": { target: BACKEND, changeOrigin: true },
      "^/openapi\\.json$": { target: BACKEND, changeOrigin: true },
      "^/docs(?:/|$)": { target: BACKEND, changeOrigin: true },
      "^/static(?:/|$)": { target: BACKEND, changeOrigin: true },
    },
  },
  build: { outDir: "dist", sourcemap: false },
});
