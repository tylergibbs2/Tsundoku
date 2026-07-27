// Config for `just generate-frontend-sdk`, which dumps the FastAPI schema to
// openapi.json and then runs @hey-api/openapi-ts over it. The generated output
// under ts/api/ is committed.
//
// Exported as a plain object rather than via the package's `defineConfig`
// helper: openapi-ts lives in tools/codegen (pinned against TypeScript 5) and
// is deliberately not a root dependency, so it cannot be imported from here.
// Paths are relative to the repo root, which is the cwd the recipe runs in.
export default {
  input: "./openapi.json",
  // Formatting is done by the recipe via biome, not openapi-ts's own
  // postProcess, which shells out to a binary that is not on PATH under bun.
  output: {
    path: "tsundoku/blueprints/ux/static/ts/api",
  },
  plugins: [
    "@hey-api/client-fetch",
    "@hey-api/typescript",
    {
      name: "@hey-api/sdk",
      // Parse both directions against the generated Zod schemas, so a
      // frontend/backend contract drift throws at the call site rather than
      // surfacing as an undefined deep inside a component.
      validator: { request: "zod", response: "zod" },
    },
    "zod",
  ],
  // NOTE: deliberately no '@tanstack/react-query' plugin. The query keys and
  // options are hand-rolled in ts/queries.ts on top of these operations.
};
