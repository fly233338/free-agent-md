# MCPorter Repository Notes

- Use the repository's declared pnpm version and run project commands directly with `pnpm`.
- Run `pnpm docs:list` before documentation work.
- Before handing off code changes, run `pnpm check` and `pnpm test`.
- Live DeepWiki tests are opt-in: `MCP_LIVE_TESTS=1 pnpm exec vitest run tests/live/deepwiki-live.test.ts`.
- The skipped OAuth-promotion case in `tests/runtime-transport.test.ts` can be validated by temporarily unskipping it. Vitest does not support `--runInBand`; remove temporary helper files afterward.
- Read `VISION.md` before broad triage or product decisions.
- Prefer focused regression tests and verifiable fixes. Ask before new features, dependencies, build-tool changes, broad API/config changes, or architecture shifts.
