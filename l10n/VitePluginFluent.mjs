import fs from "node:fs";
import path from "node:path";

const MODULE_ID = "virtual:fluent";
const RESOLVED_ID = "\0virtual:fluent";

/**
 * Exposes every `.ftl` file under `directory` as `virtual:fluent`, a module
 * mapping file name to contents (e.g. `{ "en.ftl": "..." }`). Consumed by
 * `ts/fluent.ts`.
 *
 * Being a real module rather than a `define` replacement is what makes
 * translations live-reloadable: editing a `.ftl` invalidates this module, and
 * since the components that call `getInjector()` do so at module scope,
 * nothing accepts the update and Vite falls back to a full page reload.
 */
export default function fluent({ directory = "l10n" } = {}) {
  let root = process.cwd();

  const dir = () => path.resolve(root, directory);

  const read = () => {
    const translations = {};
    for (const fp of walk(dir())) {
      if (path.extname(fp) !== ".ftl") continue;
      const key = path.relative(dir(), fp).split(path.sep).join("/");
      translations[key] = fs.readFileSync(fp, "utf-8");
    }
    return translations;
  };

  return {
    name: "fluent",

    configResolved(config) {
      root = config.root;
    },

    resolveId(id) {
      if (id === MODULE_ID) return RESOLVED_ID;
    },

    load(id) {
      if (id === RESOLVED_ID)
        return `export default ${JSON.stringify(read())};`;
    },

    configureServer(server) {
      server.watcher.add(dir());

      const onChange = (file) => {
        if (path.extname(file) !== ".ftl") return;

        const mod = server.moduleGraph.getModuleById(RESOLVED_ID);
        if (mod) server.moduleGraph.invalidateModule(mod);

        server.ws.send({ type: "full-reload" });
        server.config.logger.info(
          `  fluent: ${path.relative(root, file)} changed, reloading`,
          { timestamp: true },
        );
      };

      server.watcher.on("change", onChange);
      server.watcher.on("add", onChange);
      server.watcher.on("unlink", onChange);
    },
  };
}

function* walk(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const fp = path.join(directory, entry.name);
    if (entry.isDirectory()) yield* walk(fp);
    else yield fp;
  }
}
