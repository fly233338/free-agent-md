# Working on SoduWork

This public guide supplements [CONTRIBUTING.md](CONTRIBUTING.md). Read the relevant component guide before changing its interfaces.

## Repository and local startup

- `client/` contains the Electron desktop, main-process services, IPC bridge and renderer.
- `hub-backend/` contains the FastAPI Hub, database migrations and Runner.
- `hub-frontend/` contains the React/Vite administration UI.
- `skills/`, `ops/self-host/` and `tools/` contain bundled skills, deployment and verification tools.

From the root, run `sh start.sh --desktop` on macOS/Linux, `.\start.cmd --desktop` in Windows PowerShell, or `start.cmd --desktop` in Command Prompt. Follow the [startup guide](docs/getting-started.en.md) for prerequisites and isolated data directories. Use synthetic data and test accounts for validation.

## Changes and checks

- **Mandatory Git naming rule:** Do not prepend `Codex/` or `codex/` to feature branch names or pull request titles. Use the feature or fix name directly, such as `media-cards-20261116` or `fix: ...`.
- Preserve existing user changes and data. Add Alembic migrations for database schema changes.
- Run checks for the component you change. In `client/`, run `npm test`. In `hub-frontend/`, run `npm run build` and `node --test tests/*.test.mjs`. For backend checks, inspect `python3 quality_gate.py --help` in `hub-backend/`. For launcher changes, run `python3 -m unittest tools.dev.test_start_local` at the root. On Windows, use `py` for standalone Python commands, or `python` inside the activated environment.
- At the root, run `node tools/check-public-source.cjs`, `node tools/check-third-party.cjs`, `node tools/check-docs.cjs` and `python3 tools/security/scan_secrets.py --download`.
- Review and stage added public files. Git tracks the development inventory; do not generate or commit `SOURCE-MANIFEST.json`. The source exporter generates it inside each archive from the committed files.
- Keep paired English and Chinese documentation and their language links in sync. Directory entry points are English `README.md` and Chinese `README.zh-CN.md`.
- Keep credentials, private addresses, user data, logs, screenshots, build outputs and dependency caches out of commits. Public source inclusion is governed by [PUBLIC-SOURCE.json](tools/distribution/PUBLIC-SOURCE.json).
- Sign off commits under the DCO with `git commit -s`. In pull requests, describe the behavior change, checks actually run, platforms tested and remaining gaps.

See the [developer guide](docs/development.en.md), [CI guide](.github/CI.md), [release scope](docs/release-scope.en.md) and [security policy](SECURITY.md) for details.
