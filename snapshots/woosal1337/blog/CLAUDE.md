# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal portfolio/blog website for chele.bi, built with Next.js 14 (App Router) and deployed on Vercel. Uses MDX for content pages, Tailwind CSS for styling, and Biome for linting/formatting.

## Commands

- `bun dev` — start dev server
- `bun run build` — production build
- `bun run check` — run Biome linter and formatter with auto-fix (`biome check --write .`)
- `bun run lint` — run Next.js lint

Package manager is **Bun**. Runtime requires Node >= 20.

## Architecture

- **`app/layout.tsx`** — Root layout wraps everything in ThemeProvider and TooltipProvider, plus Vercel Analytics.
- **`app/(website)/`** — Main route group: home (`page.tsx`), blog, projects, videos, about. The website layout sets site-wide metadata.
- **`app/(website)/videos/`** — YouTube episodes. Each episode is `(episode)/<slug>/page.mdx` with an exported `meta` (video id, chapters, sources, kit), discovered by `lib/videos.ts` the way `lib/blog.ts` discovers posts. `[slug]/kit/[...file]` renders the episode's kit — the files under the repo-root `videos/<dir>/` folder that the YouTube description links to — as pages at build time via `next-mdx-remote`. Keep `videos/` as the single source of truth; the published description URL points at it.
- **`components/`** — organized into `ds/` (design-system primitives), `blocks/` (domain-specific: post chrome, polaroids, contribution graph), `ui/` (shadcn/ui primitives), `hooks/`, and `providers/` (theme provider wrapping `next-themes`).
- **`data/`** — static data files (`books.ts`).
- **`lib/utils.tsx`** — `cn()` class merge helper, navigation items, career timeline, changelog entries, and project definitions. This is the central data file for site content.
- **`mdx-components.tsx`** — custom MDX overrides (responsive images via `next/image`, external link icons).

## Key Conventions

- Path alias: `@/*` maps to project root.
- Dark-only editorial design system. Body and UI use Geist Sans; code uses Geist Mono. Surfaces are near-black with 1px hairline borders.
- CSS variables hold RGB triplets consumed as `rgb(var(--x) / <alpha>)` in Tailwind. Light and dark are both first-class, `class` strategy via `next-themes`, default `system`.
- Reusable primitives live in `components/ds/` (direct file imports, no barrel). Compose these before inventing new components.
- UI components follow shadcn/ui patterns with Radix UI primitives. Config in `components.json`.
- Biome is used instead of ESLint/Prettier. Notable disabled rules: `noNonNullAssertion`, `noForEach`, `noArrayIndexKey`, `noSvgWithoutTitle`, `useButtonType`.
- Page extensions: `.mdx`, `.ts`, `.tsx` — MDX uses experimental Rust compiler (`mdxRs: true`) with `remark-gfm`.
- `reactStrictMode` is **false** in `next.config.mjs`.

## Animation Approach

Motion uses one easing curve `cubic-bezier(0.16, 1, 0.3, 1)`, scroll reveals play once (`components/ds/reveal.tsx`), and filtering is instant.

- **CSS only** for nearly everything: hovers, the nav scrim, the gallery (scroll-snap), reveals.
- **framer-motion** survives only in kept legacy components: polaroids, number ticker, contribution graph, github stars.
- GSAP and animejs were removed from the project.

## SEO

`app/robots.ts` and `app/sitemap.ts` generate SEO files. OpenGraph and Twitter metadata configured in root layout.
