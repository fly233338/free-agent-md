# Mister Download Manager (MDM) — agent guide

Mister Download Manager (MDM) is a download manager for Windows in Rust (egui + storytold
craft-libs), laid out the way Internet Download Manager users expect. Start by reading
[README.md](README.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Rules

1. **Clean room.** MDM contains no code, binaries, artwork, icons, sounds or text from
   Internet Download Manager or any other download manager. Never disassemble, decompile,
   debug-attach or patch any IDM file, and never bypass its licensing or trial. Behaviour is
   learned only from public documentation, screenshots and black-box use of a licensed copy.
   One exception, the maintainer's: the website's comparison page may show the other download
   managers' own logos (never IDM's), small, to identify them, with a notice that they belong to
   their owners and their sources in `website/assets/alts/SOURCES.txt`.
2. Every user-visible text goes through `crate::i18n`; run `python tools/i18n/extract.py`
   after adding one.
3. Windows-only calls live in `crates/app/src/win32.rs`, their Linux and macOS counterparts in
   `unix.rs`; the rest of the workspace is safe, portable Rust (`unsafe_code = "deny"`). A
   feature works on every system, or says why it can't (`cfg` with a comment).
4. Fix root causes, keep data contracts aligned between producers and consumers, and verify the
   whole system end to end after each change.
5. Every PR updates [ROADMAP.md](ROADMAP.md): move its item to done (or add it), keep the
   statuses true. Public file: no security details beyond CHANGELOG's wording, no private notes.
6. Every PR description shows what it changed in screenshots, as many as it takes: each changed
   window and state, before and after, light and dark, a long language (de) and right to left (ar);
   phone width for the website. The images live on the `pr-shots` branch (`<pr>/<name>.png`, never
   merged) and are embedded from `raw.githubusercontent.com/anefzaoui/misterdownloadmanager/pr-shots/`.
   Neutral test folders in shots, no IDM artwork. A change with nothing to see shows its proof
   (tables, logs) instead and says so.

## Commands

- `cargo build` / `cargo test` / `cargo clippy --all-targets` / `cargo fmt --all` — workspace.
- `tools/dev/check-cross.ps1` — clippy for Linux and macOS from Windows (needs Zig, see the
  script); `node tools/extension/e2e.mjs` — the extension in real headless browsers.
- `cargo run -p mdm-labserver -- --faults "rate=2M"` — test server (GET / lists the faults).
- `cargo run -p mdm-app -- --cli get <url> -o <dir>` — headless download with progress (the
  app's program runs the command line; `misterdownloadmanager-cli` is only its launcher).
- `tools/extension/pack.ps1` — build the extension for Chromium and Firefox into
  `target/extension/`; `node tools/extension/test.mjs` — its logic against fake browser APIs.
- `tools/installer/build.ps1` — the Windows installer and portable zip into `target/dist/`.
- `python tools/website/build.py --serve` — the website (and its 21 languages) on 127.0.0.1:8765;
  after changing its English (website/, docs/, CHANGELOG.md), `python tools/website/translate_site.py
  --all` sends only the new or changed texts (`--status` shows what each language lacks).
  `MDM_SITE_PREVIEW=1` builds the English pages with their language picker only (fast).
- Website design goes through the Impeccable skill (`/impeccable`, `.claude/skills/impeccable`):
  product truth in [PRODUCT.md](PRODUCT.md), the visual system in DESIGN.md, the site's
  direction contract in `.impeccable/surfaces/`; its hook checks every website edit.
- `tools/installer/build-linux.sh` / `build-macos.sh` — the Linux (AppImage, tar.gz, .deb, .rpm)
  and the experimental macOS (.dmg) downloads; run by `release.yml` on GitHub's runners.
- Windows: if `cargo` isn't on PATH in an old shell, prefix
  `$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"`.

## Maintainer notes

The maintainer's private notes, when present, add to these rules:

@notes/CLAUDE.private.md
