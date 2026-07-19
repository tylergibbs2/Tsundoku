default: fmt check

# Install backend (uv) and frontend (bun) dependencies
sync:
    uv sync --all-extras
    bun install

# Format Python (ruff) and frontend (prettier). Pass --fix to also apply lint autofixes.
fmt fix="":
    #!/usr/bin/env bash
    set -euo pipefail
    uv run ruff format
    {{ if fix == "--fix" { "uv run ruff check --fix" } else { "true" } }}
    bun run prettier . --write --list-different

# Lint, type-check, and test everything. Pass --fix to auto-apply fixes.
check fix="":
    #!/usr/bin/env bash
    set -euo pipefail
    {{ if fix == "--fix" { "uv run ruff format" } else { "uv run ruff format --check" } }}
    {{ if fix == "--fix" { "uv run ruff check --fix" } else { "uv run ruff check" } }}
    uv run ty check
    uv run pytest
    {{ if fix == "--fix" { "bun run prettier . --write --list-different" } else { "bun run prettier . --list-different" } }}

# Run the webpack frontend build in watch mode
dev-frontend:
    bun run dev

# Run the Tsundoku backend server
dev-backend:
    uv run python -m tsundoku
