default: fmt check

# Install backend (uv) and frontend (bun) dependencies
sync:
    uv sync --all-extras
    bun install

# Format Python (ruff) and frontend (biome). Pass --fix to also apply lint autofixes.
fmt fix="":
    #!/usr/bin/env bash
    set -euo pipefail
    uv run ruff format
    {{ if fix == "--fix" { "uv run ruff check --fix" } else { "true" } }}
    bun run fmt

# Lint, type-check, and test everything. Pass --fix to auto-apply fixes.
check fix="":
    #!/usr/bin/env bash
    set -euo pipefail
    {{ if fix == "--fix" { "uv run ruff format" } else { "uv run ruff format --check" } }}
    {{ if fix == "--fix" { "uv run ruff check --fix" } else { "uv run ruff check" } }}
    uv run ty check
    uv run pytest
    # Vite transpiles TS without checking it, unlike ts-loader before it.
    bun run typecheck
    # Biome replaces prettier and adds linting, which this repo had none of.
    {{ if fix == "--fix" { "bun run check:fix" } else { "bun run check" } }}

# Regenerate the typed frontend SDK and Zod schemas from the FastAPI schema
generate-frontend-sdk:
    #!/usr/bin/env bash
    set -euo pipefail
    # create_app() builds the router graph without touching the database, so
    # the schema can be dumped without a running server.
    uv run python -c "import json; from tsundoku.app import create_app; print(json.dumps(create_app().openapi(), indent=2))" > openapi.json
    # Invoked by path so openapi-ts resolves the TypeScript 5 pinned in
    # tools/codegen rather than the app's TypeScript 7 (see that package.json).
    # Run through bun explicitly: the bin shebang wants node, which we do not
    # install.
    bun tools/codegen/node_modules/@hey-api/openapi-ts/bin/run.js -f openapi-ts.config.mjs
    bun x biome format --write tsundoku/blueprints/ux/static/ts/api

# Run the Vite dev server, which hot-reloads the frontend and l10n catalogs.
# Requires the backend to run with IS_DEBUG set so pages load modules from it.
dev-frontend:
    bun run dev

# Run the Tsundoku backend server in debug mode, pointing pages at the Vite
# dev server above. Drop IS_DEBUG to serve the built bundle instead.
dev-backend:
    IS_DEBUG=1 uv run python -m tsundoku
