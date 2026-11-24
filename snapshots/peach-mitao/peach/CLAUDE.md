@AGENTS.md

## Claude 专有：不要用内置的工作树机制

工作树用 `scripts/agent_worktree.py create`；流程与目录失效判据见
`.claude/skills/peach-worktree/SKILL.md`，残留由 `tests/test_repo_hygiene.py` 检查。
桌面端建好工作树（含兄弟仓库的）后，立即用 `request_directory` 把目录加进会话，侧栏才能打开其中文件。
