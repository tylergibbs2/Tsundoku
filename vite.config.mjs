import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

import fluent from "./l10n/VitePluginFluent.mjs";

const OUT_DIR = "tsundoku/blueprints/ux/static/js";

// The dev server only ever serves modules to pages rendered by FastAPI on
// :6439, so it needs a fixed port to be referenced from a template, and CORS
// for that origin.
const DEV_PORT = 5173;
const BACKEND_ORIGIN = "http://localhost:6439";

/**
 * Sends `/` on the dev server to the backend.
 *
 * There is no index.html here -- FastAPI renders the page and only pulls
 * modules from this server -- so the "Local:" URL Vite prints would otherwise
 * 404 and read as a broken dev server.
 */
function redirectRootToBackend() {
  return {
    name: "redirect-root-to-backend",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url !== "/") return next();

        res.writeHead(302, { Location: BACKEND_ORIGIN });
        res.end();
      });

      const print = server.printUrls.bind(server);
      server.printUrls = () => {
        print();
        server.config.logger.info(
          `  ->  App:     ${BACKEND_ORIGIN}  (run \`just dev-backend\`)\n` +
            "      This server only supplies modules; its own URL redirects there.\n",
        );
      };
    },
  };
}

export default defineConfig(({ command }) => ({
  // Built assets are served from the UX static mount (see tsundoku/urls.py),
  // so url() references emitted into CSS need this prefix. It is build-only:
  // applying it in dev would push every module behind the same prefix, which
  // the dev server has no reason to mirror.
  base: command === "build" ? "/ux/static/js/" : "/",
  plugins: [react(), fluent(), redirectRootToBackend()],
  // `just dev-frontend` serves modules from here and templating.py points the
  // page at them while IS_DEBUG is set. Asset URLs have to be absolute because
  // the HTML itself is served from a different origin.
  server: {
    port: DEV_PORT,
    strictPort: true,
    origin: `http://localhost:${DEV_PORT}`,
    cors: { origin: BACKEND_ORIGIN },
  },
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
    rolldownOptions: {
      input: {
        root: path.resolve("tsundoku/blueprints/ux/static/ts/App.tsx"),
      },
    },
  },
}));
