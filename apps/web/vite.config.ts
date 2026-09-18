import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Сборка кладётся в dist/ и целиком отдаётся статикой из gateway: отдельного
// веб-сервера у интерфейса нет. В разработке /api проксируется на тот же
// gateway, поэтому путь запроса одинаков и в dev, и в проде.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Алиас @ → src/: tsconfig о нём знает, но резолвит импорты сборщик.
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_API_PROXY ?? "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
  build: { outDir: "dist", sourcemap: true },
});
