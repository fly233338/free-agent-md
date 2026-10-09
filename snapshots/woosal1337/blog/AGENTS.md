# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

This is the personal portfolio and blog for `chele.bi`, built with Next.js 14 App Router, React 18, TypeScript, MDX, Tailwind CSS, and Biome. It deploys to Vercel.

Use the existing design system and content patterns before adding new abstractions. Keep changes small and boring unless the task explicitly asks for a redesign or broader refactor.

## Commands

- `bun dev`, start the local dev server.
- `bun run build`, run the production build.
- `bun run check`, run Biome lint and format with auto-fix.
- `bun run lint`, run Next.js lint.

Package manager is Bun. Runtime requires Node `>=20`.

## Architecture

- `app/layout.tsx`, root layout. Wraps the app in providers and Vercel Analytics.
- `app/(website)/`, main website route group, including the homepage, blog, projects, and about routes.
- `components/ds/`, local design-system primitives. Prefer these before creating new UI components.
- `components/blocks/`, domain-specific blocks such as post chrome, polaroids, and contribution graph.
- `components/ui/`, shadcn/ui-style primitives backed by Radix where applicable.
- `components/providers/`, app providers, including theme support via `next-themes`.
- `data/`, static data files.
- `lib/utils.tsx`, shared `cn()` helper plus central site content data such as navigation, career timeline, changelog entries, and projects.
- `mdx-components.tsx`, custom MDX component overrides.

## Conventions

- Path alias `@/*` maps to the project root.
- Biome is the formatter and linter. Do not introduce Prettier or ESLint configuration unless explicitly requested.
- Page and source extensions are `.mdx`, `.ts`, and `.tsx`.
- MDX uses the experimental Rust compiler with `remark-gfm`.
- Theme support uses the `class` strategy through `next-themes`, defaulting to `system`.
- CSS variables store RGB triplets consumed as `rgb(var(--x) / <alpha>)` in Tailwind.
- The site is dark-only; the light palette mirrors the dark one.
- UI components follow shadcn/ui and Radix patterns. Config lives in `components.json`.
- Import design-system primitives directly from their files. Do not add barrel files unless asked.
- `reactStrictMode` is currently `false` in `next.config.mjs`.

## Design

The site is a dark-only editorial system:

- Body and UI use Geist Sans; code uses Geist Mono.
- The reading column is a fixed editorial width; surfaces are dark with hairline borders.
- Preserve the established spacing, type, color, and motion rules.
- Avoid generic marketing layouts and decorative UI that does not serve the content.

## Animation

Prefer CSS for animation and interaction:

- Hover states, nav scrims, galleries, and reveal effects should generally stay CSS-only.
- Use the established easing curve `cubic-bezier(0.16, 1, 0.3, 1)`.
- Use existing durations: `100ms`, `240ms`, `300-400ms`, and `800ms`.
- Scroll reveals should play once via `components/ds/reveal.tsx`.
- `framer-motion` remains only for selected legacy components such as polaroids, number ticker, contribution graph, and GitHub stars.
- Do not reintroduce GSAP or animejs.

## SEO

SEO files are generated from:

- `app/robots.ts`
- `app/sitemap.ts`

OpenGraph and Twitter metadata live in the root layout and route metadata.

## Working Rules

- Read the touched code path before editing.
- Reuse local primitives and helpers first.
- Keep diffs focused on the user request.
- Do not refactor unrelated files.
- Do not overwrite user changes.
- For non-trivial logic, leave one runnable check behind when feasible.
- For visual work, verify responsive behavior and avoid text overflow.
