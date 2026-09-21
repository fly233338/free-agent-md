# AGENTS.md — Working in the Brigade codebase

This guide is for humans and AI coding agents contributing to Brigade. It covers
the layout, the commands, the conventions you must follow, and the recipes for
common changes. Read it before you touch the tree.

For user-facing docs see [README.md](README.md). For the release flow see
[docs/RELEASING.md](docs/RELEASING.md).

---

## What Brigade is

A single-operator, multi-agent AI-crew runtime written in TypeScript. It runs as a
headless WebSocket **gateway** (the state-holding daemon) with thin clients (a chat
TUI, `connect`, channel adapters). It is built on the **pi** SDK
(`@earendil-works/pi-agent-core` + `@earendil-works/pi-ai` +
`@earendil-works/pi-coding-agent` + `@earendil-works/pi-tui`, pinned exact at
`0.79.9`) and adds product layers on top: memory, skills, sub-agents, tools, an org
hierarchy, channels, cron, an extension SDK, and a dual-mode storage layer.

- **Stack:** TypeScript (strict), ESM, Node **≥ 22.12**, **npm** (never pnpm).
- **Build:** `tsc` → `dist/`. No bundler.
- **Tests:** Node's built-in `node:test`, run via `tsx`.
- **State:** everything under `~/.brigade/` (override: `BRIGADE_STATE_DIR`).

---

## Naming & brand conventions (MUST follow)

- The product is **Brigade**. In code, comments, copy, CLI help, error messages,
  env vars, daemon labels, and docs, refer to the agent SDK **only** as `pi` /
  `@earendil-works/pi-coding-agent`. Do not name other third-party AI agent projects.
- **Never** commit secrets, real personal data (names, phone numbers, emails), or
  local absolute paths. Use placeholders (`+1 555 010 0001`, `/path/to/project`).
- The mascot is 🦁 the Pride. No other animal/symbol.
- `templates/workspace/` holds default persona files and is **off-limits**:
  behavioural fixes go in code, never in template content.
- No `Co-Authored-By` trailers on commits.

Daemon labels (don't rename): macOS launchd `com.brigade.gateway`, Linux systemd
`brigade-gateway`, Windows Task Scheduler `BrigadeGateway`.

---

## Commands

| Task | Command |
|---|---|
| Build | `npm run build` (`tsc -p tsconfig.build.json` → `dist/`) |
| Build (watch) | `npm run build:watch` |
| Typecheck | `npm run typecheck` (`tsc -p tsconfig.json --noEmit`, includes tests) |
| Test (all) | `npm test` (`node scripts/run-tests.mjs`) |
| Test (one file) | `npm test -- src/agents/tools/registry.test.ts` |
| Memory eval/bench | `npm run bench` |
| Run built binary | `npm run brigade -- <args>` (e.g. `npm run brigade -- agent -m "hi"`) |
| Dev (build-then-run) | `npm run dev -- <args>` |
| Dev (no build, tsx) | `npm run dev:tsx -- <args>` |
| Dev (auto-restart) | `npm run watch` |
| Clean | `npm run clean` |

Before opening a PR, all three of these must pass: `npm run typecheck`,
`npm test`, `npm run build`.

**Test isolation:** `scripts/run-tests.mjs` pins `BRIGADE_STATE_DIR` to a fresh
tempdir so tests never touch your real `~/.brigade`. There are **281** `.test.ts`
files under `src/`.

---

## Repository layout

```
brigade/  (working tree; storage is ~/.brigade)
├── brigade.mjs                 # bin shim: enforces Node ≥22.12, routes to dist/entry.js
├── package.json                # npm; pi 0.79.9 pinned exact
├── tsconfig.json               # typecheck config (includes tests)
├── tsconfig.build.json         # build config (emits dist/, excludes tests/templates)
├── scripts/                    # run-brigade.mjs, run-tests.mjs, build-done.mjs, convex-*.mjs
├── skills/                     # 56 bundled skill directories
├── templates/workspace/        # default persona files — OFF LIMITS for edits
├── convex/                     # Convex schema + functions (optional storage backend)
└── src/
    ├── entry.ts                # CLI entry (fast-path version/help, lazy dispatch)
    ├── extension-sdk.ts        # public plugin SDK (defineModule + re-exports)
    ├── cli/                    # command files + program/build-program.ts (command registry)
    ├── core/                   # gateway server.ts, daemon/ installers, dispatch
    ├── agents/                 # the runtime (see below) — the bulk of the code
    │   ├── agent-loop.ts       # per-turn loop
    │   ├── session-wiring.ts   # toolset assembly + before-tool-call guards
    │   ├── tools/              # Brigade-native tools + registry.ts
    │   ├── memory/             # facts store, decay, auto-recall, consolidate
    │   ├── skills/             # 6-source discovery, eligibility, manage
    │   ├── subagent-*.ts       # spawn, policy, abort cascade, completion bridge
    │   ├── channels/           # adapter contract + inbound-pipeline + whatsapp/
    │   ├── routing/            # inbound → (agentId, sessionKey)
    │   ├── org/                # org/Pride hierarchy + A2A policy
    │   └── extensions/         # plugin engine + bundled modules/ (web search, etc.)
    ├── tideline/               # long-term memory engine (hybrid recall, link graph)
    ├── system-prompt/          # assembler.ts + sections (persona pin, org anchor)
    ├── sessions/               # session store, write-lock, transcript repair
    ├── storage/                # dual-mode store: local/ (filesystem) + convex/
    ├── config/                 # brigade.json schema, io, validators
    ├── providers/              # model provider catalog + auth detection
    ├── auth/ · security/       # auth profiles, encryption (libsodium seal)
    ├── cron/                   # scheduler + isolated-agent run executor
    ├── tui/ · ui/              # terminal client + brand frames
    └── workspace/              # persona file loaders (bootstrap.ts)
```

---

## Conventions (non-negotiable)

### ESM imports — always include the `.js` extension
```ts
import { makeAgentsListTool } from "./agents-list-tool.js";  // ✅
import { makeAgentsListTool } from "./agents-list-tool";     // ❌ breaks at runtime
```
This applies to every relative import. The project compiles TS → ESM (NodeNext).

### Strict TypeScript
`strict`, `noUncheckedIndexedAccess`, and `noImplicitOverride` are on. Avoid `any`
except for unavoidable schema/plugin boundaries. Tests must pass `npm run
typecheck`.

### Ownership gates
Privileged tools use one of two postures — prefer the first:
1. **Per-call gate:** the tool is registered for everyone but branches on
   `opts.senderIsOwner` to refuse mutating actions for channel peers (e.g.
   `cron list` is allowed, `cron add` is not). Per-action granularity.
2. **Blanket `ownerOnly: true`:** refused to non-owners at registration. Use when
   *every* action is privileged (e.g. `manage_provider`, `composio`).
   `senderIsOwner` defaults to `false`; only an explicit owner flow sets it `true`.

### Memory origin isolation (load-bearing)
Every memory read/write threads a `MemoryRecordOrigin` (`owner` vs.
`channel+conversationId+sessionKey`). Owner facts are never visible to peers;
channel facts recall only on an exact origin match. Dedup is same-origin only.
Auto-recall filters by origin **before** injecting. Any new memory path must thread
origin or isolation breaks silently.

### Config & secrets
`brigade.json` writes keep 5 forensic backups (`.bak` + `.bak.{1..4}`, mode 0600).
Secrets use `${VAR_NAME}` references that resolve at read and are **restored** (not
persisted resolved) on write. Keep `brigade secrets audit` clean.

### No per-cwd persona walker
Brigade does **not** walk project rule files. Persona comes from
`~/.brigade/workspace/` only.

---

## Recipes

### Add a tool
1. Create `src/agents/tools/my-tool.ts` exporting a `makeMyTool()` factory that
   returns a `BrigadeTool` (TypeBox params, `jsonResult`).
2. Register it in `src/agents/tools/registry.ts` (`createBrigadeTools`).
3. Choose a gate posture (per-call `senderIsOwner` recommended).
4. Add `src/agents/tools/my-tool.test.ts`. Three enumeration tests typically need
   updating when a tool is added: the **registry**, **session-wiring**, and
   **owner-only** tests. (Tests that assert exact tool counts neutralize
   `COMPOSIO_API_KEY` — keep that pattern.)

### Add a channel
Implement the channel adapter contract (config / gateway / outbound / security /
status / message-action / secrets), register via `b.channel(...)` in a module,
lazy-load heavy deps, ship reconnect-with-backoff + crypto-error narrowing + JID
canonicalization, and pass dedupe + reply-sanitizer + abort-trigger tests.
WhatsApp (`src/agents/channels/whatsapp/`) is the reference implementation.

### Add a skill
Drop a directory under `skills/` (bundled) or `~/.brigade/skills/` (managed, via
`manage_skill`). Frontmatter needs `name` + `description` (the discovery hook), and
optional eligibility metadata (`requires-bins`, `requires-env`, `requires-config`,
OS). Don't lift a per-cwd walker.

### Add an extension provider / model provider / web search
Create `src/agents/extensions/modules/<name>.ts` and register against the right
`b.*` slot from `src/extension-sdk.ts`. Web-search modules carry an
`autoDetectOrder` and an `isConfigured(cfg, env)` predicate.

### Add a CLI subcommand
Add a file under `src/cli/commands/` and register it in
`src/cli/program/build-program.ts`. Update `brigade doctor` checks if relevant.

---

## Storage modes (filesystem vs. Convex)

Brigade has a dual-mode storage seam (`src/storage/`): a `BrigadeStore` interface
with ~16 typed sub-stores, implemented by `local/` (filesystem, the default) and
`convex/` (optional). The mode is resolved at boot from a sticky sentinel and
freezes for the process. Toggle with `brigade store mode set <filesystem|convex>`;
copy data with `brigade store migrate`.

When touching storage, keep both backends in parity and never assume the path is
filesystem-shaped.

### Convex local dev loop (fully self-hosted — no cloud account)

- `npm run convex:install` — downloads the standalone `convex-local-backend` Rust
  binary + dashboard into `bin/` (gitignored). License FSL-1.1-Apache-2.0.
- `npm run convex:dev` — installs (no-op if cached), then starts the backend
  (`http://127.0.0.1:3210`), site proxy (`:3211`), and dashboard (`:6791`). It also
  writes `.env.local` (gitignored) with the self-hosted URL + admin key.
- `npm run convex:codegen` — regenerates `convex/_generated/` against the running
  local backend.

Per-machine state lives under `.convex-data/` (gitignored): `identity.json`,
`admin-key.txt`, the SQLite engine file, File Storage, and logs. `npx convex dev`
is only safe when the self-hosted env vars from `.env.local` are active; without
them it would try to claim a cloud project — don't run it in that state.

---

## Architecture invariants

- **Auth files** live at `<agentDir>/agent/{auth-profiles,models}.json`, mode 0600.
- **Sessions** are pi JSONL transcripts at `<agentDir>/sessions/<sessionId>.jsonl`,
  one file per session, indexed by `sessions.json`. They have a write-lock and
  transcript-repair on crash.
- **Never overwrite `session.agent.streamFn`** — `createAgentSession` installs an
  auth-aware wrapper; replacing it silently breaks all model calls.
- **Persona pin clobbers pi's skill injection** — Brigade renders skills into the
  assembled prompt itself (`applyPersonaOverrideToSession` is latched once per
  process). Don't revert to pi auto-injection.
- **`thinkingLevel` must be reasoning-aware** — some models reject `"off"`; derive
  it from `model.reasoning`.
- **Heartbeat** is workspace-driven via `HEARTBEAT.md`; strip the `HEARTBEAT_OK`
  token from output before delivery.
- **Sub-agent depth** is encoded in the session key; leaf agents (at max depth)
  lose the spawn tools entirely, and abort cascades to descendants.

---

## Proactive checks when touching subsystems

- `core/server.ts` / gateway → verify thinking-persist, hot-reload, guard-sweep,
  model-set tests are green.
- `agents/channels/` → the adapter contract honoured; WhatsApp is the
  reference; lazy-load discipline preserved.
- `cron/` → `--cron` paired with an IANA `--tz`; isolated runs stay inside
  `~/.brigade/cron/runs/`.
- `agents/subagent-*` → abort cascade + completion ordering + wake-on-settle green.
- `agents/tools/registry.ts` → pi built-ins intact (`read`/`write`/`edit`/`bash`/
  `grep`/`find`/`ls`); gate posture documented in the tool's leading comment.
- `agents/memory/` → origin threading preserved; dedup same-origin only;
  auto-recall filters before inject.
- `system-prompt/` → assembler keeps the canonical sections and the persona pin.

---

## Commit & release policy

- Use [Conventional Commits](https://www.conventionalcommits.org/). `feat` / `fix`
  / `perf` / `deps` / `revert` trigger a release; `docs` / `refactor` / `test` /
  `ci` / `chore` do not.
- Commit messages explain *why*, not *what*. No `Co-Authored-By: Claude` trailer.
- Releases are automated via release-please → npm publish (`@spinabot/brigade`).
  See [docs/RELEASING.md](docs/RELEASING.md).
