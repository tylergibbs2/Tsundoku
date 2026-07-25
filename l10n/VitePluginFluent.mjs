import fs from "node:fs";
import path from "node:path";

/**
 * Inlines every `.ftl` file under `directory` into `window.TRANSLATIONS`,
 * keyed by path relative to this file (e.g. `en.ftl`). Consumed by
 * `ts/fluent.ts`.
 */
export default function fluent({ directory = "l10n" } = {}) {
  let root;

  const read = () => {
    const translations = {};
    for (const fp of walk(path.resolve(root, directory))) {
      if (path.extname(fp) !== ".ftl") continue;
      const key = path
        .relative(path.resolve(root, directory), fp)
        .split(path.sep)
        .join("/");
      translations[key] = fs.readFileSync(fp, "utf-8");
    }
    return translations;
  };

  return {
    name: "fluent",
    configResolved(config) {
      root = config.root;
    },
    config() {
      // `root` is not resolved yet on the first `config` call, so resolve
      // against cwd here; Vite is always invoked from the project root.
      root = root ?? process.cwd();
      return { define: { "window.TRANSLATIONS": JSON.stringify(read()) } };
    },
    configureServer(server) {
      server.watcher.add(path.resolve(root, directory));
    },
  };
}

function* walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const fp = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(fp);
    else yield fp;
  }
}
