# AGENTS.md

本仓库为 7days-golang 教程文档站点，包含多个 Go 子项目（gee-web、gee-rpc、gee-cache、gee-orm、gee-bolt 等）以及配套的 Markdown 教程文章。

## Git 规范（重要）

- **不要主动 commit**：仅在用户明确确认后才能执行 `git commit`。完成代码修改后，先展示变更内容（`git status` / `git diff`），等待用户确认再提交。
- **Commit message 统一使用英文**：所有提交信息必须使用英文撰写，遵循仓库现有的提交风格（如 `typo: xxx.md`、`Update xxx.md`）。
- 不要主动 push、force-push 或创建 PR，除非用户明确要求。
- 提交前检查 `git status` 和 `git diff`，只暂存（stage）与任务相关的文件，不要提交无关内容或密钥。

## 仓库结构

- `*.md`：教程文章（各系列按 day1/day2/... 组织）
- `gee-*`：各系列对应的 Go 示例项目
- `demo-wasm`、`questions`：演示代码与问答文档

## 修改约定

- 修改文档时保持现有 Markdown 风格与目录结构一致。
- 修改 Go 代码时遵循各子项目现有代码风格，改动后尽量运行对应项目的测试（`go test ./...`）验证。
