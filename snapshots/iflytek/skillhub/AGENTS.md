# SkillHub — Agent Entry

SkillHub includes a Java backend, React web UI, CLI and security-scanning integration.
Read [README](./README.md) for setup and [CONTRIBUTING](./CONTRIBUTING.md) for contributions.

## Read before changing code

1. Start with [.trellis/spec/index.md](./.trellis/spec/index.md).
2. Read only the applicable domain index and the topic documents selected by the change.
3. Implementation and review use the same applicable contracts; add the testing guidance for verification.
4. Read actual source, tests, schemas and scripts before treating documentation as implemented behavior.
   Report conflicts and known deviations; do not silently redefine business policy.

| Change | Entry |
|---|---|
| Frontend UI, state, requests, types | [Frontend](./.trellis/spec/frontend/index.md) |
| Backend modules, APIs, persistence, scanning | [Backend](./.trellis/spec/backend/index.md) |
| Tests, CI, acceptance | [Testing](./.trellis/spec/testing/index.md) |
| Configuration, containers, release, migrations | [Deployment](./.trellis/spec/deployment/index.md) |
| CLI | [CLI](./.trellis/spec/cli/index.md) |
| Development, PR, completion | [Workflow](./.trellis/spec/workflow/index.md) |
| Reuse or cross-layer decisions | [Thinking guides](./.trellis/spec/guides/index.md) |

## Core project rules

- The registry is the core product; CLI and agent integrations are entry points.
- Preserve SKILL.md package compatibility and existing namespace/CLI contracts.
- Keep search and object storage behind replaceable interfaces.
- Authentication must remain extensible beyond a single identity provider.
- Changes to publishing, downloading, deletion or authorization must check
  that the required audit trail is preserved.

## Backend essentials

- Controllers handle transport and trusted identity extraction; application
  services orchestrate use cases; domain services own business rules.
- Put complex joins and presentation projections in app query repositories.
  Domain services return domain objects, not app DTOs.
- Domain repository interfaces belong in domain; persistence adapters belong
  in infra. Do not introduce new dependencies that violate module boundaries.
- The existing domain-to-storage dependency is a known deviation, not a
  precedent for adding further cross-module dependencies.
- User identity is String throughout authentication, APIs and persistence.
  This does not imply that every resource ID is String.
- Use existing localized domain exceptions and request-tracing facilities.
- Store API tokens using the existing secure hashing mechanism, never plaintext.

## Frontend essentials

- Use TanStack Query for server state and Zustand/local state for UI state.
  Do not introduce useEffect-based API fetching.
- Reuse existing shared UI components, variants and cn() utilities.
- Use generated API types; do not hand-edit generated schema files.
- Keep user-facing text in translation resources.
- Use console.error for errors and console.warn for deprecation warnings;
  avoid production console.log debugging and never log credentials.

## High-value checks

- For backend app tests, use make test-backend-app, or an equivalent Maven
  invocation that includes -am, to avoid stale dependent-module artifacts.
- API contract changes must check generated types and affected consumers.
- Lifecycle changes must compare docs, source and tests; report disagreements
  rather than silently changing business policy.
- Search changes: read docs/04-search-architecture.md.
- Business-flow changes: read docs/05-business-flows.md.

## Work proportionately

- Small edits: read relevant rules, edit and verify; do not require a task record.
- Multi-step work: use a task record for requirements, context, progress and verification, respecting an existing user choice not to create one.
- Large requirements or architecture changes: OpenSpec owns formal requirements and design; Trellis organizes execution and continuation.
- Repeat critical rules here when they should be visible at session entry.
  Keep detailed contracts in the relevant specs and authoritative documents.
  When changing a repeated rule, check both locations for consistency.
- Each worktree owns its task records. Tracked specs follow the checked-out branch; local template updates are explicit and must not silently overwrite them.

## Verification and delivery

Choose checks using the [change-impact matrix](./.trellis/spec/testing/index.md).
Start with focused feedback; broaden for shared behavior, public interfaces, configuration and integration changes.
Documentation-only changes require relevant document/source checks, not starting the application stack.
Report passed, failed, not-run and environment-blocked checks separately.
A build, unit test, screenshot or static configuration check is not proof of deployment or end-to-end behavior.

Use the existing Makefile and package tooling. Do not hand-edit generated OpenAPI types.
Read commands before execution: staging and schema-drift checks may start/stop services.
Preserve unrelated changes; do not commit, push, publish, deploy or remove worktrees without authorization.
Do not commit or log credentials; do not reset data to make verification pass.

## Sources and maintenance

- Engineering conventions: [.trellis/spec/](./.trellis/spec/index.md).
- Architecture, business semantics and operations: [docs/](./docs/), including [lifecycle](./docs/14-skill-lifecycle.md).
- Formal changes: [OpenSpec workflow](./.trellis/spec/workflow/openspec.md).
- Versions, commands and current behavior: dependency manifests, Makefile, schemas, source and tests.
- Only `.trellis/spec/` is shared in Git. Tasks, runtime state and personal Trellis tooling remain local.
- Execution Skills may help run a workflow; they do not own a second copy of project conventions.
- Preserve and verify existing task records before authorized cleanup; see [archive requirements](./.trellis/spec/workflow/task-archive.md).
