import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // dev: ส่ง /api ไป backend โดยไม่ติด CORS
      "/api": "http://localhost:8000",
    },
  },
});
