# 67js for coding agents

Read this before you change code in this repository. [CONTRIBUTING.md](CONTRIBUTING.md) has the full rules; this file is the short path.
To build scenes with 67js rather than change it, use the MCP server and the skills in `skills/` instead ([README](README.md#for-agents)).

## Layout

- `src/` is the library, one flat folder. `src/agent-*.js` and `src/mcp*` are the MCP tool surface.
- `bin/67js-mcp.mjs` starts the MCP server. `packages/` holds the addon packages.
- `tests/` holds the Node tests, one `*.test.js` per area. `scripts/` holds the build, smoke and gate scripts.
- `docs/` holds one guide per feature. `skills/` holds the agent skills that ship with the package.
- `changes/` holds one changelog note per pull request. `artifacts/` is ignored output for screenshots and logs.

## Set up

```sh
npm ci
```

Node 20.19 or later, Node 24 on CI. Chrome is needed for the smoke scripts and the MCP tests.

## Before you open a pull request

```sh
npm run preflight
```

It runs the gates of the `Test` workflow that apply to the files your branch changed: protected files, the change note, links,
tool schemas, size, tool cost, the build, the unit tests with coverage and the coverage gate. It keeps going after a failure,
writes each log to `artifacts/preflight/`, prints only the tail of a failing log and ends with one line per check and its fix.
`--skip-tests` skips the slow test pass while you iterate, and `--json` adds a machine-readable summary.
Run the full preflight once before you push. A green preflight means the `test` check should pass.
`npm ci` installs a pre-push hook that runs `npm run preflight -- --skip-tests` and stops a push that would fail those gates.
`SKIP_PREFLIGHT=1 git push` skips it once; use that only for a push you know the gates do not cover.

For one test file: `node --test tests/<area>.test.js`.

## Rules that fail a pull request

- Add `changes/<issue>.md` with one bullet when you change `src/`, `bin/`, `packages/` or `skills/` ([changes/README.md](changes/README.md) has the naming rule).
- Name the branch `<issue>-<slug>` and the pull request `<imperative sentence> (#<issue>)`. Put `Closes #N` or `Part of #N` in the description and paste the commands you ran with their results.
- A change to an MCP tool schema or a skill needs the Haiku bench table in the pull request ([CONTRIBUTING.md](CONTRIBUTING.md#tool-schema-and-skill-changes)).
- Look changes (shaders, lighting, materials, default render, post steps) carry `hold:look-approval`. Never remove it and never merge: only the maintainer merges.
- Never edit `CHANGELOG.md`, `bench/size/budgets.json`, `bench/size/baseline.json` or `bench/tool-cost-budgets.json`. Maintainers reset them at release.
- A bundle that grows past its allowance needs a line in `changes/<issue>.size.md` that says why the bytes are worth it ([bench/size/README.md](bench/size/README.md)). The same file accepts tool cost growth ([bench/tool-cost/README.md](bench/tool-cost/README.md)).
- Coverage may not drop. Write the tests in the same commit as the code.
- Never weaken or skip a test to make it pass. Find why it fails.

## Code

- Descriptive full names, one statement per line, small functions, comments only for a reason the code does not show.
- No new runtime dependency in the core. Optional features go in an addon.
- Scene builders are deterministic for the same seed; tests compare geometry byte for byte.
- Validate input at the public boundary and throw an error that says what failed and what to pass instead. Agents read these errors.
- MCP tools accept no arbitrary code and no remote asset URLs ([SECURITY.md](SECURITY.md)). Keep every count and size bounded.
- Update the guide in `docs/` for the feature you change.

## Checks a person or a GPU runs

Shaders, lighting, skinning, glTF and the frame path need real pixels. `npm run preflight` names the ones that may apply to your
change; the table in [CONTRIBUTING.md](CONTRIBUTING.md#checks) says when each one is needed. Say in the pull request which ones you
ran and what you saw. If you cannot run one, say that instead.

## Working etiquette

- One change per pull request, on a branch from `main`. Merge `main` into it before you push again.
- Stop only processes you started, by their PID. Other jobs may share the machine.
- Issues and pull requests are public. Keep local paths, tokens and personal data out of them.
