# Repository Guidelines

## Project Structure & Module Organization

This pnpm monorepo contains a mobile Codex client backed by a local server. `apps/mobile` is the Expo React Native app, with routes in `src/app`, UI in `src/components`, state in `src/state`, API helpers in `src/lib`, and assets in `assets`. `packages/codex-relay` contains the Hono Node server in `src`, Vitest tests in `test`, and shared Zod API contracts in `src/api-schema.ts`. Treat `dogfood-output*` as generated artifacts.

## Build, Test, and Development Commands

- `pnpm install`: install workspace dependencies with pnpm 10.
- `pnpm dev`: run the local server with `tsx watch`; it listens on port `8787`.
- `pnpm dev:server`: run the local server with `tsx watch`; it listens on port `8787`.
- `pnpm dev:mobile`: start Expo Metro for a development client.
- `pnpm dev:mobile:ios` / `pnpm dev:mobile:android`: build and run the native dev client.
- `pnpm lint`: run oxlint plus oxfmt checks across `apps` and `packages`.
- `pnpm lint:fix`: apply oxlint fixes and format the repo.
- `pnpm typecheck`: run `tsc --noEmit` in every package.
- `pnpm test`: run the server Vitest suite.

## Coding Style & Naming Conventions

Use TypeScript throughout. Formatting is owned by `oxfmt`; do not hand-format around it. The current style uses two-space indentation, double quotes, trailing commas where added, and ESM imports. React components use `PascalCase` file and export names, hooks use `use-*` file names and `useX` functions, and helpers use `camelCase`. Keep shared API shapes in `packages/codex-relay/src/api-schema.ts`.

## Mobile UI Primitives

Prefer established UI primitives over hand-rolling fragile React Native layouts.

- For any mobile bottom sheet, use `AppBottomSheet` and `SheetActionRow` from `apps/mobile/src/components/ui/bottom-sheet.tsx`.
- Do not create ad hoc `Modal` + dimmer + nested `Pressable` sheet structures in feature components.
- Do not position bottom sheet row text with `absolute`; keep rows as icon/text/trailing columns through `SheetActionRow`.
- Put spacing, safe-area padding, dimmer behavior, accessibility roles, and iOS layout fixes inside reusable primitives rather than duplicating them per screen.
- If a new screen needs a layout pattern that is likely to recur, add or extend a UI primitive first, then compose the feature screen from that primitive.
- After changing mobile UI primitives or their callers, capture the affected screen in the iOS simulator or device when practical, especially for modals, bottom sheets, keyboard-adjacent UI, and compact controls.

## Testing Guidelines

Server tests use Vitest and live in `packages/codex-relay/test` with `*.test.ts` names. Add focused route or schema coverage when changing API behavior, validation, streaming, or thread state. Run `pnpm test`, then `pnpm typecheck` and `pnpm lint` before handing off broader changes. Mobile code currently relies on typechecking and manual/dev-client verification; document any device or simulator checks in the PR.

## Commit & Pull Request Guidelines

The short Git history uses simple Conventional Commit-style messages such as `chore: oxlint, oxfmt`; prefer `feat:`, `fix:`, `chore:`, or `test:` with an imperative summary. PRs should include a brief description, validation commands run, linked issue if applicable, and screenshots or screen recordings for mobile UI changes. Mention configuration changes such as `EXPO_PUBLIC_CODEX_RELAY_SERVER_URL` or `CODEX_RELAY_WORKSPACE_PATH`.

## Security & Configuration Tips

Do not commit local secrets, device-specific URLs, or generated native build output. Physical devices usually need `EXPO_PUBLIC_CODEX_RELAY_SERVER_URL=http://<host-lan-ip>:8787`; simulators and web can use the default `127.0.0.1` value.
