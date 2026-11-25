# Linger: Human and Agent collaboration centered on Rooms

This monorepo uses React/Vite for Web, Go for TeamHub and the Local Computer
Daemon, and TypeScript for the Agent Service, Document Runtime, LLM Wiki,
Memory, and Voice services.

## Common Commands

- `pnpm install --frozen-lockfile --prefer-offline`: initialize Node dependencies
  in the current worktree when needed.
- `pnpm dev`: migrate the PostgreSQL that `TEAMHUB_DATABASE_URL` names, then run
  Web, TeamHub, and the node-services process (Agent Service, Memory, LLM Wiki,
  Document Runtime, Voice) on this machine, plus `livekit-server` from `PATH`
  whether or not a voice key is set. It starts no containers; the developer runs
  PostgreSQL.
- `docker compose up --build`: build and run every service in containers,
  PostgreSQL and LiveKit included.
- `pnpm --filter @linger/web test <test-file>`: run one Web test (the script sets the Node flags jsdom needs).
- `pnpm --filter @linger/node-services exec vitest run <test-file>`: run one
  Node Services test, including the Agent Service's under `tests/agent/`.
- `make -C apps/teamhub test`: run TeamHub unit tests.
- `pnpm contracts:generate && pnpm contracts:verify`: regenerate and verify OpenAPI consumers.
- `make check BASE=<target-ref>`: run in parallel the fast checks that the
  changes since the merge base (committed, uncommitted, and untracked)
  select; it prints the plan first, and `ALL=1` runs every fast check.
  `scripts/check-plan.mjs` holds the path-to-check map that CI also uses.
  Fast checks are local and need no Postgres, containers, or full suite.
  `BASE` is required because the built-in Skill immutability check compares
  against it; the repository assumes no default branch.
- `make check-repository-gate BASE=<target-ref>`: run the repository gate
  (migration history, commitlint, env inventory, changed-file format and lint,
  script tests, doc links).

## Structure

- `apps/web`: React Product Client; active product data comes only from TeamHub.
- `apps/teamhub`: Go service owning Account, Room, Work Item, and persisted collaboration state.
- `apps/node-services`: one Node process hosting the `agent` (Agent Service:
  Agent lifecycle, Runtime execution, and TeamHub callbacks), `memory`,
  `llm-wiki`, `document`, and `voice` roles selected by `NODE_SERVICES_ROLES`. Agent,
  Memory, and LLM Wiki share one HTTP port; the Document Runtime is the
  Hocuspocus/Yjs protocol and BlockNote/Yjs computation adapter on its own
  port, and it loads and saves native Documents' `document_bodies` rows in
  TeamHub's database. Voice supervises isolated ASR, recorder and Live workers from the voice-runtime package. TeamHub parses SKILL.md itself.
- `apps/teamhub-cli`: standalone Agent CLI calling TeamHub business APIs directly
  through the client generated from `teamhub-agent-api`; it owns its command
  schemas and host file helpers.
- `contracts`: authoritative cross-process OpenAPI and generated Go/TypeScript modules.
- `packages/document-model`: shared Room Document schema inspection and deterministic state helpers.
- `packages/service-kit`: shared isomorphic guards and helpers (`@linger/service-kit`) and the Node JSON logger and SHA-256 helper (`@linger/service-kit/node`).
- `skills`: versioned built-in Skill assets embedded into TeamHub.
- `.agents/skills/verify-linger`: acceptance recipes and an isolated
  real-service proof for a coding Agent verifying user journeys.

## Important Conventions

- Read the nearest `AGENTS.md` for the target path.
- Keep each checkout's `node_modules` local; never symlink or copy another
  checkout's installed dependency tree. Run the install command above when
  dependency checks report missing or stale dependencies; do not disable the
  check to bypass it.
- Implement the simplest solution that satisfies the current request. Do not
  design for requirements outside the current scope, and prefer existing
  dependencies over new custom infrastructure.
- A change to shared configuration (root or shared tool configs, shared
  scripts, env defaults) is done when every app that consumes it passes its
  fast checks in the same pull request, not only the one being fixed.
- A feature is done when no code it made unnecessary and no abstraction the
  request does not require is left behind.
- Prefer forward and backward compatibility across upgrades, rolling deploys,
  and mixed client/server versions (including Desktop, Daemon, CLI, and Web
  talking to newer or older TeamHub releases, as well as persisted state,
  config, and caches on users' machines). Accept previous request, config, and
  flag shapes where feasible instead of hard-cutting them. Only introduce a
  breaking change when compatibility is impractical, and explain the reason and
  rollout impact explicitly in the pull request.
- During local development, run the focused tests for the changed behavior and
  the affected fast checks. Focused Vitest or Go unit tests do not
  replace those checks. Do not run complete integration, E2E, container, or
  reliability suites by default; `make check BASE=<target-ref>` runs only the
  fast checks. Run a focused heavy scenario when
  changing that test or harness, reproducing its failure, or when real
  database, process, concurrency, or recovery semantics cannot be proved at a
  lower layer.
- Before opening a pull request, run the fast checks for every touched app:
  - Web: `make check-web` (typecheck, unit tests, and React Doctor). If the
    change adds a static import on the Room or app initial graph, also run
    `pnpm --filter @linger/web run build:assets` to check the initial JS
    budget.
  - TeamHub: `make -C apps/teamhub fmt-check` and
    `go test ./tests/integration/layout -count=1` (structural layout rules, no
    database; it has no budget to update).
  - Other apps: the matching `make check-<app>` or package `check` /
    `typecheck` from that app's `AGENTS.md`.
- Keep the owning documentation aligned in the same pull request when a change
  affects user-visible behavior, service or module ownership, cross-process
  flows or contracts, permissions, filesystem paths, lifecycle, recovery, or
  failure semantics: the nearest `AGENTS.md` or README. Keep progress and
  checklists in the issue tracker.
- Do not import source across `apps/*` boundaries. Share in-process code through
  packages and cross-process data through generated contracts.
- Edit `contracts/openapi/`, never `contracts/generated/`; regenerate after contract changes.
- When adding an app, give it a `make check-<app>` fast check and add it to
  `FAST_CHECKS` (or `HEAVY_CHECKS`) in the root `Makefile`. Add or change Make targets only when no
  existing target represents the new boundary.
- Ordinary business files and new OpenAPI component documents must not require
  Makefile edits. Create the component, `$ref` it from a top-level contract,
  and regenerate contracts. A new top-level contract is one entry in
  `contractEntries` in `contracts/codegen/contracts.ts`.
- Pull requests touching the user message → `provider_ready` path must state whether they add a
  network round trip or file walk while the user waits, and justify it or keep it
  off the critical path.
- Keep secrets in the ignored root `.env`; never commit or print credentials.
- Every environment variable that runtime code reads must be in `.env.example`
  or listed in `scripts/env-inventory.json` with its owner; prefer a code
  default over a new variable. `pnpm env:inventory:check` enforces this in
  `make check-repository` and `make check-repository-gate`. `.env.example` keeps every
  entry active with the value `pnpm dev` uses (the code default or the
  matching `scripts/local-defaults.env` value), so a copied template turns on
  every feature that needs no personal key; only personal keys (Composio,
  Soniox) stay empty. Comment out only entries whose value depends on the host
  or would break a mode (for example `NODE_ENV`, `COMPOSE_PROJECT_NAME`).
  Every fixed local default for `pnpm dev` lives in
  `scripts/local-defaults.env`; `scripts/with-local-env.mjs` only merges files.
- The repository is English-only: docs, code, comments, logs, user-facing
  strings, prompts, Skills, tests, fixtures, and benchmark data.
  `make check-repository-gate` rejects CJK ideographs in changed files. The
  only exceptions are the translation catalogs under
  `apps/web/src/i18n/locales/` (Web client) and `apps/desktop/src/i18n/locales/`
  (desktop shell); text in another language goes nowhere else.
  - NO: a test fixture with a literal Chinese sentence.
  - OK: the same text as escaped code points (`"\u4f60\u597d"`), or kana,
    accented Latin, or emoji when any unspaced script will do.

## Cross-Module Conventions

New and changed code follows these targets. Do not migrate untouched code only
to comply.

- HTTP errors use one envelope,
  `{"error": {"code", "message", "request_id", "details"?}}`, with codes
  declared in the OpenAPI component: UPPER_SNAKE on the public Product (Web)
  API, lower snake_case on the Agent API and internal contracts, whose codes
  the teamhub CLI passes through (see `apps/teamhub-cli/AGENTS.md`). Go handlers write it through
  `writeError`; never return a bare `{"error": "..."}` or a hand-built `gin.H`.
- Logging: Go uses `slog`; Node services log through the injected
  `createJsonLogger` from `@linger/service-kit/node`, never `console.*`
  (CLIs print plain text). Events are `<area>.<what>` with snake_case fields.
- Configuration: each app reads the environment in one config module
  (`config.ts`, `internal/config`) and passes typed values down. Do not read
  `process.env` or `os.Getenv` elsewhere or write to `process.env`; each
  default lives in exactly one place.
- Shared helpers: guards, hashing, sleep, and IDs come from
  `@linger/service-kit` or `internal/ids`. Add a helper there once a second
  app needs it; never copy one.
- Naming: `TeamHub`/`teamHub` in identifiers (`teamhub` only in paths,
  packages, and CLI names). Handwritten Go uses initialisms (`ID`, `URL`,
  `HTTP`).
- TypeScript: export functions as `function` declarations; object types are
  `interface` (lint-enforced); private class state uses `#field`.
- Comments explain why or state an invariant; never restate
  the code. No issue or pull request numbers, plan-step labels, or history
  ("previously", "used to"). Exported Go declarations and packages have doc
  comments; `make -C apps/teamhub lint-go BASE=<target-ref>` checks this on new
  and changed declarations only.
- Do not drive behavior by matching natural-language wording: user text,
  third-party error prose, model prose, or our own human-readable labels.
  Carry the decision in structured fields, error codes, or model structured
  output, and keep human-readable text for display only.
- Serve users of any language through
  language-agnostic mechanisms: engine language settings, structured fields,
  model structured output, and prompts that answer in the user's language.
  Never add per-language keyword lists, regexes, or model-facing examples.
  Tests that need non-ASCII or unspaced text use escaped code points, accented
  Latin, emoji, or another unspaced script.
