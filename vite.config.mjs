import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import fluent from "./l10n/VitePluginFluent.mjs";

const OUT_DIR = "tsundoku/blueprints/ux/static/js";

export default defineConfig(({ mode }) => {
  const isDev = mode === "development";

  return {
    // Built assets are served from the UX static mount (see tsundoku/urls.py),
    // so url() references emitted into CSS need this prefix.
    base: "/ux/static/js/",
    plugins: [react(), fluent()],
    // `vite build` forces NODE_ENV=production, which would give us React's
    // production build even in watch mode. Opt back into the development
    // build so component warnings survive, as they did under webpack.
    define: isDev
      ? { "process.env.NODE_ENV": JSON.stringify("development") }
      : {},
    css: {
      preprocessorOptions: {
        scss: {
          // Our stylesheets and bulma 0.9.x still use `@import`, which Sass has
          // deprecated. Silence it (and bulma's internal color-function use)
          // rather than migrating; that is blocked on bulma 1.x.
          silenceDeprecations: ["import", "global-builtin", "color-functions"],
          quietDeps: true,
        },
      },
    },
    build: {
      outDir: OUT_DIR,
      // Flat output so everything lands directly in static/js/, which is the
      // directory the Dockerfile copies out of the frontend build stage.
      assetsDir: ".",
      emptyOutDir: true,
      manifest: true,
      // Readable output while watching, matching the old webpack.dev.js.
      minify: !isDev,
      sourcemap: isDev ? "inline" : false,
      rolldownOptions: {
        input: {
          root: path.resolve("tsundoku/blueprints/ux/static/ts/App.tsx"),
        },
      },
    },
  };
});
