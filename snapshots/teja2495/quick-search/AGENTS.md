# Quick Search Agent Guide

Use this file as the repository-specific playbook. Prefer the current code and build files over prose when they disagree.

## Working rules

- Keep changes narrow and preserve unrelated work in the working tree.
- In app action menus, never leave placeholder gaps between options. Reflow items so gaps appear only at the end of the final row when adding or removing an item.
- Do not run automated UI tests unless the user asks. The user normally performs manual UI testing.
- Do not run `git add`, `git commit`, create tags, publish releases, or push without explicit permission.
- Do not mix feature work with speculative refactors or broad cleanup.
- A successful build, install, and launch proves only those steps. Do not claim that a visual state, gesture, keyboard interaction, provider response, or intermittent issue is fixed without reproducing it.

## Current project shape

- Android launcher and unified-search app written in Kotlin with Jetpack Compose and Material 3.
- Architecture: MVVM, unidirectional data flow, `StateFlow`, and immutable state updates.
- Modules: `:app` and the macrobenchmark/baseline-profile module `:benchmark`.
- Distribution flavors: `standard` and `fdroid`. Flavor-specific implementations live in `app/src/standard/` and `app/src/fdroid/`; shared behavior belongs in `app/src/main/`.
- Entry points:
  - regular launches, assistant/search/share/process-text/import flows: `app/MainActivity.kt`
  - launcher HOME role: `app/HomeActivity.kt`
  - draw-over-other-apps mode: `overlay/OverlayActivity.kt`
- Persistence is primarily modular `SharedPreferences`; secrets use the existing encrypted preference path. Notes are stored with Room under `search/data/notes/`. The startup app catalog uses `search/data/AppCache.kt`.

## Architecture map

### Search state and orchestration

- Canonical UI state and section visibility models: `search/core/SearchModels.kt` and `SearchStateModels.kt`.
- Main orchestrator: `search/core/SearchViewModel.kt`; prefer its focused delegates and API files instead of growing the main class.
- Query coordination: `SearchQueryCoordinator.kt`, `UnifiedSearchHandler.kt`, and `searchEngines/SecondarySearchOrchestrator.kt`.
- `SearchSectionRegistry.kt` is the canonical table for search-section ordering, aliases, settings toggles, permissions, and minimum query lengths. Keep coordinated section metadata there.
- Ranking and matching live in `search/common/`, `search/fuzzy/`, and `search/utils/`. Preserve query-version checks, debounce behavior, and stale-result suppression.

### Data and preferences

- Search repositories live in `search/data/`; feature-specific search policies and handlers live in their feature packages.
- Add preferences to the relevant class under `search/data/preferences/`, then expose them through `search/data/userAppPreferences/UserAppPreferences.kt`.
- Startup-critical preference reads go through `StartupPreferencesFacade.kt`. Do not add one-off blocking reads to startup or composables.
- Search history remains in `search/searchHistory/SearchHistoryPreferences.kt`.
- Searchable Quick Search settings are catalogued in `search/appSettings/AppSettingsRepository.kt`; new applicable settings must be wired there as well as in the Settings UI.

### UI and navigation

- Search route/state collection: `search/searchScreen/searchScreen/SearchRoute.kt`.
- Main search composition: `SearchScreen.kt`, `SearchScreenContent.kt`, `SectionRenderingComposables.kt`, and `searchScreenLayout/`.
- Settings routes and destinations: `settings/shared/`, `settings/navigation/`, and feature-specific settings packages.
- Reuse `shared/ui/components/`, `shared/ui/theme/DesignTokens.kt`, and `shared/ui/theme/AppColors.kt`. Account for wallpaper, custom-background, one-handed/bottom-search-bar, tablet, and overlay modes when the changed path is shared.
- Put user-facing strings in resources. When adding or changing copy, update the base file and all 12 localized `values-*` `strings.xml` files unless the user narrows the scope.

### Startup and process-wide caches

- App startup is phased through `app/startup/StartupCoordinator.kt`, `search/core/SearchStartupCoordinator.kt`, and `SearchStartupLifecycleDelegate.kt`. Keep expensive work off the main thread and outside the first visible phase.
- `MainActivity` and `OverlayActivity` share process-wide icon caches. Route lifecycle cleanup through `app/UiSurfaceMemoryManager.kt`; do not clear caches when one surface exits while another is still active.
- Use `clearAppIconMemoryCache()` for memory eviction without forcing displayed icons to refresh. Use `invalidateAppIconCache()` only when an explicit icon change should refresh active UI.

## Feature guides

Read the matching guide before implementing these changes:

| Change | Guide |
|---|---|
| Built-in tool | `app/src/main/java/com/tk/quicksearch/tools/new-tool.md` |
| Search result type or section | `app/src/main/java/com/tk/quicksearch/search/new-search-type.md` |
| Built-in search engine | `app/src/main/java/com/tk/quicksearch/searchEngines/new-search-engine.md` |
| Searchable app-setting row | `app/src/main/java/com/tk/quicksearch/search/appSettings/new-app-setting.md` |
| General preference or Settings UI | `app/src/main/java/com/tk/quicksearch/settings/new-setting.md` |

For a new section, update the model/repository or handler, `SearchUiState`, `SearchSectionRegistry`, orchestration, rendering/order, permission degradation, preferences, and searchable app-setting entry as applicable. For a new tool, also inspect `settings/ToolSettingsRegistry.kt`, `searchEngines/AliasHandler.kt`, and `search/core/SearchToolCoordinator.kt` rather than assuming one integration point.

## Implementation guardrails

- UI reads state and emits events; repositories, handlers, and the ViewModel own business logic and permission-aware behavior.
- Use immutable `copy(...)` updates and existing visibility/loading/result state types.
- Extend existing repositories, policies, registries, and delegates before creating parallel abstractions.
- Keep Android provider work and network work off the main thread. Preserve local-first behavior and do not add analytics or tracking.
- For permission denial, hide or degrade only the affected feature through existing state; never crash or block unrelated search.
- Check both distribution source sets when changing review/update behavior, typography, or distribution defaults.
- If a touched Kotlin file is already very large, place new cohesive logic in a focused file or delegate when that matches the surrounding structure.

## Validation

- Run focused unit tests for changed pure logic. Do not run instrumented/Compose UI tests unless requested.
- If resource XML changes, validate every affected `app/src/main/res/values*/strings.xml` file and run `git diff --check`.
- After every completed coding task, always run this exact command from the repository root outside the sandbox before considering the task complete:

```bash
./gradlew assembleStandardDebug && adb install --user 0 -r app/build/outputs/apk/standard/debug/app-standard-debug.apk && adb shell am force-stop com.tk.quicksearch && adb shell am force-stop com.tk.quicksearch.debug && adb shell am start -W -n com.tk.quicksearch.debug/com.tk.quicksearch.app.MainActivity
```

- If any part fails, diagnose it and rerun the full command until it succeeds. If completion is impossible because no device is connected or the environment is blocked, report that boundary plainly instead of claiming completion.
- For Gradle cache permission/lock failures, use the project-local cache with `GRADLE_USER_HOME=$PWD/.gradle-codex`. For Kotlin daemon marker failures, also use `-Pkotlin.compiler.execution.strategy=in-process`.
- Manually verify only what the change affects: empty and non-empty queries for search work, typo/acronym behavior for matching work, permission-off states for protected data, persistence after restart for settings, and standard/wallpaper/overlay surfaces for shared UI. Leave actual manual UI execution to the user unless asked.

## Release safety

- Standard releases include Play review/update integrations; F-Droid substitutes flavor-local implementations without Play libraries.
- For F-Droid work, read `docs/FDROID.md` and the `fdroid-release` skill when available.
- Treat version tags as immutable. Before any authorized publish, align version name/code, release notes/changelog, artifact, and tag, then verify the remote result.

---

Last audited against the repository: 2026-08-13
