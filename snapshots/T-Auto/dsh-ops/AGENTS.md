# AGENTS.md

Instructions for AI coding agents working in this repository. Humans: see
[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (中文：[docs/贡献指南.md](docs/贡献指南.md)), which this file
summarizes and never overrides.

## What dsh-ops is

A DSH tool-enhancement plugin. Its purpose is to save the model's tokens, contain context growth,
shorten task time and make the model more capable — by giving it low-cognitive-load tools with small
inputs/outputs, honest feedback that stops retry loops, and progressive disclosure of advanced
capabilities.

- **Minimal and low-intrusion.** It only adds `ops_*` tools (including `ops_bash` on Windows) and can
  optionally replace some official tools. It does not change host logic, rewrite the shared tool
  registry, or depend on other plugins; integration code with other plugins lives apart from the core.
- **Native and PTC are separate projections of one kernel.** Native mode output is read by the model
  (compact, line-numbered text); PTC output is read by sandboxed code (strict typed data). Do not
  make one shape serve both. See issue #261 for the 0.4.0 design.

## Hard rules

1. **No code file over 1000 lines.** `node scripts/check-file-size.mjs` (`npm run check:size`) runs
   in CI over every git-tracked `.js .mjs .cjs .ts .mts .cts .rs .ps1 .sh .py .cpp .h .hpp .cc` file
   outside `node_modules/ native/target/ runtime/ licenses/ docs/ dist/`. When a file approaches the
   limit, split it into modules and group them in a folder (see `src/shells/`,
   `scripts/lib/build/`, `bench/lib/fixtures/`). Do not raise the limit or add exclusions.
2. **A PR adds at most ~1000 implementation lines** (tests and byte-identical moves excluded) and
   touches only the files its issue names. Large work is split into slices on a staging branch
   (for 0.4.0: `release/0.4.0`).
3. **No AI attribution** in commits, PRs, issues or comments: no `Co-authored-by:` lines naming an
   agent/model/bot, no "Generated with/Made with" footers. Commits use the user's own identity.
4. **Every new behaviour has an assertion** that fails when the change is reverted. No silent skips,
   no retries to hide flaky concurrency — fix the cause.
5. **Do not edit generated output.** `lib/` is built from `src/`; `runtime/` is staged worker output.

## Layout

| Path | Contents |
| --- | --- |
| `src/` | Plugin source (strict TypeScript and TSX). Compiled by `tsc` to `lib/` |
| `lib/` | Build output that is shipped and imported by tests — gitignored, never edited by hand |
| `src/components/<name>/` | One directory per DSH component row (`shell`, `file`, `ptc`, `panel`, `tui`, `hide-official`, …): entry, `package.json`, `locale/`, `icon.png` |
| `native/` | Rust worker (`dsh-ops-worker`); one JSON request on stdin, one JSON result on stdout, spawned per call through the host subprocess/sandbox |
| `test/` | One `*.test.mjs` file = one suite = one process; shared helpers in `test/lib/` (never named `*.test.mjs`) |
| `bench/` | Repository-only benchmarks; never shipped, never part of the default gate |
| `scripts/`, `bin/` | Gate, manifest validation, packaging, CLI |
| `docs/` | Bilingual docs: every document exists in English and Chinese |

## Commands

```console
npm ci --ignore-scripts                                  # install (locked)
npm run build                                            # src/ -> lib/ (tsc + assets)
cargo test --workspace --locked --manifest-path native/Cargo.toml    # Rust unit tests
npm run build:ptc                                        # build + stage the native worker (needed by most suites)
npm run build:bash-ipc                                   # Windows only
npm run verify                                           # build + manifest check + all suites
node test/run.mjs <filter>                               # only suites whose file name contains <filter>
npm run check:size                                       # the 1000-line gate
node scripts/verify-gate.mjs --skip-install              # the full release gate, exactly what CI runs
```

- Suites without a built worker **skip**; a skip is not a pass. On Linux/macOS the gate sets
  `DSH_OPS_REQUIRE_RUNTIME=1`, which turns those skips into failures.
- `DSH_HOME` must point into the system temp directory when running a suite directly; the harness
  refuses anything else. `node test/run.mjs` creates one per suite.

## Code conventions

- English for code, comments, CLI output and commit messages; user-facing docs in both languages,
  updated in the same PR.
- Tool names always come from `publicToolName()` in `src/policy.ts`; never hand-write `ops_`.
- Config is validated in `src/config.ts`; unknown keys are errors that name the key. Defaults in
  `cordis.patch.yml` must equal the defaults in code.
- The host half must not import `@deepseek-ai/*` values at load time; use `ctx.inject` / `ctx.get`.
  Publish tools only through this plugin's own scoped `ctx.tools.register`.
- Tool failures are returned values (`status`, `error.code`, `effectState`), never thrown. Never
  report a partial or early-stopped result as complete.
- Do not remove tool contracts (argument semantics, defaults, path base, paging completeness,
  permission boundaries) to save schema bytes.
- New dependencies need a reason in the PR, an exact version published at least 7 days earlier, and
  no change to security settings.

## Commits and PRs

- Conventional, imperative English subjects, e.g. `fix(file): classify oversized grep files`.
- A PR links a claimed issue, fills `.github/PULL_REQUEST_TEMPLATE.md`, and puts real command output
  (pass/skip/fail counts) in its Validation section.
- Add a `docs/CHANGELOG.md` `## [Unreleased]` entry when behaviour or shipped docs change.
- Never force-push shared branches, rewrite pushed history, or merge PRs without the maintainers.

## Windows notes

- Run `npm`/`git` from PowerShell if the Git Bash environment resolves `npm` to WSL or lacks the git
  identity/CA bundle.
- A local `tar` may fail to unpack the packed tarball on non-ASCII doc filenames; CI is the reference
  for that gate step.
