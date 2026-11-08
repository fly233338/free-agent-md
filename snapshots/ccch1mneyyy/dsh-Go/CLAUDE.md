# AGENTS.md

dsh-Go 是 DeepSeek Harness 的 Android 手机应用：Flutter 原生界面 + 纯 Dart 客户端 + 打过补丁的 DSH 引擎运行时（在 PRoot 里运行 `dsh web`）。改动前先读 [CONTRIBUTING.md](CONTRIBUTING.md)（贡献与验证契约）与 [docs/architecture.md](docs/architecture.md)。

## 仓库布局

```
app/                         Flutter App：原生界面、Riverpod 状态、l10n、手机操控
app/lib/l10n/parts/          界面文案的中英文 ARB 输入
packages/dsh_client/         纯 Dart 客户端：HTTP/SSE、mux、会话与删除 API
packages/dsh_remote/         远程传输：WebRTC / LAN / TURN / 中继
runtime/                     打补丁的 DSH 引擎运行时
runtime/bridge/dsh-go-bridge/  App ↔ 引擎的 HTTP 桥（/dsh-go/v1/*，含会话删除路由）
runtime/patches/             引擎补丁及其 pins.json（补丁与版本钉死）
sdk/plugin-kit/              插件 SDK
tooling/                     APK 构建与构建号脚本
docs/                        架构、发布、路线图、用户指南
```

## 命令

按改动面选择验证，在 PR/报告里写实际执行的命令和结果。完整说明见 [CONTRIBUTING.md](CONTRIBUTING.md)。

```bash
(cd app && flutter pub get && flutter analyze && flutter test)   # Flutter 应用
(cd packages/dsh_client && dart pub get && dart analyze && dart test)
(cd packages/dsh_remote && dart pub get && dart analyze && dart test)
(cd sdk/plugin-kit && npm install && npm test)
node --test runtime/tests/*.test.mjs                               # 引擎桥/补丁测试
python3 app/tool/l10n_merge.py --check                             # 文案生成检查
python3 app/tool/guide_sync.py --check                             # 用户指南同步检查
tooling/build-apk.sh --build-name <x.y.z>                          # 构建 APK
```

CI（`.github/workflows/ci.yml`）在 PR 上跑通用检查和改动涉及的部分，在 `main` 上跑全量，结果看 `CI OK`。它不碰真机和真实账号，绿了不等于手机上没问题。

## 硬规则

### 不接受外部 PR（最高优先级）

- 本仓库**暂不接受任何外部 Pull Request**（代码、文档、配置、模板都不收）。
- **禁止合并任何外部 PR**：不得用 `gh pr merge`、GitHub API、网页合并、rebase 或 cherry-pick 把外部提交带进 `main`。
- **禁止替用户创建 PR**，除非用户在当次对话里明确要求。
- 收到外部 PR：关闭它并回复"暂不接受外部 PR，请改用 issue 提供建议"。入口检查（`.github/workflows/pr-gate.yml`）会自动关闭外部 PR；人工按同一政策处理，不要"先合并再说"。
- 不要因为某个 issue 有了实现，就自动把实现包装成 PR 合入。

### 源码、生成物与运行时补丁

- 不手改生成物：`app/build/`、`.dart_tool/`、生成的 l10n 产物等；改输入后运行对应生成器。
- 界面文案改 `app/lib/l10n/parts/*.arb`，中英文同步，再跑 `python3 app/tool/l10n_merge.py`；不要手改生成结果。
- 用户指南改 `docs/guide/`，再跑 `python3 app/tool/guide_sync.py`。
- 引擎补丁在 `runtime/patches/`：补丁文件与 `pins.json` 保持同步，不手改正被补丁覆盖的产物。
- 插件教学技能改 `sdk/plugin-kit/skill/` 或 SDK 对应输入，再跑 `node sdk/plugin-kit/scripts/sync-skill.mjs`。

### 行为与契约

- 客户端、桥接、插件协议的改动，同时检查另一端的调用方与向后兼容。
- 危险操作（删除会话、权限、凭据）以主机/引擎的实际回答为准，不用本地推断代替；失败要有稳定错误码，不静默吞掉。
- 界面文案中英两版同步（`app/lib/l10n/parts/*.arb` 与对应 `.en.arb`）。
- 双语文档同步：README、CONTRIBUTING、SECURITY、docs/guide 中英两版同步。

### 凭据与隐私

- 不记录、不回显、不持久化完整 API key、token、cookie、登录态。
- 诊断包和日志外发前人工检查；自动打码不能当成保证。

### Git 安全

- 开工前先检查工作树、分支和上游状态，并 `git fetch origin main`；默认从最新 `origin/main` 建立隔离工作分支，不在陈旧分支上直接叠加新任务。已有未提交改动时不得为同步而自动 reset、stash 或覆盖。
- 工作提交并合并后，必须清理本次创建的临时工作树与分支；清理前确认提交已合入目标、没有未保存或未推送的成果。不强制删除含改动的工作树，不删除其他任务的分支。
- 合并及清理后，再获取最新 `main`，在干净的主工作树内仅用 fast-forward 同步，并报告最终提交与未清理事项；主工作树有无关改动时保留并说明，不能为了制造“干净”而丢失工作。
- 只暂存明确路径，不用 `git add .` / `git add -A`。
- 未经要求不 commit、不 push、不打 tag、不发布。
- 不 force push `main` 或重写共享历史，除非用户在当前对话里明确要求；重写后必须重建受影响的分支与 PR。

### 真机验证

- Flutter widget 测试需要对应架构的 Flutter 引擎；只有桌面端（x86_64）而设备是 arm64 时，明确写"未运行"及原因。
- 手机操控、PRoot、直接启动、更新安装相关改动必须在真机上验证；桌面结果不能替代。

## 代码审查原则

审查 PR 或改动时，以**不引入新 Bug、最小必要改动、保持代码简洁**为核心：

1. **防止回归**：优先检查新增 Bug、竞态、资源泄漏、性能退化、兼容性问题，特别关注共享层（`packages/dsh_client`、bridge、runtime 补丁）对既有主机连接方式的影响。
2. **避免过度设计**：识别重复实现、无必要的抽象、冗余封装和过度防御性编程；只在存在更简单等效方案时报告，不误判必要的安全校验和错误处理。
3. **严格控制范围**：改动应围绕目标与关联 issue，不夹带无关重构、格式化、依赖升级或其他功能修改；必要的测试和文档同步除外。
4. **保证实质价值**：关注无效代码、重复逻辑、无意义拆分和缺乏有效断言的测试；不以代码行数或提交次数判断贡献，不推测贡献者动机。
5. **审查必须有据**：只报告本次改动引入的实质问题，说明具体位置、触发条件和实际影响，优先给最小修复建议。

## 技能与流程

- 内部 PR：走 `.agents/skills/pr`（流程、模板、验证记录）。
- 代码审查：走 `.agents/skills/review`（证据优先，只报本次改动引入的实质问题）。
- 缺陷报告：`.agents/skills/bug`；安全审计：`.agents/skills/vuln-check`；大范围审计：`.agents/skills/audit`。

## 编辑本文件

`CLAUDE.md` 是指向 `AGENTS.md` 的符号链接；编辑真身。每条规则保持自包含，细节链接到权威文档。
