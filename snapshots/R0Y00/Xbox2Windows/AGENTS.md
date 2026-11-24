# AGENTS.md

This file is for coding agents working in Xbox2Windows. Read `CONTRIBUTING.md` and
`docs/experiments.md` before changing behavior. If this file conflicts with those
documents, they take precedence.

## Project

Xbox2Windows is a static-recompilation research project for Xbox Series X|S
(Scarlett) software on x64 Windows. The CPU experiments translate source-built
x64 functions from PE machine code through C++ to Windows DLLs. The shader
experiments translate selected gfx1013 programs to desktop DXIL. The repository
also contains Windows runtime shims, PE tooling and reproducible fixtures.

This is not a full emulator and not a playable port. Execution of the title's
CPU code, full-game startup and frame rate remain unverified. Do not claim
otherwise.

## Hard rules

- Never add game files, dumps, DLLs, EXEs, torrents, distribution links or
  credentials to the repository, issues or pull requests.
- Keep public project wording title-neutral, including the repository
  description and README. Describe results in terms of the platform, component
  or fixture tested. Do not claim that a game runs.
- Use only source-built fixtures, synthetic inputs or public samples with a
  known revision and license.
- Keep generated output under `out/` and local inputs under `game-files/`.
  Both directories are gitignored.
- Do not weaken or delete tests to make a change pass.
- One pull request should cover one reviewable behavior. Do not mix unrelated
  refactors, formatting changes or dependency updates.
- Original contributions are submitted under the MIT License. Preserve
  applicable third-party notices.

## Platforms

The full build, Windows runtime tests, D3D12 tests, MASM fixtures and GPU tests
require x64 Windows with Visual Studio's Desktop development with C++ workload,
the Windows SDK, CMake/Ninja, DXC and Python 3.11 or newer.

`dxc_compile_time_gvn` measures pass attribution through `-ftime-report`, which
arrived in DXC 1.7.2212 (December 2022). The 1.6 build that ships with Windows
SDK 10.0.22621 has no such flag, so that test reports a capability skip (77)
instead of failing.

The Ubuntu CI job assembles and translates gfx1013 fixtures with LLVM 15. The
pure-Python checks listed below also run on Linux and macOS. Do not stub D3D12,
MASM or `cl` to make the CMake configure succeed on another platform.

## Build on Windows

Install the Desktop development with C++ workload, including x64 MSVC, the C++
CMake tools with Ninja, the Windows SDK and DXC. From a PowerShell prompt at the
repository root:

```powershell
.\tools\dev.ps1
cmake --preset dev
cmake --build --preset dev
ctest --preset dev --no-tests=error -R 'desktop_root_signature|era_heap_allocation|offscreen_warp'
```

For the script, shader, texture and PE fixture tests, create the Python
environment before configuring:

```powershell
python -m venv out/pe-env
.\out\pe-env\Scripts\python.exe -m pip install -r requirements-dev.txt
cmake --preset dev
cmake --build --preset dev
ctest --preset dev --no-tests=error
```

`CMakeLists.txt` uses `INTAKE_PYTHON` for the Python-driven tests. Its default is
`out/pe-env/Scripts/python.exe`.

## Tests

List the registered tests with `ctest --preset dev -N`. Use
`--no-tests=error` when checking a new filter so an empty selection fails.

| Area | Command |
|---|---|
| CPU translation | `ctest --preset dev --no-tests=error -R '^cpu_' -V` |
| Script states | `ctest --preset dev --no-tests=error -R '^script_(state_literals\|path_links)$' -V` |
| Textures | `ctest --preset dev --no-tests=error -R '^(bcpack_prefix_and_mip_tail\|bc7_tile_swizzle\|bc7_draw_warp\|texture_bc_volume)$' -V` |
| Shader translation | `ctest --preset dev -R '^pixel_aot_' -V` |
| D3D12 and ray tracing | `ctest --preset dev -R '^bvh_(differential\|wave64)_hardware$' -V` |
| Windows runtime | `ctest --preset dev -R 'era_heap\|desktop_memory_query'` |
| PE tooling | `ctest --preset dev -R 'static_exe_intake\|conditional_import_paths'` |

Tests ending in `_warp` use Microsoft WARP. Tests ending in `_hardware` use a
physical GPU and may return 77 (capability skip). A skip is not a pass and not a
failure; report it separately. GPU reports must identify the adapter, driver,
Windows build, commit and debug-layer status.

## Pure-Python checks

These checks do not need Windows, D3D12 or game files. The list matches the
platform-independent Python job in `.github/workflows/windows.yml`:

```bash
python3 -m venv out/pe-env
./out/pe-env/bin/python -m pip install -r requirements-dev.txt
./out/pe-env/bin/python -B tests/script_state_check.py
./out/pe-env/bin/python -B tests/resource_root_check.py
./out/pe-env/bin/python -B tests/bcpack_check.py
./out/pe-env/bin/python -B tests/bcpack_symbols_check.py
./out/pe-env/bin/python -B tests/bcpack_tables_check.py
./out/pe-env/bin/python -B tests/bc7_blocks_check.py
./out/pe-env/bin/python -B tests/bc7_tiles_check.py
./out/pe-env/bin/python -B tests/gfx10_texture_roundtrip_check.py
./out/pe-env/bin/python -B tests/texture_bc_volume_check.py
./out/pe-env/bin/python -B tests/form_coverage_check.py
./out/pe-env/bin/python -B tests/resource_ranges_check.py
./out/pe-env/bin/python -B tests/ttpf_batch_export_check.py
./out/pe-env/bin/python -B tests/awc_metadata_check.py
./out/pe-env/bin/python -B tests/sgd5_effects_check.py
./out/pe-env/bin/python -B tests/dxcontainer_part_offsets_check.py
./out/pe-env/bin/python -B tests/layout_chunks_check.py
./out/pe-env/bin/python -B tests/dependency_paths_check.py
./out/pe-env/bin/python -B tests/pe_package_preflight_check.py
./out/pe-env/bin/python -B tests/host_commit_check.py
./out/pe-env/bin/python -B tests/pe_package_ordinal_plan_check.py
./out/pe-env/bin/python -B tests/compat_report_check.py
./out/pe-env/bin/python -B tests/intake/paths_check.py
./out/pe-env/bin/python -B tests/intake/routing_check.py
./out/pe-env/bin/python -B tests/intake/import_forms_check.py
./out/pe-env/bin/python -B tests/shader_probe_check.py
./out/pe-env/bin/python -B tests/shader_census_check.py
./out/pe-env/bin/python -B tests/shader_corpus_report_check.py
./out/pe-env/bin/python -B tests/dxil_retarget_check.py
./out/pe-env/bin/python -B tests/rdna2_tools_check.py
./out/pe-env/bin/python -B tests/pso_readiness_check.py
./out/pe-env/bin/python -B tests/xmem_attribute_scan_check.py
./out/pe-env/bin/python -B tests/xgameruntime_table_check.py
./out/pe-env/bin/python -B tests/docs_links_check.py
./out/pe-env/bin/python -B tests/bidi_controls_check.py
./out/pe-env/bin/python -B tests/gpu_report_format_check.py
./out/pe-env/bin/python -B tests/hardware_reports_check.py
./out/pe-env/bin/python -B tests/rectlist_topology_check.py
./out/pe-env/bin/python -B tests/startup_sampler_heap_check.py
./out/pe-env/bin/python -B tests/startup_image_sample_l_check.py
./out/pe-env/bin/python -B tests/startup_image_3d_check.py
./out/pe-env/bin/python -B tests/startup_image_load_mip_check.py
./out/pe-env/bin/python -B tests/startup_image_2d_array_check.py
./out/pe-env/bin/python -B tests/startup_host_cpu_check.py
./out/pe-env/bin/python -B tests/startup_translator_check.py
./out/pe-env/bin/python -B tests/startup_flat_param_check.py
./out/pe-env/bin/python -B tests/startup_inline_sampler_check.py
```

`tests/pixel_aot_check.py binary` additionally needs LLVM with gfx1013 support
and the local `llvm-mc`, `llvm-objcopy` and `libLLVM` paths. CI uses LLVM 15;
newer versions may print a different `exp` spelling.

## Repository map

| Path | Purpose |
|---|---|
| `src/` | Windows runtime shims and shared shader helpers. |
| `tools/` | Offline translators, PE/image probes and inventory tools. |
| `tests/` | C++, HLSL, MASM and Python fixtures. `tests/cpu/` holds the PE fixtures. |
| `docs/experiments.md` | Measured results, assumptions and reproduction commands. |
| `game-files/` | Local inputs; gitignored. Never commit or upload. |
| `out/` | Build, generated sources and reports; gitignored. |

## Evidence

A change is ready when another contributor can reproduce it. Include:

- the commit or build under test;
- the exact command;
- the observed result and the expected result;
- the environment for hardware or driver-dependent results;
- the first mismatch or diagnostic for a failure;
- any capability skip, separate from passes and failures;
- a negative control or failure case for a new fixture.

State what was measured and what remains a hypothesis. A passing fixture supports
the behavior under test; it does not establish full-game startup.

## Pull requests

- Create a topic branch from current `main` in your fork.
- Use a focused branch name, for example `docs/agents-guide` or
  `bcpack/stride-6-diagnostic`.
- Link the issue with `Refs #123` or `Fixes #123` when the completion condition
  is met.
- Update the relevant README row or `docs/experiments.md` when a public
  capability, build requirement or reproduction command changes.
- Include the exact test command and result in the PR body.
- Do not include game files, dumps, distribution links or secrets.

## First places to look

- `README.md#choose-an-experiment`
- `CONTRIBUTING.md`
- `docs/experiments.md`
- Open issues labeled `help wanted` and `good first issue`.
