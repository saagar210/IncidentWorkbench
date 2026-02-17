import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const host = process.env.TAURI_DEV_HOST;
const cacheDir = process.env.VITE_CACHE_DIR;

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  cacheDir: cacheDir || "node_modules/.vite",
  build: {
    chunkSizeWarningLimit: 700,
    rollupOptions: {
      output: {
        manualChunks: {
          "react-vendor": ["react", "react-dom", "react-router-dom"],
          "query-vendor": ["@tanstack/react-query", "axios", "zustand"],
          "chart-vendor": ["recharts", "html2canvas"],
          "tauri-vendor": ["@tauri-apps/api", "@tauri-apps/plugin-shell", "@tauri-apps/plugin-stronghold"],
        },
      },
    },
  },
  server: {
    port: 1420,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 1421 } : undefined,
    watch: {
      ignored: ["**/src-tauri/**"]
    }
  }
});
