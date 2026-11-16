# AGENTS.md

Guidance for coding agents that change this repository. These rules add to [CONTRIBUTING.md](CONTRIBUTING.md), which covers the same setup and review process for people. To install Pomerado for a user, follow [docs/agent-setup.md](docs/agent-setup.md) instead.

## Setup and checks

Use macOS or Linux, Node 24.21 or a later Node 24 release, git 2.36 or later, and jq.

```sh
corepack enable
corepack pnpm install --frozen-lockfile
corepack pnpm typecheck
corepack pnpm build
corepack pnpm test
corepack pnpm exec playwright install chromium
corepack pnpm test:browser
npm pack --dry-run
bash tools/ci-scan.sh content
GITLEAKS=/path/to/gitleaks bash tools/ci-scan.sh secrets
```

- Browser tests run the built `dist/`, so build before you run them.
- Tests use synthetic sites and scripted model responses. They need no model key, and no test may call a real model.
- CI runs gitleaks 8.30.1.
- CI runs a browser test that fails once more, in a fresh process, and reports one that passes then as flaky. Fix a flaky test at its cause. While a fix is under way, list the test in `typescript/tests/browser/quarantine.json` with `test` (as CI names it, `file › title`), `owner` (a GitHub login) and `issue` (a public issue's URL), and its failures warn instead of failing CI. Remove the entry with the fix. CI fails while an entry names a test that no longer exists.
- On a pull request, CI runs each browser test whose own lines in a spec file change three times, as many as fit about 80 s, and each test in a changed unit test file three times, so a new flaky test fails before it merges. A change above a spec file's first test counts for every test in the file; changed fixture files outside the spec files repeat nothing.
- Set `EVENT=pull_request`, `PR_BASE` to the base commit and `PR_HEAD` to your head commit to scan your commits as CI does. The content scan then also checks your commit messages, and the secrets scan checks each commit's diff.

## Layout

- `typescript/src/` holds the minter, Guardian, the runtime, browser helpers and the local MCP host.
- `typescript/authoring/` holds the minter's shared prompts and examples.
- `typescript/tests/unit/` holds Vitest tests, and `typescript/tests/browser/` holds Playwright tests with local fixture sites.
- `tools/` holds build helpers, the CI scans and the browser shard planner.
- `docs/` holds guides. [docs/how-it-works.md](docs/how-it-works.md) lists each module.
- In code, OpenAI model IDs are set only in `typescript/src/models/models.ts`. A unit test enforces it.

## Rules

- Every change goes through a pull request. Never push to `main`.
- Never run `gh pr merge`. A maintainer merges.
- Bring `main` into your branch with a merge, not a rebase. Never force-push.
- A pull request merges only after an independent review and green CI.
- Rulesets on `main` enforce this. They require a pull request and three checks on the current head: a green `CI`, `review/clear` from the independent review, and `Approval`. The approval gate in `.github/workflows/approval.yml` posts `Approval` through its own GitHub App. It passes at once when the author is a maintainer, someone with write access, and the head branch is in this repository. A pull request from a fork, or from an outside contributor, also needs a code owner's approval of its current head commit before `Approval` passes. [docs/RELEASING.md](docs/RELEASING.md#the-approval-gate) describes the gate and its setup. The release workflow runs the full check again on every push to `main`, which validates the merged result.
- Maintainers merge by hand with a merge commit until a merge queue takes over.
- A push after a review needs a new independent review.
- Write the failing test first for a change in behavior.
- Add to this package only code the local host runs, or a hook interface another host implements.
- Keep `#N` style references out of commit messages, where N is a number. The content scan rejects them. Link a public issue by its full URL.
- Public text stays generic. Keep customer data, credentials, incidents, internal hostnames and internal references out of code, tests, commit messages and pull request text.
- Workflows name the exact code they run: each action at a full commit SHA with its version in a comment, each container image at an `@sha256:` digest, and no download piped into a shell. `pnpm test` runs `tools/check-workflows.ts`, which checks this, and Dependabot moves the action pins weekly.
- Third-party code keeps its own license. Put its license and notice under `third-party/`, as `third-party/codex/` does for the Guardian policy, and ship them with the package.
- Contributions are accepted under the MIT License.
