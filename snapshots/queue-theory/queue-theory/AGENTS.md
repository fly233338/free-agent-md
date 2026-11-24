# Queue theory — agent guide

A guide to queueing theory for software teams (`README.md`), translated under
`locales/`, plus a SvelteKit website in `queue-theory.github.io/`.

**Read [spec/](spec/README.md) first. It is the single source of truth.**

## Rules

- Edit English in `README.md`; `make content` mirrors it to `locales/en-001/index.md`.
- Translate from `locales/en-001/index.md`, one locale at a time; see [spec/locales.md](spec/locales.md).
- In each locale directory `README.md` is a symlink to `index.md`; never hand-edit `.locale-peer-id`.
- Never hand-edit generated site files: `src/content/`, `src/lib/locale-pages.json`,
  `static/search/`, `static/sitemap.xml`, `static/llms.*`.
- Keep product names, code, formulas, and URLs untranslated.

## Before committing

`make content check build verify` passes, and `git status` in the site shows no
stale generated files. Then deliver per
[spec/repository.md](spec/repository.md#delivery-commit-push-publish): commit,
push, `make publish`.
