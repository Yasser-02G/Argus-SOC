import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En dev (npm run dev), le frontend tourne sur le port 5173 et le backend sur
// 8000 : ce proxy permet d'utiliser des chemins relatifs (/api/...) sans se
// heurter au CORS, exactement comme en production derrière Caddy.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/health": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
