# AGENTS.md

`e2e` — an agentic end-to-end testing framework. pnpm monorepo, ESM only,
TypeScript 7.

## Contracts

There is no separate spec. The code is the contract, pinned in three places:

- The emitted `packages/e2e/dist/index.d.ts` (and `dist/engine/index.d.ts`,
  `dist/runner.d.ts`, `dist/reporters.d.ts`, `dist/oauth/*.d.ts`), and `@e2e-dev/core`'s
  `packages/core/dist/core/*.d.ts` and `dist/engine/index.d.ts`,
  are the public API. `packages/e2e/tests/types/sdk-types.ts` holds compile-time
  assertions (`@ts-expect-error` lines) for the parts that are easy to loosen
  by accident; it runs under the package `typecheck`, never under vitest.
- Wire formats live in `packages/e2e/schema/*.schema.json` (report-1,
  session-1, agent-judgment-2, the engine protocol's engine-manifest-1,
  `e2e doctor`'s doctor-1, the scheduler's advisory timings-1, and the deprecated agent-judgment-1) with a valid and an invalid fixture
  each. Integration tests validate every generated report and session envelope
  against them; `tests/unit/schema-fixtures.test.ts` checks the fixtures. A
  wire change edits the schema, both fixtures, and the producer in one review.
- Security invariants are the list under Gotchas below, enforced by tests in
  `tests/integration/agent-policy.test.ts` and the secret-ledger unit tests.
- Behavior changes update the matching `docs/**/*.mdx` page in the same
  change, including "not implemented yet" callouts, and `skills/e2e/` when the
  changed surface is described there. `scripts/check-error-codes.ts` (in
  `pnpm check`) fails when an error code in source is missing from
  `reference/errors.mdx` or `reference/engine.mdx`, or documented but raised
  nowhere.

There are no RFCs or design documents in the repo. The why lives in PR
descriptions and commit bodies; `git log` and `gh pr view` are the archive.
## Layout

`packages/` holds what publishes to npm; `crates/` holds every Rust crate,
one Cargo workspace with one `Cargo.lock` and one `rust-toolchain.toml` at
the root (sources only: `scripts/native/`, which takes an addon from
`scripts/native/addons.ts`, builds each addon into its npm package);
`apps/` holds the private apps and suites that consume the built packages
the way a user would.

- `packages/core` — the published `@e2e-dev/core` package, which `e2e` is built
  on and depends on at its exact version (a changesets `fixed` group keeps
  the two versions equal): the engine contract (`@e2e-dev/core/engine`, and
  `src/engine/protocol/`), locators (`src/locator/`), the agent
  (`src/agent/`, the `act` executor socket plus the judgment methods),
  the replay cache (`src/cache/`), secrets, and the session half of a
  worker: `run/engine-sessions.ts` (engine init and dispose, each attempt's
  session from launch to close, which the runner's `TargetExecutor`
  extends), `run/standalone.ts` (the worker an `@e2e-dev/core` host, a runner
  host, or MCP keeps alive, with a `WorkerPolicy` per kind), and
  `run/standalone-attempt.ts` (one attempt: reservation, launch, fixtures,
  deadline, close). `src/core/` is its own surface: `launch` opens a
  `core` attempt (no attempt published to `globalThis`, no trace, no session
  deadline), `SessionState` the `session-state-1` export, and `createAgent`
  (`@e2e-dev/core/agent`) the agent with a per-`cacheKey` replay cache settled
  at session close. A host shares its static secrets with every session in
  the process while it is open (`run/secrecy.ts`), and inside a test the
  running attempt takes charge of the host and its sessions, records their
  steps, and keeps their video (`run/guest-steps.ts`), both through
  `globalThis`, so they hold between two installed copies of the package. It
  imports
  nothing of `e2e`:
  `tests/unit/package-imports.test.ts` in `packages/e2e` fails on a
  dependency `@e2e-dev/core`'s manifest does not declare. `e2e` reaches its
  modules as `@e2e-dev/core/lib/<path>` (`./lib/*` in its exports), which is
  not public API; `@e2e-dev/core`'s behavior is tested by `packages/e2e`'s
  suites, through those paths and through the runner.
- `packages/e2e` — the published `e2e` package: SDK surface, runner, CLI,
  and `e2e/engine` and `e2e/agent`, which re-export `@e2e-dev/core`'s. A
  config's reporters and test filters resolve in `config/resolve-run.ts`
  over `@e2e-dev/core`'s `resolveProjectConfig`, and their types live in
  `src/run-types.ts`. Core knows the contract and never an engine's
  internals: no engine package is imported from `src/` (grep for
  `from '@e2e-dev/` and `import('@e2e-dev/`; the presets below are the only
  hits). Engine words still appear as platform labels, capability names, and in
  error text that names a factory, such as `config/targets.ts` telling you to
  call `web()`; no path through them reaches engine code. The one exception is the
  `e2e init` scaffold presets in `src/cli/init/engines.ts`, which write the
  user's config and so name engine packages as text; the package build records
  the sibling packages' versions in `dist/cli/init/sibling-versions.json` for the
  ranges they write. Each preset owns its prompt label, dependencies, config,
  example, and run command; interactive choices derive from this list. These
  presets never import engine implementations.
  - `src/run/` runner core (scheduler, units, workers, retries, sessions;
    `standalone-kinds.ts` the hosted and one-shot kinds of `@e2e-dev/core`'s
    standalone worker, `host-trace.ts` a hosted attempt's `trace.md`, and
    `select-target.ts` the target a session names, shared with MCP;
    `open-session.ts` exposes `openHost` on `e2e/runner` for another test
    runner: worker-lifetime provisioning, app processes, and engine init,
    then `host.openSession({ name })` for each test's fixtures, deadline,
    steps, artifacts, and trace at close. Only one hosted attempt may be
    opening, live, or closing per process; close it before opening another),
    `src/collect/` registration+selection, `src/session-tools/` the shared session tool catalog and handlers,
    `src/mcp/` the `e2e mcp` server (a live session that rides
    the `act` socket with a queue executor so every MCP call is a harness
    action; in a directory with no config, `open_session {engine}` names the
    engine as a package, whose default export is called, or as a factory
    call, a package with an export and options that may hold further such
    calls, which `mcp/default-engine.ts` resolves in the project, beside e2e,
    or in `~/.e2e/engines`, never by a specifier written in core), `src/oauth/` subscription sign-in (the `e2e login`, `logout`,
    and `models` commands and the `e2e/oauth/*` model constructors; each
    constructor subpath is the place its `@ai-sdk/*` optional peers are
    imported, and the Copilot constructor loads `@ai-sdk/openai` lazily, only
    for the Responses models, so the CLI boots without any of them). The
    constructors and the CLI
    are the whole public surface: the flows, stores, and fetch behind them
    are module-private, not a library for other products. `tests/live/` holds hand-run
    checks that need a stored login and are never part of `pnpm test`.
- `packages/web` — the published `@e2e-dev/web` package: the
  browser engine, built with the public `defineEngine`, contributing the
  `browser` fixture and `expect(browser)`. `@e2e-dev/web/engine` (and
  `@e2e-dev/mobile/engine`) export the factory and types without `test`, so
  `@e2e-dev/core` programs never import `e2e`'s main entry. It depends on
  `@e2e-dev/core` (peer), never the reverse, and on `e2e` as an optional peer
  that only the main entry loads; a target names it explicitly as
  `engine: web()`. There is no default engine and no well-known id registry
  in core. It imports from `@e2e-dev/core/engine` only: the semantics every
  engine must reproduce (error taxonomy, text and URL matching, assertion
  polling, JSON-value rules) are exported there, and an engine never imports
  `@e2e-dev/core/lib/*`.
- `packages/mobile` — the published `@e2e-dev/mobile` package: the
  iOS/Android engine on agent-device, built with the same public
  `defineEngine`, contributing the `device` fixture. Like the web engine it
  depends on `@e2e-dev/core` (peer) and optionally `e2e`, never the reverse; the
  engine implementation imports from `@e2e-dev/core/engine` only, and a target
  names it as `engine: mobile()`.
  The `@e2e-dev/mobile/tools` subpath holds the agent-side `open_app`, `swipe`,
  and `alert` tools; focused-field typing uses the engine's keyboard grammar.
  The main entry never loads the AI SDK.
  `unstable_deviceSession()` on `./tools` gives custom tools the running
  attempt's raw driver session, like `device.unstable_raw`. The client is typed as
  `DeviceSessionClient`, exported from the main entry.
  The `@e2e-dev/mobile/lease` subpath holds the agent-device lease plumbing
  device-cloud providers (`testmu`, `browserstack`, `revyl`) share: one
  daemon per slot, heartbeat, a release that fails unless the session end is
  confirmed, and `agentDevicePlugin()`, which checks a provider plugin's
  version and registers it in the daemon's home. Its `installLeasedApp()`
  installs a target's `app.appPath` through any lease's daemon; `eas` uses
  it too.
- `packages/desktop` - the published `@e2e-dev/desktop` package: the
  desktop engine (native apps through the OS accessibility tree), built with
  the same public `defineEngine`, contributing the `desktop` fixture. It
  imports from `@e2e-dev/core/engine` only, and a target names it as
  `engine: desktop()`. The engine drives macOS through its own Rust driver,
  `crates/e2e-desktop-napi` (a NAPI-RS crate), loaded into the worker's process and called
  directly (`src/driver.ts`): no CLI process and no JSON-RPC. Every native
  call that talks to another process runs on a blocking thread and resolves
  with an envelope that says whether input reached the app; `call` bounds it
  by the operation's budget and translates it. Unit tests drive
  `DesktopSurface` with a scripted driver (`tests/helpers/fake-driver.ts`)
  and run on any OS. The app it launches gets only a few variables of the
  run's environment (`INHERITED_ENV` in `src/launch-ownership.ts`): the driver
  launches through `open -n` with exactly that environment, since
  LaunchServices hands the app the environment of the process that asks.
  `pnpm --filter @e2e-dev/desktop build:native` (needs `rustup`) builds
  `packages/desktop/desktop.<platform>-<arch>.node`, which the loader takes in a
  checkout; a release ships it in `@e2e-dev/desktop-darwin-arm64` and
  `@e2e-dev/desktop-darwin-x64` (`packages/desktop/npm/<platform>`, where
  every native addon's platform packages live), optional dependencies with `os`/`cpu` set,
  in a changesets `fixed` group with the engine, each with a
  `THIRD_PARTY_LICENSES.md` of the crates the addon links. After a change under
  `crates/`, run `cargo clippy --workspace` and `cargo fmt --all --check` at the root, rebuild, and
  run the desktop testbed; after a dependency change, also
  `pnpm --filter @e2e-dev/desktop licenses:native`, which CI checks. A prototype that runs on macOS only: `prepare`
  and `init` refuse any other OS.
- `packages/electron` - the published `@e2e-dev/electron` package: the
  Electron engine, contributing the `electron` fixture, and the reference
  for an engine built outside this repository (ENG-892): it imports
  `@e2e-dev/core/engine` and nothing else at run time: it starts the binary
  and speaks the DevTools protocol itself (`src/cdp/`, typed by
  `devtools-protocol`), never another engine or an automation library. What it needs from core becomes public
  contract (`expressionSelectors` came from it); `docs/engines.mdx` lists the
  assumptions it broke. `app.open()` launches the project's `electron`
  package on `app.appPath` (or `executablePath`) with a private
  `--user-data-dir` per attempt; `prepare` downloads the Electron binary,
  since Electron 45 has no install script. Reads join
  `Accessibility.getFullAXTree` and one `DOMSnapshot` on backend node ids
  (`src/tree.ts`, pure, tested on a captured read); actions run in an
  isolated world and send trusted input; the page-side code is typed
  functions in `src/in-page/`, sent as source text (`toString()`) and tested
  in Chromium (`tests/integration/`). Windows are the tabs. Screenshots
  mask password fields and nested documents, and are withheld when the DOM
  snapshot finds one inside a closed shadow root, which no mask reaches
  (`unmaskableCount`, independent of the accessibility tree). The app gets
  only a few variables of the run's environment (`INHERITED_ENV` in
  `src/app-process.ts`) and `electron({ env })`. A window that shows a local
  file outside the app's directory is not observed, traced, or captured
  (`src/file-bound.ts`): an Electron target has no `app.url` for core's
  file-app bound to key on.
- `packages/core/src/engine/protocol/` - the engine protocol: the engine
  contract as LSP-style JSON-RPC (`connectEngine` client, `serveEngine`
  server, spawn/socket/loopback transports), so an engine can run in
  another process, machine, or language. The harness holds only protocol
  clients (`ResolvedTarget.engine` is an `EngineClientHandle`); a
  `defineEngine` handle is served over `loopbackTransport`, so a contract
  change that cannot cross the wire fails in every suite.
- `packages/kernel` - the published `@e2e-dev/kernel` package: Kernel hosted
  browsers for the web engine. An official integration with a hosted service
  is one package per service, named after it (`@e2e-dev/<service>`), with the
  vendor SDK and the engine it plugs into as peers. It implements that
  engine's provider seam (`BrowserProvider` for web, `DeviceProvider` for
  mobile) and imports the engine's types only; the engines never know it
  exists. A service with providers for both engines ships them in that one
  package, each engine an optional peer and each provider on its own entry
  that never imports the other engine (`@e2e-dev/testmu` and
  `@e2e-dev/testmu/web`).
  Its docs page under `docs/integrations/` ships with the vendor's logo on
  its overview card (`authoring-docs`, "Vendor logos");
  `scripts/check-docs-logos.ts` fails `pnpm docs:check` without it.
- `packages/notte` - the published `@e2e-dev/notte` package: Notte cloud
  browsers for the web engine, `attempt` scope only, with a marker-file
  ledger for `sweep` since sessions carry no tags. Maintained by Notte.
- `packages/browser-run` - the published `@e2e-dev/browser-run` package:
  Cloudflare Browser Run hosted Chromium for the web engine
  (`BrowserProvider`). It reads `CLOUDFLARE_ACCOUNT_ID` and
  `CLOUDFLARE_API_TOKEN` from the run's environment when it acquires a
  browser, so importing a config needs no login. One session per worker slot
  by default, or a fresh browser per attempt with `scope: 'attempt'`; the CDP
  endpoint is built from the account and session id rather than taken from the
  response, so a response cannot send the token to another origin. Each
  session is journaled by id under the OS temp directory, and `sweep` deletes
  what a killed worker left open.
- `packages/lightpanda` - the published `@e2e-dev/lightpanda` package: a
  `BrowserProvider` that starts a local `lightpanda serve` per worker slot
  and stops it with the run; no vendor SDK, the binary is the dependency.
- `packages/moli` - the published `@e2e-dev/moli` package: a `BrowserProvider`
  that runs a local Moli browser for the web engine, one `moli serve` process
  on an available loopback port per worker slot, stopped when the lease is
  released. The binary is `binary` when given, else `MOLI_PATH`, then `PATH`,
  then `~/.local/bin/moli`, resolved when a browser is acquired, so importing
  a config starts nothing; no vendor SDK, the binary is the dependency.
  On-demand layout and screenshots (`--layout`) and optional resource fetching
  (`--resource`) are on by default, and `args` passes further `moli serve`
  flags. Worker scope only.
- `packages/eas` - the published `@e2e-dev/eas` package: Expo Simulators
  hosted iOS simulators and Android emulators for the mobile engine
  (`DeviceProvider`). Expo publishes no SDK for the sessions API, so it calls
  Expo's GraphQL API with `fetch`, and `@e2e-dev/mobile` is its only peer.
- `packages/smol` - the published `@e2e-dev/smol` package: Chromium in
  smol machines microVMs on the runner's own computer for the web engine
  (`BrowserProvider`), through the `smolmachines` SDK's embedded engine
  (peer). Each worker slot boots one warm browser machine from the pinned
  Playwright Ubuntu image; a Node TCP relay exposes DevTools, and SDK agent
  readiness allows machine startup without waiting for published ports. In
  `attempt` scope every attempt runs in a copy-on-write branch. With `app`,
  the app under test runs in the same machine, so a branch also copies its
  running app and data on the machine. When maintaining this integration,
  update the provider's SDK dev dependency to a published version and raise
  its peer minimum only if the provider needs new SDK behavior. Keep the
  Playwright image and Chromium version in sync with `@e2e-dev/web`. Run
  `pnpm --filter @e2e-dev/smol test:unit` and `pnpm check`, then verify live
  machines in both attempt and worker scopes with an app running in the VM.
- `packages/limrun` — the Limrun hosted mobile device provider. Each worker
  leases one remote device, installs its app, and releases the device at exit.
- `packages/decision` — the published `@e2e-dev/decision` package: a
  `StepExecutor` (`decisionExecutor()`) that drives `agent.act` and
  `agent.assert` through an AI SDK *decision* model answering `choice`
  questions with probability distributions, plus an optional small language
  model that writes field values when the decision model picks `type`.
  `minProbability` and `minConfidence` gate a chosen operation, target,
  secret, or assertion verdict. It also exports `decisionFilter()`, a
  `TestFilter` that asks a decision model whether the pull request's diff
  can affect each test, packing test files into calls under the model's
  size limit, 8 calls at a time, and leaves out the unlikely ones. It runs
  every test on an `e2e.config` or lockfile change, and asks nothing about a
  test whose test file, setup file, or stored screenshots changed. It scores
  each test it keeps through `relevance` (1 for a touched test, the model's
  probability for a judged one, 0.5 for one it did not judge), and the
  runner starts each target's likeliest files first. A failed
  call leaves its tests in and the rest are still judged; after 3 failed
  calls it stops asking. When every call fails, or git or a file read
  fails, it throws, and the run warns and runs every test, the touched
  ones first, since the error carries their scores in `relevance`.
- `packages/acp` — the published `@e2e-dev/acp` package: a `StepExecutor`
  (`acp()`, with `claudeCode()` and `codex()` presets) that runs
  `agent.act` and `agent.assert` on a coding agent over the Agent Client
  Protocol, answers `agent.waitFor` and `agent.extract` in a second,
  tool-less session (`answer`), and takes `e2e explore`'s rules and
  `report_finding` through `extend`. The step tools (`createGrammarTools`, `createVerdictTool` from
  `e2e/agent`) reach the agent as an MCP server on 127.0.0.1; permission
  requests for anything else are rejected, and a tool of the agent's own
  that runs without asking fails the step with `POLICY_DENIED`.
- `packages/github` — the published `@e2e-dev/github` package: the reporter
  that posts the run as one pull request comment from GitHub Actions and
  keeps it current on reruns, writing the same text to the job summary. It
  reads the token, event, and repository when the run finishes, never at
  config load, and renders the page with `renderMarkdownReport` from `e2e`.
- `packages/html-reporter` — the published `@e2e-dev/html-reporter`
  package: `htmlReporter()` writes the run as one self-contained page,
  `<output>/report.html`. The page is a React app (`app/`) that Vite builds
  into one HTML file with everything inlined; the reporter embeds the
  report-1 document in it and links artifacts from `results/` by relative
  path, so it opens from `file://`. Its styles are a copy of the e2e-site
  design system's tokens, with OFL fonts in place of Cassette, which the
  site's license does not let us ship.
- `packages/testmu` — the published `@e2e-dev/testmu` package: TestMu AI
  (formerly LambdaTest) hosted Android emulators, iOS simulators, and real
  devices for the mobile engine (`DeviceProvider`), through agent-device's
  `@agent-device/testmu` plugin, and hosted Chrome and Edge for the web
  engine (`BrowserProvider`) from `@e2e-dev/testmu/web`.
- `packages/revyl` - the published `@e2e-dev/revyl` package: Revyl hosted
  iOS simulators and Android emulators for the mobile engine
  (`DeviceProvider`), through agent-device's `@agent-device/revyl` plugin.
  Revyl installs the build from an `https` `app` URL when it starts each
  device. `revylBrowsers()` from `@e2e-dev/revyl/web` (`BrowserProvider`,
  attempt scope only) starts a Revyl web session per attempt and leases the
  single-use CDP URL Revyl mints for it. Verify a change against live Revyl
  sessions with `REVYL_API_KEY` set.
- `packages/browserstack` — the published `@e2e-dev/browserstack` package:
  BrowserStack App Automate real Android and iOS devices for the mobile
  engine (`DeviceProvider`), through agent-device's built-in `browserstack`
  provider. An `https` `app` is uploaded once per run through the App
  Automate API, since the session's `app` capability takes only `bs://` ids.
- `packages/e2b` — the published `@e2e-dev/e2b` package: E2B sandboxes for
  both engines, through the `e2b` SDK (peer). Every sandbox refuses public
  traffic; a loopback tunnel on the runner (`src/tunnel.ts`) adds E2B's
  traffic access token, and a lease names only that tunnel, so no lease
  carries that token. `e2b()` (`DeviceProvider`) boots one `android-16`
  sandbox per worker slot, installs the engine's agent-device there behind
  `agent-device proxy`, and installs the target's `.apk` through that proxy
  with the agent-device client (pinned like `@e2e-dev/mobile`'s); the lease's
  `daemon` is the tunnel, so the runner needs no `adb`. `e2bBrowsers()` from
  `@e2e-dev/e2b/web` (`BrowserProvider`) starts Chromium on a sandbox's
  loopback and creates the sandbox with `maskRequestHost`, so E2B's edge
  rewrites `Host` to `localhost` and DevTools accepts the request. Keep the
  Playwright image in `docs/examples/web/e2b-template.ts` in sync with
  `@e2e-dev/web`. Run
  `pnpm --filter @e2e-dev/e2b test`, then verify live sandboxes on both
  engines, web in both scopes, with `E2B_API_KEY` set.
- `apps/testbed` (`@e2e-dev/testbed`, private) — dogfood project that
  consumes the **built** packages like a real user would: the playground app
  where every runner feature (sessions, routes, downloads, frames, uploads,
  serial groups, the executor seams, verdict edge cases, the reporter under
  stress, `explore`) has a deterministic test. Hard UI surfaces belong to the
  benchmarks, not here.
- `apps/web-benchmark` (`@e2e-dev/web-benchmark`, private) — a Next.js app of
  self-contained hard-surface scenarios (shadow DOM, canvas, iframes, native
  dialogs, planted bugs) at `/e/<slug>`, copied from the e2e-inc web
  benchmark, plus the e2e suites written against them (`tests/` and
  `tests-agent/` both gate PRs; the agentic one runs from its committed
  recordings, see "Committed recordings" under Gotchas). Scenario files are
  copies: keep diffs against the source minimal so scenarios port both ways,
  and never fix a planted bug. The one exception is Control Inventory, ours
  like the mobile benchmark's: plain controls, one exercise per agent verb the
  hard scenarios never reach, with one agentic test per verb in
  `tests-agent/control-inventory.e2e.ts`.
- `apps/mobile-benchmark` (`@e2e-dev/mobile-benchmark`, private) — an Expo
  app of hard mobile surfaces (merged or hidden accessibility trees, native
  alerts over modals, keyboard-covered submits, virtualized lists, a WebView,
  OS permission and payment sheets), copied from the e2e-inc mobile
  benchmark, plus the e2e suites on the `@e2e-dev/mobile` engine
  (`tests/` locators only, `tests-agent/` one `agent.act` per scenario).
  Both suites run in CI on an iOS simulator and an Android emulator
  (`.github/workflows/mobile.yml`; the Expo build is cached per native
  fingerprint and its JS repacked on a hit); the agentic one replays
  committed recordings and calls the model for a step with none, see
  "Committed recordings" under Gotchas. Scenario files are copies: keep
  diffs against the source minimal, and name no company a scenario was
  distilled from.
- `apps/desktop-testbed` (`@e2e-dev/desktop-testbed`, private) - a native
  AppKit app (`app/macos/main.swift`, built by `pnpm build:app` into
  `build/SignInForm.app`): a sign-in form, and a Controls window with one
  control per engine capability the form does not reach. Its e2e suites on
  `@e2e-dev/desktop`: `tests/` locators only, `tests-physical/` the physical
  pointer and keyboard (`pnpm test:physical`, which moves your pointer), and
  `tests-agent/` one `agent.act`. Hand-run on a Mac with Accessibility
  permission and the native driver built; no CI job runs it yet.
- `apps/electron-testbed` (`@e2e-dev/electron-testbed`, private) - a small
  Electron app (`app/`: context isolation, a preload bridge, IPC, a second
  window, a closed-shadow password field) and the e2e suites on
  `@e2e-dev/electron` (`tests/` deterministic, `tests-agent/` with a model).
  Its windows stay hidden unless `E2E_ELECTRON_HEADED=1`. The `electron`
  job in `spec.yml` runs it under xvfb, after the package's integration tests
  (`pnpm test:electron-testbed` by hand).
- `examples/` — standalone user-facing projects, one per technology
  (`with-vite`, `with-next`, `with-astro`, `with-angular`, `with-expo`, `with-swiftui`,
  `with-compose`, `with-kotlin-multiplatform`, `with-flutter`, `with-maui`), each the same
  one-screen greeter demo with deterministic and agent tests. They install
  the published packages from npm, sit outside the pnpm workspace, commit no
  lockfile, and gate no pull request; oxlint and fallow ignore them.
  `.github/workflows/examples.yml` runs every one nightly
  (23:00 Europe/Warsaw) on each platform it supports, with the packages
  packed from main swapped in for the npm ones, agent tests included, and
  posts one Slack message for the run (`scripts/examples-nightly/`, the
  `SLACK_EXAMPLES_NIGHTLY_WEBHOOK_URL` secret). A new example or platform
  gets a matrix entry there. It also needs an official entry in
  `examples/examples.json` (the list e2e.com/examples renders,
  partner and community repositories included) and a preset in
  `packages/e2e/src/cli/init/examples.ts`; `pnpm check:examples` fails
  without either. A change still runs the example's suite by hand and updates the
  "Last checked" line in its README. A native, Flutter, or .NET MAUI example (SwiftUI, Compose, Kotlin
  Multiplatform, Flutter, .NET MAUI) keeps its tests in an `e2e/` folder
  beside the native project, as a user would.
- `docs/` (the docs pages: the `.mdx` files under `docs/`, navigation,
  redirects, and the page menu in `docs/docs.json`, the images under
  `docs/images/`; `docs/examples/` is typechecked and shown
  verbatim on docs pages and in `skills/e2e/` (`docs/examples/skill/`), kept
  in sync by `scripts/check-docs-examples.ts`; a shell
  block that runs `npx` or `npm install`/`ci` sits in a `<CodeGroup>` of
  `npm`, `pnpm`, and `bun` blocks, which the site syncs site-wide, enforced
  by `scripts/check-docs-package-managers.ts`).
  `docs/ja/`, `docs/zh/`, `docs/cs/`, `docs/es/`, `docs/pt/`, `docs/hi/`,
  `docs/fr/`, `docs/pl/`, and `docs/id/` hold the Japanese, Simplified Chinese,
  Czech, Spanish, Brazilian Portuguese, Hindi, French, Polish, and Indonesian
  translations, one page per English page at the same path, with the tab and
  group labels in `docs/<language>/navigation.json`. Translations are best
  effort: keep the English pages current in every change, and leave the
  translations to lag behind, since no contributor is expected to update a
  language they don't speak. `scripts/check-docs-translations.ts` warns on a
  stale outline, code block, or label. It fails on a translation whose English
  page is gone or that has no title, a language with no `navigation.json`, and
  a line that repeats the end of the line above it (`repeatedLines` in
  `scripts/docs-prose.ts`; `authoring-docs` "Translations").
  The `e2e` build copies the
  pages to `packages/e2e/docs/` (gitignored,
  `packages/e2e/scripts/prepare-build.ts`) so the published package ships
  them for agents to read offline.
- `skills/e2e/` — the agent skill for consumers: `SKILL.md` plus
  `references/<topic>.md`, one per `e2e guide` topic. It lives at the repo
  root because `npx skills add e2e-inc/e2e` only looks in well-known
  directories. The `e2e` build copies it to `packages/e2e/skills/`
  (gitignored) so the published package ships it; `src/cli/skill.ts` reads
  that copy first and the repo source as the fallback, and `e2e init` writes
  it into a project's `.agents/skills/` and `.claude/skills/`. `SKILL.md`
  opens with a table that routes each job to one reference, and every
  reference over 100 lines opens with a `## Contents` list of its sections
  (`tests/unit/skill.test.ts`).
  Every consumer skill under `skills/` is named in the root `skills.sh.json`
  group, which puts it at the top of the skills.sh page.
- `skills/create-verification-skill/`: a generator skill for consumers;
  it writes a project-local `verify-<app>` skill and feature map on top of
  e2e, with the bug bash wired to the map. Installed with `npx skills add
  e2e-inc/e2e --skill create-verification-skill`; not shipped in the
  package and not read by `e2e guide`. `references/example/` is the skill
  it generated and ran for `apps/testbed`: regenerate it when a playground
  route, label, or test it names changes.
- `skills/migrate-to-e2e/`: a consumer skill that ports a Playwright,
  Cypress, Selenium, Appium, Detox, Maestro, or TesterArmy suite one slice per session, the old
  suite running beside the new one, with a `MIGRATION.md` progress file the next
  session resumes from. It routes to `docs/migrate/<runner>.mdx` for the
  API mapping, so a mapping change edits the guide, not the skill. Installed
  with `npx skills add e2e-inc/e2e --skill migrate-to-e2e`; not shipped
  in the package and not read by `e2e guide`.
- `.dev/skills/` — the skills we use to work on this repo (`authoring-docs`,
  `babysit`, `merge-risk`, `ship-pr`, `verify`, `writing-pr`).
  `npx skills add e2e-inc/e2e` offers only `skills/*`: its default scan never looks in `.dev/`, and it skips
  `.claude/skills/<name>`, the relative symlink to each that agents load
  them through, because it does not follow symlinked directories. Its
  `--full-depth` scan does reach `.dev/skills/`; there the frontmatter's
  `metadata.internal: true` hides them. A new repo-only skill goes in
  `.dev/skills/` with both. On Windows the symlinks need Developer Mode and
  `core.symlinks=true` (CONTRIBUTING.md). The vendored third-party skills in `.claude/skills/` (`unbox-ai`,
  `unslop`, tracked by `skills-lock.json`) stay where they are: the CLI
  skips them as installed project skills. Each also carries
  `metadata.internal: true`, which keeps skills.sh from listing it on the
  e2e-inc/e2e page; `npx skills update` drops that line, so add it back.
- `plugins/e2e/` — one package of skills for Codex, Claude Code, Cursor, and
  Devin, and the e2e MCP server (`mcp.json`, `npx -y e2e@<version> mcp`) for
  all of them but Claude Code; Grok Build reads the Claude files. There is no
  `.mcp.json`: Claude Code loads one from a plugin's root without being told,
  and `pnpm plugins:check` fails when it appears. The root
  `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`, and
  `.cursor-plugin/marketplace.json` all point here. Edit skill Markdown in
  `skills/`, then run `pnpm plugins:sync`; `pnpm plugins:check` checks the
  generated copies, license, the Claude, Cursor, and Devin manifests (generated from
  Codex's), every manifest's `version`, and the version `mcp.json` pins, which is the
  runner's (`version-packages` syncs it, so plugin
  installs update once per release; it does the same for
  `packages/e2e/server.json`, the MCP Registry entry). The Codex manifest's other fields
  (its `mcpServers` path, `./mcp.json`, reaches the Cursor manifest too, and
  the sync drops it from Claude's), assets, README, and
  per-skill `agents/openai.yaml` are maintained in the plugin. Keep the
  package self-contained and leave the repository's development MCP
  configuration outside it. Example skills use `SKILL.example.md` so clients
  do not discover them as additional skills.
  GitHub Copilot reads the generated `plugin.json` and `mcp.json` at the plugin
  root (the Agent Plugins v1.0.0 format awesome-copilot's intake requires),
  ahead of `.claude-plugin/`; `plugin.json` cannot name MCP servers, so
  dropping `mcp.json` drops Copilot's server. The plugin's skill copies leave
  out `metadata.openclaw`, since that spec takes string metadata values only
  (ClawHub publishes from `skills/`), and a skill links no file outside its
  own directory.
  Devin reads the generated `.devin-plugin/plugin.json` (card fields and the
  server inline); its loader also reads the root `plugin.json` and MCP files,
  which declare the same `e2e` server. Its marketplace (CognitionAI/devin-marketplace) lists `plugins/e2e`
  pinned to one commit of this repository, so a plugin change reaches Devin
  users only after a pull request there bumps that `sha`.

## Commands

Build first — nearly everything downstream consumes `dist`.

```bash
pnpm check          # lint -> check:dead-code -> typecheck -> docs:check-errors -> check:peer-ranges -> check:changeset-bumps -> check:examples -> check:benchmark-coverage -> check:install-scripts -> plugins:check -> mcp-server:check -> docs:check (full gate)
pnpm test           # builds, then vitest unit + integration
pnpm test:testbed   # builds, then runs the real CLI against the playground app
pnpm test:web-benchmark   # builds, then runs the real CLI against the benchmark scenarios
```

Focused work:

```bash
pnpm --filter @e2e-dev/core run build && pnpm --filter e2e run build
pnpm --filter e2e run test:unit                       # unit only; needs @e2e-dev/core built
pnpm --filter e2e exec vitest run tests/unit/scheduler.test.ts
pnpm --filter e2e exec vitest run -t 'name fragment'
pnpm --filter @e2e-dev/web run test
pnpm --filter @e2e-dev/testbed run test:headed
```

- Package `test` scripts do **not** build. Root `build` and `test` order the
  packages explicitly rather than relying on topological sort, because `e2e`
  devDepends on the web engine for its browser-backed integration tests
  while the engine optionally peer-depends on `e2e` — pnpm reports that cycle
  on every install. `@e2e-dev/core` builds first: `e2e` and every engine compile
  against its `dist`.
- `pnpm typecheck` runs `build` first, then per-package `typecheck`. The
  package `typecheck` covers `tests/**`, which is what makes
  `tests/types/sdk-types.ts` a test.
- Integration tests need Chromium: `pnpm --filter @e2e-dev/web exec
  playwright-core install chromium`. The web engine's `prepare` hook
  also installs a missing browser once per run, in the runner, before `collected`
  is emitted and the run's clock starts.

## Definition of done

Work is done when a human can review it without redoing any of it: verified
against the built packages, reviewed in a fresh context, green, every bot
thread handled, and labeled `Ready for Human Review`. "It compiles" and
"tests pass" are not done.

- Prove behavior with the `verify` skill (`.dev/skills/verify`) while
  iterating and before the PR: the built CLI on the testbed or a benchmark,
  the `e2e` MCP server (`.mcp.json`), a scratch project for `init`, the docs
  site. If you cannot verify something, say so; never imply you did.
- The PR body is the source of truth for the change (`writing-pr` skill):
  `## What`, `## Why`, `## How it works` as numbered steps through the diff,
  then `## Verified`. It describes the head commit. After every push to a
  branch with an open PR, whatever the task was, run the `writing-pr`
  skill's "After every push to an open PR" steps. A push that changes how
  the PR works, its scope, or a measured number edits the body in the same
  step and captures stale evidence again. Run the `unslop` pass on the
  text you edit. A body and a diff that disagree are a review finding.
- `## Verified` states whether the change was run locally and carries the
  evidence: CLI output, a main-vs-branch table for fixes, the `pnpm bench:ab`
  table for a perf claim or a runner, agent, or engine change, a
  `pnpm record:terminal` recording when terminal output or UI changes, and
  the run's video for on-screen behavior.
- Open every PR through the `ship-pr` skill (`.dev/skills/ship-pr`):
  checks, verification, fresh-context self-review, the PR, then the
  `babysit` skill (`.dev/skills/babysit`) until the label is on. Asking
  for a PR means asking for all of that. A push, a merge conflict, a change
  request, or a move back to draft removes the label
  (`.github/workflows/review-label.yml`), so a labeled PR is always labeled
  for its current head.
- On a PR from a fork you cannot add the label. Comment exactly `/ready` as
  the PR's author once the gates in
  [CONTRIBUTING.md](./CONTRIBUTING.md#ready-for-human-review) hold: green,
  conflict-free, every review thread replied to and resolved. The workflow
  refuses it otherwise and lists what is open. Never resolve a thread just to
  pass: handle the feedback first.
- Never merge or approve.
- When a reviewer (human or bot) corrects the same thing twice, encode it:
  make it impossible in types or structure, else a lint rule or a test, else
  a skill line, in that order of preference.

## Non-obvious conventions

- **Relative imports carry the `.ts` extension** (`rewriteRelativeImportExtensions`).
  `import { x } from '../internal/ids.ts'` — not `.js`, not extensionless.
- `exactOptionalPropertyTypes` + `noUncheckedIndexedAccess` are on. Optional
  properties use the conditional-spread idiom; `oxc/no-map-spread` is disabled
  for exactly that reason.
- Lint is `oxlint` with `correctness`/`suspicious`/`perf` as errors and
  `style`/`pedantic` off. `no-await-in-loop` is intentionally off (sequential
  execution is the runner's contract).
- `pnpm check:dead-code` runs [fallow](https://github.com/fallow-rs/fallow)
  (`.fallowrc.json`): unused files, exports, dependencies, and duplicate
  export names fail CI. An export whose only consumer is a test is dead
  production API - make it module-private or move it. The class-member rule is
  advisory (`warn`) because it misses getters and callback-invoked methods.
- JSDoc on new functions; avoid inline comments unless they explain *why*.

## Testing quirks

- Vitest 5, `pool: 'forks'`, two projects. `integration` is capped at
  `maxWorkers: 3` and runs in a later group — do not raise it; CPU starvation
  produces timeouts indistinguishable from real failures.
- Integration tests write throwaway projects into
  `packages/e2e/tests/tmp-projects/` (gitignored) and import the runner from
  `dist/` via a non-literal specifier so the fixture's `e2e` self-reference
  shares one registry. Stale `dist` means confusing failures — rebuild.
- Testbed suites beyond the default one never gate a PR: `test:agent` /
  `test:dogfood` (real model calls, need `AI_GATEWAY_API_KEY`, optional
  `E2E_MODEL=provider/model-id`, the testbed's own override) run only on the weekly
  `.github/workflows/agent.yml` schedule or by manual dispatch. Both run
  against local deterministic apps, so a failure there is ours.
- The default testbed suite runs `decisionFilter` with Jev on a pull request
  (`apps/testbed/e2e.config.ts`, with `--changed-since` from `spec.yml`), so a
  PR's testbed check runs only the tests Jev rates the change can affect;
  without the key, every test runs, and when a call fails, the tests no call
  judged run. The merge queue and `main` pass no `--changed-since` and run
  every test, so the merge gate stays deterministic. Locally, every test runs
  unless you pass `--changed-since origin/main`.
- Agentic assertions must be model-portable: assert on meaning (`toContain`)
  and pair each agentic step with a deterministic locator check.

## Inspecting agent runs with unbox-ai

`e2e run --ai-trace` records every model call of a run to `.e2e/ai-trace.json`
in the AI SDK devtools database shape (`{ runs[], steps[] }`). One run per
agent step, named `<test title> · <api> "<label>"`; one entry per model round
trip (an `act` turn, a `waitFor` poll, a judgment repair round) with the exact
prompt, the tool definitions and their JSON schemas, the response, usage, model
latency, and provider metadata. Recorder: `src/internal/ai-trace.ts` (an AI SDK
`registerTelemetry` integration, attributed through an async-local scope set
in `run/execute.ts` and `run/steps.ts`; workers drain on `unit-done`).

Use [unbox-ai](https://github.com/e2e-inc/unbox-ai) to read it — never
`cat` or Read the file, it is megabytes of resent context. The skill in
`.claude/skills/unbox-ai/SKILL.md` has the full workflow and recipes (other
agents: `npx skills add e2e-inc/unbox-ai`). Start wide, then drill:

```bash
AI_GATEWAY_API_KEY=... pnpm --filter @e2e-dev/testbed test:agent -- --ai-trace --no-cache
npx unbox-ai runs apps/testbed/.e2e/ai-trace.json            # one line per agent step
npx unbox-ai summary apps/testbed/.e2e/ai-trace.json --run 3 # one step: turns, tokens, caching
npx unbox-ai tools apps/testbed/.e2e/ai-trace.json --run 3   # what the agent called, and how often
npx unbox-ai event apps/testbed/.e2e/ai-trace.json 2 --run 3 # one turn's new messages
npx unbox-ai compare apps/testbed/.e2e/ai-trace.json --run 3 --run 4 --trajectory
```

This is how to debug an agentic step: a wrong node id, a loop guard firing, a
prompt or tool description change, or where the tokens went. Reach for it
before changing prompts in `src/agent/`, and again after, with `compare`. In
integration tests, pass `runOptions: { aiTrace: true }` and read the file from
the fixture project (`tests/integration/agent-ai-trace.test.ts` shows how).

- Steps replayed from the replay cache make no model call and leave no run; use
  `--no-cache` when you want the whole flow traced.
- Cost shows as `-` in unbox-ai (the devtools shape carries none); the AI
  Gateway's `marketCost` is in each step's `output.providerMetadata`, and the
  `--debug` step table prints dollars.
- Live view while a suite runs: `npx unbox-ai devtools` in the project
  directory, then `E2E_DEVTOOLS=1 ... test:agent -- --workers 1` (the testbed
  agent config registers `@ai-sdk/devtools`; that recorder is one database
  per process, hence one worker). Prefer `--ai-trace` for anything to keep.
- "Trace" means three things here: the recorded actions the replay cache
  keeps (`trace-1` entries under `.e2e/cache/`), this AI trace, and the
  runner's trace page per test (`.e2e/results/<test>/trace.md`). Say
  which.

## Cross-checking the web engine's tree

`packages/web/tests/integration/crosscheck.test.ts` reads every node of the
web engine's semantic tree against two oracles on the same page: Chrome's
accessibility tree over CDP (role, name, checked, disabled, expanded,
selected, pressed, heading level, and interactive nodes the tree left out)
and Playwright's `getByRole(role, { name })` round trip, exact but tolerant of
icon-font glyphs the way the engine's role locator is. It runs on the
fixture pages in `tests/crosscheck/fixtures.ts` under `pnpm test`, and on
every web-benchmark scenario in `benchmark.yml` or locally:

```bash
pnpm --filter @e2e-dev/web-benchmark run build && pnpm --filter @e2e-dev/web-benchmark run start &
CROSSCHECK_BENCHMARK_URL=http://127.0.0.1:4280 pnpm --filter @e2e-dev/web exec vitest run tests/integration/crosscheck.test.ts
```

- Every disagreement must be listed in `tests/crosscheck/expected.txt` with a
  reason; a new one fails, and so does a listed one that stopped happening.
  `E2E_CROSSCHECK_UPDATE=1` rewrites the file keeping the reasons and marks
  new lines `TODO`, which fails until someone writes one. Review its diff: a
  removed line is a fix, an added one a change in what the model reads.
- Deliberate vocabulary choices (a `listitem` named from content, `box`, an
  editor host as `textbox`, Chrome's own role names) are policies at the top
  of `tests/crosscheck/crosscheck.ts`, each with its reason, not lines.
- A reader change (`src/in-page/read-semantics.ts`) runs it before the PR.
  A bug in that family starts as a fixture page line here.
- Pages load with Playwright's clock paused (`openCheckPage`), so a timer
  cannot replace a node between the engine's read and the oracles'. Content a
  timer reveals is never read: build fixture pages synchronously.
- `tests/integration/conformance.test.ts` holds the reader to a third
  oracle: the role and accessible-name expectations of the axe-core test
  suite (`tests/conformance/axe-core/`, vendored byte for byte through
  Playwright's copy, MPL-2.0). Its disagreements live in
  `tests/conformance/expected.txt` the same way, grouped by reason; a line
  that starts with `Bug:` is a fix waiting to be made, and the fix deletes it.
## Recording the terminal

`pnpm record:terminal` records a command in a real TTY as a video for the PR
body, at one size and font so recordings compare. It drives
[VHS](https://github.com/charmbracelet/vhs), which must be on `PATH`
(`brew install vhs`, or `nix shell nixpkgs#vhs -c pnpm record:terminal ...`).
Use it whenever a change alters what the terminal shows: CLI output, a
reporter, a prompt, watch or pause UI.

```bash
pnpm record:terminal --cwd apps/testbed --out /tmp/branch.gif -- node node_modules/e2e/dist/cli/bin.js run tests/todos.e2e.ts
pnpm record:terminal --cwd /tmp/e2e-main/apps/testbed --out /tmp/main.gif -- node node_modules/e2e/dist/cli/bin.js run tests/todos.e2e.ts
pnpm record:terminal --cwd apps/testbed --out /tmp/watch.gif --tape /tmp/watch.tape
```

The recording ends when the prompt returns, whatever the exit code. Several
arguments after `--` are a program and its arguments; one is a shell line
(`"a && b"`). A UI
that takes keys needs `--tape <file>` with the VHS commands to play (`Type`,
`Enter`, `Ctrl+C`, `Wait+Screen /regex/`, `Sleep`); the script owns the
output, shell, and size. `.gif` renders inside a markdown table, `.mp4` and
`.webm` as players at the end of the body. The options are in the header of
`scripts/record-terminal.ts`; the tape builder is tested in
`scripts/record-terminal/` (`pnpm test:scripts`).

## Measuring a change against main

`pnpm bench:ab` runs a benchmark suite through two builds, the merge base
with `origin/main` (a worktree under the system temp directory, installed and
built once per commit) and the working tree, in pairs in a seeded random
order, and prints a markdown table for the PR body. Use it for any perf claim
and before and after a change to the runner, the agent loop, or an engine:

```bash
pnpm bench:ab -- tests-agent/control-inventory.e2e.ts --config e2e.agent.config.ts
pnpm bench:ab --suite testbed --threshold 3 -- tests/forms.e2e.ts
```

Arguments after `--` go to `e2e run`; the options are in the header of
`scripts/bench-ab.ts`. What it reports, in order:

- Behavior. A test whose status, attempts, or step sequence (kind, api,
  label, status, error code, cache mode) differs between the builds, or
  between two runs of one build, is listed and left out of the timings. This
  is the regression check: a perf change that alters behavior is not a perf
  change.
- Timings: the whole suite, the observe, action, and model event phases, and
  every step api, each as the median paired change with a bootstrap 95%
  interval, `faster`, `slower`, or `same` against `±--threshold`, else
  `unresolved`. Sampling stops once the suite's interval resolves.
- Counters that should not move within one build: steps, events by kind,
  observed nodes and bytes, cache modes, model calls and tokens, run exit
  code. A change here is exact and needs no statistics.

Runs go with `CI=1`: committed recordings replay read-only, a step with none
calls the model. A load average above half the cores is warned about; shared
CI runners are too noisy for wall-time verdicts, so trust the behavior and
counter sections there. The harness's statistics have unit tests under
`scripts/bench-ab/` (`pnpm test:scripts`).
## Microbenchmarks

`pnpm microbench` measures small pure-JS functions (secret redaction,
locator resolution, mobile tree projection; the cases are in
`scripts/microbench/cases.mjs`) as instruction counts under Valgrind's
Cachegrind, so the result does not move with the machine's load. Valgrind
runs on Linux only; on macOS, `--tool time` runs the same cases on wall time
as a smoke check.

```bash
pnpm microbench --trials 10 --base-root .                      # repeatability: one build against itself
pnpm microbench --base-root /path/to/base/checkout             # base against this checkout
pnpm microbench --tool time --case redact                      # local smoke run, noisy
```

- Each trial runs a case in two fresh processes, N and 3N iterations, and
  keeps the difference: startup, loading, warmup, and compilation cancel.
  Cases and inputs come from this checkout, the code under test from each
  `--root`/`--base-root`, which must be built. Give both roots paths of the
  same length: a different length moved one case by a fixed 0.075% between
  builds of the same code, and the harness warns about it.
- The default mode, `jitless`, counts the interpreter only, regexps
  included; in CI, the trials of one commit spread at most 0.17% per case.
  `--mode jit` keeps V8's compilers under `--predictable`,
  `--single-threaded`, `--predictable-gc-schedule`, and fixed seeds, but V8
  still optimizes differently in some processes and its trials cluster up
  to 2% apart: use it to look at JIT behavior, not to compare. Every
  process runs with `--v8-pool-size=0`, and with ASLR off (`setarch -R`) on
  Linux. Counts are not wall time.
- A direction is reported only when the base and head trial ranges do not
  overlap and the change reaches the noise floor (`--threshold`, 0.5% for
  instruction counts). `--expect-same` (implied by one directory twice)
  makes the run a repeatability check, which exits 1 when any case's ranges
  separate, under the floor too.
- `.github/workflows/microbench.yml` runs both checks on a Blacksmith runner
  with one pinned Node version; dispatch it with a `base` ref to compare. On
  a pull request from this repository it posts the comparison and the
  repeatability result as one comment and edits it on every run; a fork's or
  Dependabot's pull request has the tables in the job summaries only. A
  measured regression never fails the job: read the comment.
- A case's `child.mjs` and `cases.mjs` are plain JavaScript: `--jitless`
  turns off WebAssembly, which Node's TypeScript stripping needs.

## Golden device trees

`packages/mobile/tests/fixtures/snapshots/{ios,android}/` holds raw
agent-device snapshots of the mobile benchmark's home list and every
scenario's first screen, captured from a real simulator and emulator, beside
the tree each one projects to (`<scenario>.tree.txt`: role, name, text,
value, states, test id, attributes, one node per line, no geometry).
`tests/unit/captured-snapshots.test.ts` projects them the way `observe` does
under `pnpm test`, so a change to `src/nodes.ts` shows up as a diff of the
trees, on both platforms, without a device.

- After a reader change, `E2E_GOLDEN_UPDATE=1 pnpm --filter @e2e-dev/mobile
  exec vitest run tests/unit/captured-snapshots.test.ts` rewrites the trees;
  the diff is what the model and the locators now read. Review it like code.
- Re-capture after an agent-device bump or an app change, with the current
  build installed (`pnpm ios` / `pnpm android` in the app), one platform at a
  time: `pnpm --filter @e2e-dev/mobile-benchmark run capture:snapshots
  --target ios-simulator` (or `android-emulator`), then update the trees. A
  bump that changes the snapshot shape is exactly what this catches.

## Gotchas

- Status prose drifts. `README.md` (the build copies it into `packages/e2e/`
  for npm) and the docs pages can claim things that have since landed or
  been removed (the located verbs and the locate cache are both gone, for
  example). Verify against `src/` before repeating or relying on any "not
  implemented yet" list — and fix the prose when you find it stale.
- Committed recordings. The two benchmarks commit their agentic suites' replay
  cache (`apps/web-benchmark/.e2e/cache/`,
  `apps/mobile-benchmark/.e2e/cache/`; their `.gitignore`s leave it
  tracked, the testbed's ignores its own, since fixture-app recordings are
  worth nothing to anyone). CI replays the entries read-only and calls the
  model for a step with no recording, so those suites gate a pull request at
  deterministic speed and cost. On a pull request they run for this
  repository's branches only, since a fork's has no key; the merge queue runs
  them, with the key, for every queued pull request the change reaches.
  Re-record with the package's `test:agent` and commit the changed entries in
  the same pull request as the scenario change.
  The web benchmark's agent job runs with `--strict-cache`, so a recording a
  change broke fails with `REPLAY_STALE` instead of quietly calling the model.
  That includes a change to the cache key (`REPLAY_POLICY_VERSION`, a new key
  field): strict lists the file store and fails a step whose
  key misses while an entry recorded for the same step sits under another key
  (`cache/rekeyed.ts`). Only entries whose `recordedFor` names the whole step
  (params digest, occurrence, agent) count; a lenient `read-write` replay
  completes an older one. Such a change re-records every entry and deletes the
  old ones in the same pull request. A step that was never recorded still runs
  live. A strict run replays on retries too and never writes or deletes an
  entry, whatever the mode.
  The web benchmark's entries are in. The mobile benchmark's iOS and Android
  entries are recorded on a Mac; Android replays with `--strict-cache`, iOS
  leniently.
- No implicit default model. For the built-in agent, the entry's `model`
  serves `act`; the judgment calls (`assert`, `waitFor`, `extract`) use its
  `judge` when one is configured, else `model`. A judgment never sees the
  prior-step ledger or the acting agent's summaries; it sees the instruction, its
  params, the agent's context, and the current screen with its location. Without a model, the first `agent` acquisition in a run
  reports one run-level `MODEL_UNAVAILABLE` and stops the run (exit 2). A
  custom executor handles `act` and `assert` through `runStep` and needs no
  model; its `waitFor` and `extract` use the built-in judgments on the
  agent's `judge` or `model`, else on the executor's own `answer`. No implicit target either: `targets` is required and
  each names its engine.
- Security invariants (fail closed when one cannot be enforced):
  - Secret values never reach model input, digests, logs, reports, or
    artifacts as text. Model input is the redacted location, the redacted semantic tree (as text
    or, on request, the redacted node tree), masked pixels only when masking
    is proven, and the sanitized prior-step records. Pixels mask secure
    fields only, before and after a secret fill: a value the app shows
    elsewhere is in the image, a documented limit (`docs/security.mdx`), not
    a gap to close with taint or text-matching heuristics. Text downloads are
    rewritten whenever the session's ledger holds a value
    (`redactsDownloads` in `run/secrecy.ts`), since a plain string reaches
    the app unseen. What an executor keeps in `attempt.memory` is its own;
    the harness never reports it.
  - Provider keys are a class of their own in the ledger
    (`registerProviderKey` in `run/secrecy.ts`): the closed list of model
    provider variables there, subscription tokens, a coding agent's saved
    login, and what an executor registers through `e2e/agent`. Every ledger
    redacts them from what the run writes and from model input, whole
    values only, text downloads included (an app can be given one). They
    never enter a ledger's own entries (so no saved session carries one), and never
    redact what a test id is made of, since the runner and a worker need
    not know the same keys. A new provider adds its variable to the list;
    a name pattern is not a substitute. Redact before any cut: half a
    value is no longer a match.
  - An agent's secret fill is authorized by the runner, not the model.
    `typeSecret` (`action-dispatcher.ts`) takes only a handle the step's
    params declare, the target resolves on the newest observation
    (`feed.resolve` and `requireLatest` in `observation-feed.ts`), and
    `authorizeSecretFill` (`secrets.ts`) requires the secret configured for
    the run, an enabled editable node, and a password field for a password.
    There is no origin check: the value goes to whatever site the page is on
    (`docs/reference/security.mdx`). The model never sees or picks the value.
    A test's own `fill(secret)` is trusted code and runs none of these checks.
  - Every model tool call is parsed into a closed schema and authorized
    immediately before dispatch. Nothing runs on a refusal: an unknown tool
    name, or an undeclared field on a built-in tool that declares fields,
    goes back to the model as the call's error result (the AI SDK's
    `tool-error`, naming the tool or the field), the next turn is the
    repair, and refusals count toward the failure-streak guard. A built-in
    tool with no fields drops extra keys and runs; the schema a provider
    receives still sets `additionalProperties: false`. A project tool keeps
    the schema given to `defineTool`. A node id not on the current screen is
    `LOCATOR_NOT_FOUND`, an action failure the model reads and re-aims from.
    `POLICY_DENIED` is for denied destinations, forbidden fills, and withheld
    pixels. Model text is never evaluated as code, selectors, shell, or
    config. The one exception is `e2e mcp`'s `run_code`, which runs a coding
    agent's JavaScript in the server's process with a test file's authority
    (`session-tools/run-code.ts`): that agent can already write a test and
    run it. The code can read every configured secret and credential (the
    config file, the environment, the app) and fill one into whatever field
    it likes. Its result passes the secret ledger, which replaces a secret's
    exact value only: that prevents accidents and is not a boundary. An
    accepted exception to the first invariant and to the fill rule above. On
    by default by design (maintainer decision): no flag or config gates it.
    App content, ledger text, and pixels are quoted as untrusted
    evidence with no policy authority.
  - Every navigation a test or the agent asks for (`app.open`,
    `browser.goto`, the `navigate` verb) goes through one rule,
    `resolveNavigationUrl`: only `http:`, `https:`, and the exact
    `about:blank` pass; every other scheme (`view-source:file:` included) and
    a malformed URL is `POLICY_DENIED` (a relative URL on a target with no
    `app.url` is `APP_URL_REQUIRED`). One exception: on a target whose
    `app.url` is itself a `file:` URL (one file, no host, never a directory),
    a `file:` URL passes for a file in that file's directory or below it,
    compared as decoded paths with symbolic links resolved, so neither an
    encoded separator nor a link climbs out, and never for a directory,
    whose listing links to its parent; a path that cannot be resolved is
    outside. The agent names navigation URLs and a page can tell it to, so
    anything wider would let a local page read any file the user can and
    carry it to an http(s) address. A link or a script in the local page
    can still take the browser anywhere a file page may go, which an
    http(s) page cannot, so `leftFileApp` holds the same bound over every
    sink that keeps or sends a screen on its own: an observation taken for
    a model (`checkObservedLocation` in `agent/observation-feed.ts` and
    `agent/invocation.ts`), the trace's step screens (`traceScreen`), and
    failure evidence (`run/failure-evidence.ts`). Out of the directory, the
    screen is withheld and only the location kept. A model is sent no
    pixels of a file app at all (`isFileApp` where `pixelsAllowed` is
    set and where `Invocation.observe` asks for pixels), since pixels can
    show a frame of another local file that no tree lists. For the same
    reason no automatic screenshot of a file app is kept: the two
    `captureEvidence` of `agent.assert` and the failure screenshot are
    second captures nothing places. A video the user turns on is not gated. A test's own reads are trusted and not gated. An engine opens a
    file app only when it declares `fileApps`, and the harness tells its
    `validateApp` with `fileApp: true`; the scheme is read once, in core
    (`namesFile`). The web engine refuses a provider and `connect` there,
    since the bound is checked against the runner's disk. `device.openLink` takes custom app
    schemes, so it refuses a list instead (`packages/mobile/src/links.ts`):
    `file:`, `data:`, `javascript:`, `view-source:`, `blob:`, `filesystem:`.
    There is no origin or host allowlist; PR #290 removed them on purpose, since a
    click reaches any origin a typed URL could.
  - Sessions are per-run, target-bound, AES-256-GCM encrypted with a
    memory-only key, and deleted at cleanup; payloads never enter diagnostics.
  - Reports escape contextually, strip terminal controls, generate artifact
    names, and never let a label become a path component.
  - Test, config, and engine code run with the runner's full OS authority;
    nothing here sandboxes them. Untrusted PR code belongs in an external
    sandbox with no secrets or write tokens. The merge queue runs a queued
    pull request's code with the repository's secrets, fork or not, so
    enqueueing (auto-merge included) is the trust decision: review a fork's
    test, config, and engine changes before you enqueue it.

- CI: `.github/workflows/spec.yml` runs lint, typecheck, and the testbed on
  Node 26, `pnpm test` on the newest Node 22, 24, and 26 and on the
  `engines.node` floors (22.22.3, 24.8.0), as two jobs per version
  (`test:runner` for core and e2e, `test:packages` for the rest), the CLI on Bun 1.4.3 and the
  latest Bun, `scripts/install-smoke.ts`, a fresh install of the packed
  packages with pnpm 11 and 12, and `native` on `blacksmith-6vcpu-macos-26`
  (the desktop driver's `cargo fmt --check`, clippy, and `cargo test`, a
  build for both Mac architectures with each one's architecture checked by
  `lipo`, a load of the arm64 build, also
  through the engine's loader test, and a load of the x64 build in the
  official darwin-x64 Node under Rosetta; rustup, when the image has none,
  comes from the rustup-init release and SHA-256 that
  `.github/actions/rust-toolchain` pins), which
  `spec gate` needs; `benchmark.yml` runs the
  web benchmark's two suites; `mobile.yml` runs the mobile benchmark's on an
  iOS simulator and an Android emulator (KVM on x64 Linux); `docs.yml`
  checks the docs. All four run on pull requests and in the merge queue
  (`merge_group`), which is the merge gate: auto-merge enqueues, and the
  queue merges only when every check is green on the queued tree. Each
  of the four ends in a `<workflow> gate` job, the only checks the `Main`
  ruleset requires (`spec gate`, `benchmark gate`, `mobile gate`, `docs
  gate`); it fails when any job it needs failed or was cancelled and passes
  over a skipped one, so a new job gates merges once it is in its gate's
  `needs`. The benchmark and docs workflows gate on paths: a `changes` job
  (dorny/paths-filter over `.github/filters.yml`) skips the suites when the
  change cannot reach them, and a manual dispatch always runs them. Never
  use a workflow-level `paths:` filter: the gate would never report and the
  merge would wait forever. A suite that cannot run (the agentic ones on a
  fork's or Dependabot's pull request, which get no model key) is skipped at
  the job level, never at the step level, so it boots no device for nothing.
  A push to main runs `spec` and the web benchmark; `mobile` only rebuilds
  the Expo app on a cache miss, since main's caches are the ones every pull
  request restores. A new build input or benchmark dependency goes into
  `filters.yml` in the same change. Every workflow
  pins actions by SHA; keep new actions SHA-pinned. Every job runs on
  Blacksmith, like the e2e-inc repos. Linux jobs use
  `blacksmith-4vcpu-ubuntu-2404` and macOS jobs `blacksmith-6vcpu-macos-26`;
  keep new jobs on those labels. The one exception is the `release` job:
  npm Trusted Publishing rejects OIDC tokens from self-hosted runners, and
  Blacksmith counts as one, so it stays on `ubuntu-latest`.
- Commits follow Conventional Commits; PRs are squash-merged with the number in
  the subject.
- PR titles and bodies follow the `writing-pr` skill
  (`.dev/skills/writing-pr/SKILL.md`). `unslop`
  (`.claude/skills/unslop/SKILL.md`, from `okwasniewski/dotfiles`) applies to
  any prose an agent writes here; other agents install it with
  `npx skills add okwasniewski/dotfiles --skill unslop`.
- Releases go through changesets: a user-visible change adds a `.changeset/`
  entry. On `0.x` the bump is `patch` for a feature or fix; never
  pick `minor` on your own. A breaking change is a `minor` with the summary
  opening `**Breaking:**`; a `minor` or `major` for a release the maintainer
  calls opens `**Release:**` (`scripts/check-changeset-bumps.ts`, `pnpm check`). Peer ranges point one way only (engine -> `@e2e-dev/core` and optionally `e2e`, integration ->
  engine) and read `>=<major.minor.patch> <major+1>`, the floor the oldest
  sibling the package works with. Raise it when a package starts relying on a
  newer sibling's export or contract field;
  `scripts/check-peer-ranges.ts` (`pnpm check`) fails on any other shape for
  every peer one package under `packages/` has on another (vendor SDK peers
  such as `@onkernel/sdk` are not checked). Narrow or exact, every runner minor (exact: every patch too)
  falls out of range, and changesets 3 then patch-bumps each engine and
  rewrites its pin, never a major (`determineDependents` in
  `@changesets/assemble-release-plan` patches an out-of-range peer dependent).
  That republishes every engine on every runner release, and a consumer who
  updates `e2e` alone is left with an exact peer npm 7+ refuses (ERESOLVE). A
  runner major is the one legitimate rewrite (`>=1.0.0 <2.0.0`, engines
  patched): `version-packages` runs `scripts/restore-peer-ranges.ts` after
  `changeset version`, which puts that in shape and leaves a wide range alone.
- The root `release` script publishes with no `--tag`, so versioned releases
  land on `latest`. `changeset publish` passes `--tag` through to the publish
  tool when given one, so `publishConfig.tag: "latest"` on every package is
  only a backstop for a hand-run `npm publish` (`pnpm publish` ignores it).
  Canaries pass `--tag canary` explicitly and never move `latest`.
  Do not switch to changesets pre mode to get a real prerelease version: a
  `0.16.0-beta.0` runner is outside the engine's `e2e` peer range, so
  changesets patch-bumps `@e2e-dev/web` and rewrites the peer to
  `>=0.16.0-beta.0 <0.16.0`, which no stable runner satisfies. Widening the range does not
  rescue it — node-semver only lets a prerelease satisfy a comparator set when a
  comparator with the same `major.minor.patch` carries a prerelease, so
  `0.3.0-beta.0` satisfies neither `>=0.1.0-0 <1` nor `*`. Never hand-edit a
  package `version` or `CHANGELOG.md`; `changesets/action` owns both.
- When you release (merge the `chore: version packages` pull request) and it
  publishes `e2e` or an `@e2e-dev/*` package an example depends on, update the
  examples once npm has the new versions, in a separate pull request from the
  release (#1838 is the pattern). Raise each `e2e` and `@e2e-dev/*` range in
  `examples/*/package.json` and `examples/*/e2e/package.json` to the newest
  version on npm (`npm view <pkg> version`); leave a package with no newer
  version alone. Run each changed example's suite by hand and update the "Last
  checked" line in its README for every example you ran. Where you have no
  simulator, emulator, or toolchain for one, install it, typecheck it, run
  `npx e2e list`, leave its "Last checked" line alone, and say so under
  `## Verified`. The examples commit no lockfile and gate no pull request, so
  nothing else catches one left on an old version.
- Canaries are hand-run, never from CI: `pnpm run canary` with `GITHUB_TOKEN`
  set versions and builds every public package as a changesets snapshot, and
  `pnpm run canary:publish` publishes them to the `canary` dist-tag, then runs
  `scripts/restore-peer-ranges.ts`. Publishing
  is its own step because npm's two-factor prompt is interactive. Never publish
  without building first: each build stamps `dist/.build.json`, and every
  package's `prepublishOnly` (`scripts/check-dist.ts`) refuses a `dist` whose
  stamp does not match `package.json`. `scripts/canary-changeset.ts` first writes a changeset bumping all
  of them, so they move together: a snapshot of one engine alone would keep a
  peer range the runner's canary does not satisfy. Snapshot versions read
  `0.10.0-canary-<datetime>` (`snapshot.useCalculatedVersion`); the build runs
  after `changeset version` so `init` records those versions, and `init` pins a
  prerelease engine exactly, since a caret on a prerelease resolves to the
  newest canary of that tuple, whose peer range names a different runner build.
  The snapshot also pins every `e2e` peer to that runner build (and an
  integration's engine peer to that engine build), since a prerelease
  satisfies no `>=x <1` range: the tarballs need the pin, main must not keep
  it, so the restore step widens it to `>=<sibling major.minor.patch> <1`
  before the output (versions, changelogs, consumed changesets, peers) is
  committed to main as `chore: release`. A `changeset publish` typed by hand
  needs `node scripts/restore-peer-ranges.ts` after it, or `pnpm check` fails
  on the pin.
  The canary build also builds the desktop driver into both platform
  packages (`build:desktop-native`), so it runs on a Mac with rustup. In
  `release.yml`, a macOS `native` job builds the driver and loads both
  builds the same way before it uploads them, and the release
  and nightly jobs place it into the platform packages (`scripts/native/place-native.ts`)
  before they publish.
- The runner publishes as the unscoped `e2e` (entry points `e2e`, `e2e/agent`,
  `e2e/engine`, `e2e/runner`, `e2e/reporters`, `e2e/oauth/chatgpt`, `e2e/oauth/copilot`, `e2e/oauth/grok`, `e2e/oauth/opencode-console`; the bin is `e2e` too); engines, reporters, and integrations publish public
  under the `@e2e-dev` scope. The `@e2edev` scope (moved to `@e2e-dev` on
  2026-09-28), `@e2edev/e2e`, `@e2edev/oauth` (folded into `e2e/oauth` on
  2026-09-21), and `@e2e-dev/integrations` (moved to `@e2e-dev/kernel` on
  2026-09-29, deprecated by hand after the first `@e2e-dev/kernel` publish)
  are the retired names: deprecated on npm, never referenced here. The release job authenticates with npm
  Trusted Publishing (OIDC), no token; each package carries its own trusted
  publisher connection on npmjs (see "npm Trusted Publishing" in
  CONTRIBUTING.md). Provenance attaches automatically once the repository
  is public.
  Document the CLI as `npx e2e`; npx runs the locally installed bin first, and
  the flag `--no-install` adds nothing once the package is a dependency.
- Private packages are skipped entirely by changesets (`privatePackages: false`),
  so `@e2e-dev/testbed` gets no version bump, no `CHANGELOG.md`, and no git tag.
