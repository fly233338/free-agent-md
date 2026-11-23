# Agent instructions

**Building an app with Exact rather than working on it?** This checkout is the version to use:
Exact has no releases, tags or npm package, and an app uses the checkout by path. Make it with
`bun scripts/exact.mjs new <path>`. A website (pages served to a browser) reads only
`docs/start-here-site.md`; any other app reads `docs/start-here.md`. That guide is the only
required reading (LLP 1115 D7). The rest (`docs/contract-for-agents.md`, `docs/agent-pitfalls.md`, `docs/contract-grammar.md`,
`docs/reference.md`) is lookup only, by the section its table names: do not read the long
guides front to back. `docs/recipes/` answers the common questions in one short file each,
`contract vocab <name>` answers for any tag or property, every `bun exact.mjs <verb>
--help` names its flags, and `apps/shelf` is a whole app to grep.

**Feedback (required when building an app).** When a doc was wrong or missing, a workaround was
needed, something took several tries or a command confused you, record it from the app's directory:
`bun exact.mjs feedback note "<what happened>"`. It attaches exact2's commit and the last command's exit
code, never output or code. It goes to Expo only as `bun exact.mjs feedback status` says (skip it under `never`);
`EXACT_FEEDBACK=0` stops it on the machine (docs/diary.md).

Working on exact2 itself: read `rules/RULES.md` and `rules/DEFERRED.md` first; they bind and this file does not.
The design record, the LLP corpus, is private: clone `expo/exact-llp` into `llp/`, which this
repository ignores (a worktree links its checkout's: `ln -s <checkout>/llp llp`); there `llp/1000-exact2-root.explainer.md` is the map. Code and docs cite LLPs by
number (`LLP 1115 D7`), and a reader without the corpus learns only that the decision is recorded.
Push an LLP before the code that cites it. `docs/agent-pitfalls.md` lists verified
footguns in writing apps here; add to it when you hit one. Design documents under `llp/research/`
are the predecessor's — research, never authority.

## Write the web, ship the platform

LLP 1115 (Charlie, 2026-10-09; James's "no tells"). **What the author writes is CSS**: the
vocabulary, the layout model, the dev loop. **What the author leaves unsaid is the
platform's**: controls, colour, type, motion, gestures, presentation, haptics, keyboard and
accessibility come out as a hand-built UIKit/SwiftUI app following Apple's guidelines would
have them (AppKit on the Mac, and each platform likewise). **What the author writes wins.**
Precedence: author > platform > CSS default. One test settles a dispute: *would someone who
knows the platform notice?* If so it is a tell, and the platform's answer wins; judge against
a hand-built screen on the same OS version, not against Chrome.

So layout stays CSS (users cannot perceive it): a bare node is `display: block`,
`box-sizing: content-box`, `flex-direction: row`, `flex-shrink: 1`, and the web is the
layout parity oracle — a kernel that disagrees with a bare `<div>` reintroduces the
four-disagreeing-default-layers bug class the predecessor had (an unavoidable deviation is
declared in `llp/1001-kernel-v1.spec.md`). Names stay CSS (they are what the author writes):
`object-fit`, `text-overflow`, `line-clamp`, not `resizeMode`, `ellipsizeMode`,
`numberOfLines`; where a common reset (normalize.css, Tailwind's preflight) differs from the
raw default, its behaviour is a familiar path too (LLP 1104 D4). Unsaid presentation is the
platform's: a `color` a bar button only inherits from the page leaves UIKit's tint. Agents
writing apps should therefore say less — structure (a header's heading and buttons, a
`tablist`, an `alertdialog`) and leave colours, fonts and metrics to the platform.

## Apple platforms: public API only

Exact's Apple hosts use only Apple's public API: the classes, methods, properties, keys and
notifications that Apple's SDK headers declare and its documentation describes. App Store
review rejects an app that uses anything else ([App Review Guideline
2.5.1](https://developer.apple.com/app-store/review/guidelines/#software-requirements)). So
shipped code calls no private method, reads no undocumented key, and names no private class:
it looks none up by name, compares no class's name and holds no literal of one. Find a platform
view through public API, such as its accessibility elements, a delegate or a notification.
Where public API cannot reach it, do without, and name the known difference in the LLP that
owns the feature and in the code. Private API is for development builds only, inside an `#if`
on `EXACT_INSPECT` or `EXACT_AGENT`; LLP 1035.003 names the only exceptions.
`host/apple/inspect-gate.test.mjs` checks the sources for private class names.

## Numeric typography

On graphical hosts, use tabular digits for numeric columns and values that change
in place. Use default spacing for prose, ordinary labels and static standalone
statistics. Apply it to numeric text, keeping the platform font. See the
[guidance and limits](docs/contract-for-agents.md#tabular-numbers).

## Writing

For all prose, always: comments, commit messages, guides, LLPs, issues and PR text. This
section binds (`rules/RULES.md`, "Agents").

- Write with clarity of mind. A reader should understand it on first reading and find
  nothing ambiguous.
- Say what the reader needs to know about the topic and nothing more. Do not recount
  history or keep a diary; an alternative not chosen earns a line when it explains the
  choice.
- Cite sources where they help: standard specifications, and host platform API
  documentation and guidelines.
- Comments should communicate information that cannot be easily inferred from the code.
  Judiciously omit or remove comments or parts of comments that do not clearly explain
  anything that is not already communicated by the code, though take care not to delete
  comments with meaningful marginal value.
- Before opening a PR or pushing to main, do an editing pass: reread the prose you added
  or changed as a reader new to the work would, and hold each line to the points above.

## Working here

- Tooling runs on Bun (pinned in `package.json`); `bun install --frozen-lockfile`.
  Rolldown remains the app bundler. Node and npm are not required.
- The web artifacts (`app.wasm`, the Markdown editor, text flow) build with a pinned
  nightly (`WEB_TOOLCHAIN` in `scripts/app.mjs`) that builds std for size; everything
  else is `rust-toolchain.toml`'s stable, which the gate and hourly lane use. That
  stable moves to each Rust release within two weeks, with the lints the release
  adds fixed or allowed in the same commit (LLP 1153.003 D6.1). `build.mjs`
  names the install commands when the nightly or its `rust-src` is missing.

- `kernel/tables/schema.json` is the one declaration authority; `kernel/build.rs`
  generates from it. Edit the table, never generated code.
- Every source file ≤ 1,500 lines. Stage (`git add -A`) before running the gate; caps reads tracked files.
- Writing or changing a test: read `docs/testing.md` (waits, isolation, coverage, measuring).
- **The only blocking gate is `bun scripts/gate.mjs`.** Run it, push, and fix what
  the hourly lane attributes to you. Its warm budget after a one-crate edit is 30 s.
  It runs format, caps, boot, an incremental Cargo check of default members, and
  small Rust and Bun unit suites. Every part runs after failures and prints its time.
  A cold checkout must provision and compile its dependencies first.
- **Everything else runs hourly:** `bun scripts/async.mjs` checks origin/main's newest
  tip over all commits since its last run. It runs the full build, default-member
  tests, workspace check and clippy, format, caps, boot and wasm check; `affected.mjs`
  selects the other Cargo and Bun suites, app drives, macOS and UIKit XCTests,
  conformance and Apple platform builds. The quick difftest runs each hour; the
  longer semantics checks reuse passing input fingerprints. Every suite runs at
  least daily. New failures are bisected independently through affected commits with the
  failing suites and their prerequisite builds; the actual parent must pass. A probe
  that cannot finish names its range without assigning blame. Logs and attribution are in the lane's
  `target/async/`, local issues and git notes (`refs/notes/async`, `async2`).
- The hourly lane also installs tvOS and builds
  Linux, Windows x64 and ARM64, and Weatherlight's Android APK. It needs the Rust
  cross targets, Zig, pinned Hermes bundles, Android SDK/NDK and JDK. `--tier 2` runs
  only these platform checks in a separate worktree. A cross-target
  compile proves compilation; presentation and input need the native hardware.
- A green Cargo check proves compilation, not an app's behavior. The hourly lane
  builds and drives affected apps and runs the platform tests. Use `scripts/agent.mjs`
  or the app itself to investigate a behavior; the driver commands are below.
- `bun scripts/affected.mjs` lists the test suites a branch's changes can affect (the working
  tree included) and the command for each; `--run` runs the Cargo and Bun ones, and `--why
  <suite>` says why one was selected. A suite reads its Cargo dependencies, its imports and
  what its tests name. Shared code that names an app or a host only builds what its caller
  asks for, so a Shelf change runs Shelf's tests and a Linux host change runs no XCTest. A
  change to Swift test files alone runs only the XCTest classes they reach (`--only`). A
  read that nothing names can escape the selection; `--audit <suite>` runs a suite with the
  units outside its inputs unreadable to look for one (`docs/testing.md`). Advice, not a check.
- An unset `EXACT_UPDATE_TRUST` bakes development trust, which checks only an
  origin named by `EXACT_UPDATE_ORIGIN`. `EXACT_UPDATE_TRUST=production` native
  bakes require an authenticated `EXACT_UPDATE_RECEIPT` or explicit new-stream
  `EXACT_UPDATE_GENESIS=1` (README).
- An app outside this repo (one `bun scripts/exact.mjs new <path>` made) builds, runs, and is
  driven through these same scripts with `EXACT_APP_DIR` set — `scripts/app.mjs` is the
  one place that knows; its `exact.mjs` sets it. exact2 is consumed there by path. What
  `exact new` writes (its `AGENTS.md`, `exact.mjs` verbs, `app.json` `$schema`) is LLP 1086.
- The web build, `bun host/web/build.mjs <app>`, makes the JS target (LLP 1071: the
  plan compiled to one ES module over a ~20 KB runtime, `host/web-js`); what it refuses
  fails the build. A game builds the wasm target (LLP 1071 §8), and `--wasm` is the
  internal flag for the uses below. The dev loop, the agent's web host, the smoke's app drive and
  metrics run what the build makes: on the JS target an edit rebuilds and reloads the
  page, carrying compatible state and, while the logic is unchanged, settled answers.
  A native client opening the dev URL is forwarded to the resident loop's producers
  (`dev.mjs --wasm`, started at its first request).
  Delivery bakes the web crate without its wasm for the native streams and publishes
  the JS build of that bake's plan as the web root; the smoke's bare-plan fixtures and
  conformance's oracle stay `--wasm` (LLP 1071 §7, "Retiring the wasm target on the web").
- The dev loop is `bun host/web/dev.mjs`: edit `apps/caltrain/app.contract` or its data
  crate, the page rebuilds and reloads (`--wasm`: the resident loop restarts the plan in
  place in ~20 ms). `bun scripts/metrics.mjs` prints every number
  (`--long` adds the macOS build and boot, and the loop's own budgets: the
  warm gate, touch one line, test what you changed; `--web-bytes` prints only the bytes each
  web app ships against its budget, in seconds, before and after a cut). macOS: `bun host/apple/build.mjs --run`;
  iOS: `bun host/apple/build.mjs --ios --run` (a simulator; `--sim` or `EXACT_SIM` picks one);
  tvOS: `bun host/apple/build.mjs --tvos --run` (an Apple TV simulator; LLP 1008 §9;
  `--tvos --no-install` compiles it with none, which the hourly lane runs after a change to Swift it shares with iOS);
  `--device --run` on a connected iPhone (signed with a team profile on this Mac);
  `--host` also builds the sample host (LLP 1031 D10), the native app that embeds two
  sessions, which `bun scripts/smoke.mjs host` drives and `scripts/agent.mjs host
  --session a …` addresses; `--ios --host` is the same fixture on a simulator, driven
  by `smoke.mjs host-ios` and `agent.mjs host-ios`. The Swift is one package, `host/apple/Package.swift`:
  `ExactKit` (session, view, app owner — what an embedder links) and the executables
  as adapters over it. `apps/<name>/app.json` is the app manifest (LLP 1030 D2): the
  bundle id, name, host files, and deploy policy come from it, never from a crate name.
- The hourly lane runs `cargo run -p contract-difftest -- quick` and the longer
  Contract semantics checks (`semantics/README.md`). Non-default crates and hosts
  run their affected tests there too; a local full-workspace build is not a gate.
- Verify by running, never by grepping. Fix loops get three rounds, then stop and say so.
- The code to push has been simplified, its tests follow the [test optimization
  guidelines](docs/testing.md), and its prose and commit message follow the [writing
  guidelines](#writing). Do this before testing; prose edited after testing needs no rerun
  unless it changes behavior, like a prompt or agent context.
- Land it (LLP 1176; Charlie, 2026-11-14: "just land stuff, we can fix it later if it breaks
  something"). When your change passes the gate on your own tree, merge it yourself, at
  once, as a squash, and fix forward what it breaks. Do not hold it for a main that moved
  during the checks, for a failure main already has (say so where its owner will see it), or
  for a second pass after a rebase with no conflict. A pull request that `rules/RULES.md` says
  needs a human's approval still does. Give each change in flight its own warm worktree.
- To see a change work, drive the app: `bun scripts/agent.mjs <web|macos|ios|linux> tree
  "tap change-station" "type station-search Palo" "clock +60000" state logs "screenshot
  out.png"` — the ten operations of LLP 1012 and LLP 1079 (`perf`: a subtree's work by
  plan site, `perf <target> during "<op>" …` for the difference a drive made, and
  `perf frames`, `perf frames live <ms>` for a game's frame pacing; a development build writes a trace on ⌥⌘T
  (macOS), ⌥⇧T (web), the dev menu's Save Trace (iOS) or `SIGUSR1` (macOS, the iOS simulator, Linux), which `bun
  scripts/agent.mjs trace <file>` reads, `trace --pid <pid>` asks a running app for, and `trace --phone` copies off a
  phone; `--plan <dir>` joins another build's source map), the same on every host, with the clock
  in your hands (`clock settle` instead of waiting; `"screenshot out.png over 600 every
  50"` films motion on it as a contact sheet, `.apng` to play). Android reader drives refuse films.
  Use `android --live` and `adb shell screenrecord` to see Android's reader layers play.
  The driver refuses a build older than its sources and names the rebuild (LLP 1012.001.000).
  `bun scripts/smoke.mjs
  <web|macos|ios|linux|host>` is the whole app driven that way. The Linux host
  (`bun scripts/build-linux.mjs caltrain`: a development build, as
  `build.mjs` makes for Apple; a release build is the one that ships) runs headless
  anywhere, macOS included. `host-dev` compiles incrementally unless the shell
  exports `CARGO_INCREMENTAL=0`, which a hand-run cargo obeys (a touched kernel
  line is then 17 s, not 6) and `build.mjs` overrides, saying so.
- The terminal host (LLP 1101): `cargo build --profile host-dev -p harness-terminal`,
  then `./target/host-dev/harness` runs the coding harness in this terminal (inline;
  `--fullscreen` for the alternate screen), or `exact-terminal <entry.contract>` any
  terminal entry. After `--drive` it runs the operations headless (`--size 80x24 --drive
  type prompt "hi" key Enter until "…" print`); headless, the frames go into a terminal
  emulator (`vt100`) and `print`, `screenshot` read its screen (`print --all` the
  scrollback, `document` the whole laid-out document). With `--print`, `--json`, or a
  pipe on stdin or stdout, an entry runs once and exits (LLP 1101.003: `harness --print
  --prompt "…"`, `exact-terminal apps/todo/terminal.contract --json /done`); the other
  words are its location (`--help`). Develop it in `host-dev`: a debug build lays out a long
  document hundreds of times slower. `exact-terminal` is in `default-members`
  (`tests/it/screen.rs` drives inline mode through the emulator); `harness-data` is not,
  so the hourly lane runs `cargo test -p harness-data` when the harness changes.
  `examples/replay.rs` replays a recorded session through the same emulator.
  The LLP reader is the other terminal app (LLP 1101.004): `cargo build --profile
  host-dev -p llp-terminal`, then `./target/host-dev/llp [llp/ or a document]`.
- Delivery (LLP 1030.000): `bun scripts/deploy.mjs <app> [--origin <dir>]` prints the
  classifier's table (a dry run); `--yes` publishes the web root and signed bundles per stream through
  `scripts/origin.mjs`; `keygen <id>` makes a signing key (the private half never enters
  the repo). `bun scripts/smoke.mjs deploy` drives it; on a Mac it signs production
  macOS Rust modules, so set `EXACT_RUST_SIGN_IDENTITY` to an identity listed by
  `security find-identity -v -p codesigning` (an Apple Development one does). Its first
  deploy builds every release bundle cold; the rest reuse that cache. A native host
  opens its update store at launch and checks after first pixel
  (`EXACT_UPDATE_ORIGIN=<url>` points a dev build at a directory `serve.mjs` serves;
  `state.delivery` shows what it did).
  `bun scripts/push.mjs <app> [--watch]` publishes an edit to installed release binaries
  as a signed update in about a second, from the stream a deploy or a production build
  started; `deploy.activate: "immediate"` applies it while the app is open. A channel's
  origin `"appdrop"` is AppDrop's, named after the signing key: no account, no server.
  Moving a stream to a new origin, pass `--seq-above` the old origin's seq.
- `QUEUE.md` is what would make sense to do next. Add a line when you find something
  worth doing; delete it when it lands. It decides nothing.
- An app under `apps/` keeps a diary, as an app `exact new` made does (`docs/diary.md`,
  "What to keep": the header, then Rough, Lean in, Needed and Checkpoints). Write it as
  you work, at `apps/<app>/diary/<YYYY-MM-DD>-<topic>.md`, and commit it with the
  change: it is how the team sees where building on Exact was rough, including what you
  fixed in exact2 to get past it. The app's name may appear; secrets and personal data
  may not. Nothing is sent: the repository is the record.
- Each worktree builds into its own `target/`: never symlink or share another
  checkout's (the scripts refuse); a private `CARGO_TARGET_DIR` outside every
  checkout is fine. What a development Apple build takes from the machine
  instead: the host's two Rust modules, by the SHA-256 of every input
  (`~/.cache/exact/apple-modules`, `host/apple/modules.mjs`), and, into a
  `target/` that has compiled nothing, the registry crates another build
  compiled and, for an app, the checkout's own crates another app of the
  checkout compiled, which Cargo then accepts or not by its own fingerprints
  (`~/.cache/exact/apple-crates`, `host/apple/crates.mjs`). A development web
  build takes the compiler and the leaf wasm modules the same way
  (`~/.cache/exact/web-modules`, `host/web-js/module.mjs`; `bun
  host/web-js/module.mjs --prebuild` warms a builder for its checkout's
  sources). Deleting any of these directories only costs the next first build
  its time.
- Never `git stash`. Kill only PIDs you recorded. Agents remove apparatus freely and add
  none without a human saying so.
- Optional capability is a separate artifact loaded on demand (the GPU module) or another
  executor (the browser, for motion on the web) — never a cargo feature on a core crate.
  Each crate depends on strictly less than the one above it; there is no build matrix.

The Snapback client (`snapback4/`) is not in this repository, and Exact works without it: an app that
asks for Snapback is told the client is missing. A checkout that has it there uses published
`snapback4@0.4.33` and the matching immutable Rust revision in `snapback4/Cargo.toml`; rebuild an
app’s device with `bun exact.mjs snapback --rebuild` after changing these pins.
