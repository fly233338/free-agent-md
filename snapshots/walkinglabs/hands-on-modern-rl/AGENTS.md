# Repository Guidelines

## Project Structure

- `docs/`: VitePress course site content.
- `docs/.vitepress/`: site configuration and theme overrides.
- `docs/public/`: static assets copied to the final site.
- `docs/en/`: English translation stubs (mirror of Chinese structure).
- `code/`: runnable Python experiments aligned with chapters.
- `scripts/`: repo maintenance scripts such as sitemap, verification, and asset optimization.
- `.github/workflows/`: deployment workflow for GitHub Pages.

## Commands

```bash
npm install
npm run dev            # dev server with asset optimization
npm run dev:fast       # dev server skipping asset optimization (~5s startup)
npm run build
npm run preview
npm run verify
npm run assets:optimize
```

## Editing Rules

- Keep changes scoped. Do not rewrite unrelated docs or config.
- Prefer adding new course material under `docs/` and updating sidebar/nav in `docs/.vitepress/config.mjs`.
- Run `npm run verify` before pushing if you touched config, theme, or build scripts.
- When adding/moving/renaming pages, update both Chinese and English sidebars if applicable.

## TikZ → SVG Workflow

For academic-style diagrams with proper LaTeX math rendering:

1. Write the diagram as a `standalone` TikZ document (see `docs/preface/images/actor-critic.tex` for style reference)
2. Compile: `xelatex <file>.tex && pdf2svg <file>.pdf <file>.svg`
3. Keep both `.tex` (source) and `.svg` (output) in the same `images/` directory
4. Reference the `.svg` from markdown with `<img src="./images/<name>.svg">`

Style: rounded-corner boxes (`draw=black!70, fill=black!3`), Stealth arrows, Songti SC font, `$...$` for math.

## Writing Conventions

- Write docs as tutorial and lecture material, not as terse reference notes.
- **Direct and concise**: No guiding filler like "用...做解释会更直观". Present the example or formula directly.
- **No redundancy**: Avoid saying the same thing twice in different words.
- **No vague qualifiers**: Replace metaphors ("相当于...") and hedging ("由于...") with precise causal statements.
- **Follow the causal line**: Do not circle around the same point with "first summarize, then restate, then contrast". Write in the order the idea actually changes: new capability or setting appears → it changes the training/problem object → this enables or forces a new formulation.
- When opening a new concept, prefer the pattern "有了新的 X，系统会 Y，于是可以/必须 Z". Avoid unnecessary callbacks to previous chapters unless they are needed for the next sentence.
- Avoid slogan-like summary phrases such as "一问一答一打分", "骨架始终未变", "系统地扩展", or "完全不涉及". State the concrete mechanism instead.
- Avoid AI-like error lists. Instead of listing many parallel mistakes ("query 太宽、没比价、库存错、参数错"), describe the process and show how an early wrong state propagates into later actions.
- Prefer Chinese terms in Chinese prose. Use "一段回答" instead of "completion", "奖励" instead of "reward", "动作掩码" instead of "action mask", "逐步记录/逐步优势" instead of "step-level record/advantage". Keep English only when it is a standard acronym or the local chapter title requires it, and explain it in Chinese.
- Match the narrative style of Chapter 3.1 and 3.2: conversational, patient, and problem-driven.
- Open sections by connecting to what the learner already knows, then name the new problem the section solves.
- Use concrete scenes before abstractions: examples like CartPole, multi-armed bandits, LLM generation, game tasks, and everyday choices should make the concept feel necessary.
- Prefer a guided lecture voice. Use phrases like "Let's start with the intuition", "Look at it from another angle", "What this step means is…", "The real issue is…", while keeping the tone serious and precise.
- Maintain textbook prose for course material. Avoid chatty, assistant-like, slogan-like, or casual internet phrasing; write as a polished Chinese textbook chapter.
- Ensure every conceptual step has a textbook-style transition. Do not jump directly from a definition to a formula, term, algorithm, or conclusion; explain why the next idea is needed before introducing it.
- Avoid encyclopedia-style exposition that only lists definitions. Definitions should appear after motivation and should be followed by interpretation.
- Keep formulas close to their meaning: explain every important symbol, then restate the formula in plain English.
- Avoid the "不是……而是……" / "not A, but B" contrast pattern. It makes the prose feel indirect. State the positive claim directly, then explain the reason.
- Let paragraphs flow from question to answer. Good sections often follow this rhythm: familiar example → confusion or tension → formal tool → worked example → takeaway.
- Use bold sparingly to mark conceptual pivots, not decoration.
- Explain ideas progressively: intuition first, then formal definitions, then code or practice.
- Prefer learner-facing prose in Chinese, with concrete examples, small derivations, and explicit transitions.
- When introducing formulas or algorithms, state what problem they solve before showing the notation.
- Keep paragraphs teachable and paced for reading aloud or self-study.
- Use short sections and explicit headings.
- Use kebab-case for paths under `docs/`.
- Prefer directory-based routes with `index.md`.

## Commit Style

- Use Conventional Commits such as `feat:`, `fix:`, `docs:`, `chore:`.
