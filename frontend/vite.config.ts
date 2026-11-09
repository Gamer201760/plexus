import { fileURLToPath } from "node:url"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"
import { htmlMeta } from "./scripts/htmlMeta.ts"

const apiUrl = process.env.API_URL ?? "http://localhost:8000"
const tileUrl = process.env.TILE_URL ?? "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
const osmCopyrightUrl = process.env.OSM_COPYRIGHT_URL ?? "https://www.openstreetmap.org/copyright"
const frontendRoot = fileURLToPath(new URL(".", import.meta.url))
const sourceRoot = fileURLToPath(new URL("./src", import.meta.url))
const apiProxy = { "/api": { target: apiUrl, changeOrigin: true } }
const extraHosts = process.env.DEV_ALLOWED_HOSTS?.split(",").filter((host) => host !== "")

export default defineConfig({
  plugins: [react(), htmlMeta(frontendRoot)],
  define: {
    __TILE_URL__: JSON.stringify(tileUrl),
    __OSM_COPYRIGHT_URL__: JSON.stringify(osmCopyrightUrl),
  },
  resolve: { alias: { "@": sourceRoot } },
  server: { proxy: apiProxy, ...(extraHosts ? { allowedHosts: extraHosts } : {}) },
  preview: { proxy: apiProxy, ...(extraHosts ? { allowedHosts: extraHosts } : {}) },
  test: {
    css: { modules: { classNameStrategy: "non-scoped" } },
    projects: [
      {
        extends: true,
        test: { name: "node", environment: "node", include: ["tests/**/*.test.ts"] },
      },
      {
        extends: true,
        test: {
          name: "dom",
          environment: "jsdom",
          include: ["tests/**/*.test.tsx"],
          setupFiles: ["tests/setup/polyfills.ts", "tests/setup/dom.ts"],
        },
      },
    ],
  },
})
