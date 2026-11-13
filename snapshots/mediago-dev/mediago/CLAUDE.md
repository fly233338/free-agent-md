# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MediaGo is a cross-platform video downloader supporting m3u8/HLS streams. The codebase is a pnpm monorepo with two delivery products:

1. **Desktop app** (`apps/electron` + `apps/ui`) — Electron wrapper that launches Go Core as a subprocess
2. **Docker Web app** (`apps/core` + `apps/ui`) — Docker runs Go Core directly; the main UI is embedded in the Core binary

The Player UI (`apps/player-ui`) is also embedded in every Core binary. Electron Core serves `/player/` but suppresses the embedded main UI because Electron owns the main renderer.

## Documentation Site Safety

`docs/` is the production VitePress source directory. Everything placed there can be packaged and deployed to the public documentation site.

- Never create agent planning or working artifacts anywhere under `docs/`. This includes `docs/plans/`, `docs/superpowers/`, design or implementation plans, audit reports, task logs, handoff notes, scratch Markdown, generated prompts, and session notes.
- Only add or edit files under `docs/` when they are intentional public documentation, documentation assets, VitePress source/configuration, or tests required for the documentation site.
- Store persistent internal planning artifacts under `.agents/plans/`. Store disposable artifacts in the system temporary directory.
- This rule overrides any skill, tool, or template that defaults to writing plans under `docs/` or `docs/plans/`.
- Before finishing a task that touches documentation, inspect `git status --short -- docs` and remove accidental internal artifacts without deleting legitimate documentation content.

## Common Commands

```bash
pnpm install                # Install all dependencies (run once per clone)
task dev:electron           # Start Electron desktop dev environment (HMR)
task dev:web                # Start Web Core directly plus the Vite UI
task build:electron         # Production build for Electron
task build:docker           # Build the deployable Web image
pnpm core:dev               # Start Go Core dev server (port 9900)
pnpm core:build             # Compile Go Core binary
pnpm player:dev             # Start Player dev (alias for core:dev)
pnpm player:build           # Build Player (alias for core:build)
pnpm deps:download          # Download third-party tools (ffmpeg, BBDown, etc.)
pnpm deps:download:all      # Download tools for all platforms
pnpm lint                   # Lint with oxlint
pnpm lint:fix               # Auto-fix lint issues
pnpm format                 # Format with oxfmt
pnpm format:check           # Check formatting without modifying
pnpm check                  # Full check: lint + format + type check
pnpm type:check             # TypeScript type checking via Turborepo
pnpm pack:electron          # Build + package Electron distributable
```

Commits use Conventional Commits format (e.g. `feat(electron): add queue UI`).

## Architecture

### Monorepo Layout

**Apps:**

- **`apps/core/`** — Go (Gin) REST API backend for download orchestration. Runs on port 9900. Uses SQLite (GORM), SSE for real-time events, PTY for capturing download tool output, and embeds both browser UIs through `//go:embed`.
- **`apps/electron/`** — Electron main process (tsdown build, inversify DI). Launches Go Core via `@mediago/service-runner`.
- **`apps/ui/`** — Shared React 19 frontend (Vite 8, Ant Design 6, Zustand, TailwindCSS 4, i18next). Used by both Electron and server targets.
- **`apps/player-ui/`** — React 19 frontend for player (Vite 8, shadcn/ui, video.js, TailwindCSS 4). Built assets are embedded into Go Core via `//go:embed`.

**Packages:**

- **`packages/common/`** — Platform-agnostic shared types, constants, and utilities
- **`packages/core-sdk/`** — TypeScript SDK for Go Core REST API (Axios, SSE via eventsource)
- **`packages/electron-preload/`** — Electron preload scripts for IPC bridge
- **`packages/browser-extension/`** — Browser extension (Lit web components)
- **`docs/`** — VitePress documentation (Chinese, English, Japanese)

### Multi-Target Build

The `APP_TARGET` env var (`electron` | `server`) controls which backend the UI builds against. Both targets share the same React UI but connect via different transports:

- **Electron**: IPC bridge (preload) + Go Core direct (via `@mediago/core-sdk`)
- **Server/Web**: HTTP/WebSocket + Go Core direct (via `@mediago/core-sdk`)

The UI adapter layer (`apps/ui/src/hooks/adapters/`) abstracts this: `electron.ts` provides IPC bridge in desktop mode, `platform-stubs.ts` provides no-op stubs in web mode, and `index.ts` exports `platformApi` which selects the appropriate adapter.

### Key Patterns

- **Go Core lifecycle**: Electron launches Core via `@mediago/service-runner`; Task and Docker execute Core directly for Web usage
- **Dependency Injection**: inversify with `@inversifyjs/binding-decorators` in Electron backend
- **State Management**: Zustand in the UI
- **Real-time events**: Go Core emits SSE events (`/api/events`); the UI's `api/events.ts` subscribes and dispatches to React via a listener pattern
- **TypeScript**: Strict mode with experimental decorators and decorator metadata enabled
- **Module format**: ES Modules everywhere

## Tooling

- **Package manager**: pnpm 10.15.0 (enforced via `packageManager` field)
- **Build orchestration**: Turborepo
- **App bundling**: tsdown for Node/Electron, Vite 8 for UI apps
- **Go builds**: Task and pnpm invoke `packages/tooling/src/core-build/cli.ts`, which orchestrates `go build` / `go run` in `apps/core`
- **Linter**: oxlint (config in `.oxlintrc.json`)
- **Formatter**: oxfmt (config in `.oxfmtrc.json`)
- **Pre-commit**: husky + lint-staged (runs oxlint --fix + oxfmt --write on staged files)
- **Electron packaging**: electron-builder

## Style Conventions

- TypeScript, ES modules, 2-space indentation, UTF-8, LF endings
- Components: PascalCase. Utilities: camelCase. Constants: SCREAMING_SNAKE_CASE
- UI port: 8555 (strict). Go Core port: 9900. Player UI port: 8556
