import path from "node:path";
import { defineConfig } from "vitest/config";

// Frontend logic only: API helpers, form checks and mappers in src/lib.
// Screens and components stay checked by hand (see docs/process/TESTING.md).
export default defineConfig({
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/lib/**/*.ts"],
      // Wiring to better-auth and the environment: no rules of our own to break.
      exclude: ["src/lib/auth.ts", "src/lib/auth-client.ts", "src/lib/backend.ts"],
      reporter: ["text", "json-summary", "lcov"],
    },
  },
});
