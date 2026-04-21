# PERT+ Developer Guide

This document is for contributors who want to maintain, extend, or refactor PERT+ over time.

The user-facing documentation explains how to run the app. This guide explains how the app is put together, how new functionality should be added, and what conventions the current codebase expects contributors to follow.

## Purpose

PERT+ is a PySide6 desktop application that wraps a set of simulation and analysis workflows into a single GUI while keeping the original source artifacts in the wider workspace untouched.

At a high level, the application is built from four layers:

1. Application bootstrap and persistent settings
2. UI panels and shared widgets
3. Background job execution
4. Engine modules that perform the actual work

## Project Structure

Core directories under `Unified_App/`:

- `app.py`: application entry point
- `config/`: persistent settings wrapper and config helpers
- `engine/`: workflow logic for simulation, analysis, graphics, clustering, PCA, and related tasks
- `ui/`: main window, panels, theme, and reusable widgets
- `worker/`: threaded job runner and queue management
- `tools/`: maintenance scripts such as sample output regeneration
- `sample_outputs/`: canonical reference outputs for packaged/open-source distribution

Important top-level documents:

- `README.md`: user-facing overview
- `QUICK_START.md`: user runbook
- `TROUBLESHOOTING.md`: user troubleshooting
- `SETTINGS_REFERENCE.md`: user-facing setting definitions
- `DEVELOPER_GUIDE.md`: contributor-facing architecture and extension guide

## Runtime Architecture

### Application bootstrap

The application starts in `app.py`.

Startup flow:

1. Configure Qt high-DPI scaling policy.
2. Create `QApplication`.
3. Detect portable mode by checking for `settings.ini` next to the executable.
4. Create the shared `Settings` instance.
5. Apply the persisted theme.
6. Create and show `MainWindow`.

Portable mode matters for contributors because the app supports both:

- normal platform-backed `QSettings`
- local `settings.ini` storage beside the executable

### Main window and navigation

`ui/main_window.py` owns the shell of the application.

Responsibilities:

- Create toolbar and status bar
- Register the sidebar navigation items
- Instantiate one panel per workflow
- Share a single `JobManager` across panels
- Clean up temporary graphics sessions on app close

Navigation is driven by the `_NAV_ITEMS` table. When adding a new workflow panel, this is the central registration point.

### Panel model

Most workflows are represented as subclasses of `BasePanel`.

`BasePanel` provides:

- Standard page header
- Scrollable form area
- Shared progress/log panel
- `run_job()` dispatch into a worker thread
- Shared status and error handling
- Automatic compaction of per-panel Output group boxes

Every normal panel must define:

- `_build_form()`
- `_collect_kwargs()`
- `_engine_fn()`

Panels should stay thin. They are responsible for collecting inputs, persisting relevant settings, and delegating actual work to engine functions.

### Background execution

`worker/job_runner.py` contains two core pieces:

- `JobWorker`: a `QThread` wrapper for a single engine call
- `JobManager`: a single-job-at-a-time queue manager

The worker injects two optional callbacks into engine functions when the engine signature supports them:

- `progress_cb(current, total, message)`
- `cancel_check()`

This means engine functions should accept these callbacks whenever their work is long-running enough to benefit from progress reporting or cancellation.

### Settings model

`config/settings.py` is a typed wrapper around `QSettings`.

Contributors should prefer adding typed properties here rather than scattering raw settings keys through UI code. This keeps defaults, validation, and persistence behavior centralized.

Current settings categories include:

- theme
- recent input/output directories
- simulation defaults
- clustering defaults
- PCA defaults
- effect-size defaults
- batch defaults
- graphics DPI

## Engine Conventions

The `engine/` package contains workflow logic. These modules are intentionally structured so they can be called from the UI or from maintenance scripts.

General conventions used by current engines:

- Accept concrete input paths as strings or `Path` values where practical
- Accept `progress_cb` and `cancel_check` for long-running tasks
- Return a path or a small result object that the UI can interpret
- Keep file writing inside the engine layer rather than the panel layer
- Raise exceptions normally; UI error handling is centralized in the panel/worker layer

Examples:

- simulation writes batch CSV outputs
- analysis writes CSV and JSON summaries
- graphics engines write PNGs and return their output directory
- clustering writes row-level CSV, summary CSV, and JSON summary

## Graphics Workflow Architecture

Graph/image workflows now use a shared temp-preview architecture so the behavior is consistent and scalable.

### Core classes

- `ui/panels/image_preview_panel.py`
- `ui/widgets/generated_image_preview.py`

### Why this exists

Earlier graphics behavior was panel-specific and saved images directly to user-selected folders. The current design centralizes preview/export behavior so new panels do not have to reimplement it.

### Current graphics rules

- Image outputs are generated to a temp directory first.
- The UI previews generated images inside the panel.
- `Save Graphics` exports image and HTML artifacts to a user-selected auto-named subfolder.
- `Don't Save` deletes the temp graphics session.
- Temp graphics are also cleared on regenerate and on app close.
- Non-image analysis artifacts such as CSV/JSON may still auto-save immediately when the workflow needs them.
- HTML artifacts are not previewed in-panel.
- Complexity Visualizer HTML is export-only and not auto-saved.

### Extension points for future graphics panels

If a new panel produces image artifacts, prefer subclassing `ImagePreviewPanel` instead of `BasePanel` directly.

Shared helper methods:

- `_build_graphics_output_group(...)`
- `_add_generate_and_preview(...)`
- `_temp_output_dir_str()`
- `_autosave_non_image_to_picker(...)`

These helpers are the preferred path for future graphics workflows.

## Workflow Categories

The current workflows fall into three broad categories.

### 1. Pure data-output workflows

Examples:

- Monte Carlo Simulation
- Batch Simulation
- Percent-Error Analysis
- Complexity Measures
- Build RCP

These primarily produce CSV, JSON, or RCP files and typically use `BasePanel` directly.

### 2. Graphics-preview workflows

Examples:

- Path Generator
- Error Graphics
- Cluster Graphics
- PCA Analysis
- Cluster Effect Sizes
- Complexity Visualizer

These use `ImagePreviewPanel` because they generate previewable image artifacts.

### 3. Hybrid workflows

Examples:

- PCA Analysis
- Cluster Effect Sizes

These generate both:

- auto-saved structured outputs such as CSV
- temp-preview graphics that are explicitly exported by the user if desired

## Adding A New Workflow

Recommended checklist for a new contributor.

### Add a new engine function

Place the main logic in `engine/` and keep it callable outside the UI.

Prefer a signature like:

```python
def run_new_workflow(
    input_path: Path,
    output_dir: Path | None = None,
    progress_cb: Optional[Callable] = None,
    cancel_check: Optional[Callable] = None,
) -> Path:
    ...
```
```

### Add a panel

- Use `BasePanel` for non-graphics workflows.
- Use `ImagePreviewPanel` for image-producing workflows.

Panel responsibilities should stay limited to:

- building controls
- collecting kwargs
- saving user defaults where appropriate
- handling any UI-specific interpretation of results

### Register the panel

Add the new panel class to `_NAV_ITEMS` in `ui/main_window.py`.

### Update documentation

At minimum, update:

- `README.md`
- `QUICK_START.md` if user flow changes
- `TROUBLESHOOTING.md` if there are new failure modes
- `SETTINGS_REFERENCE.md` if new persistent settings are introduced
- `DEVELOPER_GUIDE.md` if the architectural pattern changes

## Contributor Conventions

### Keep UI thin

Do not move heavy data processing into panel classes. Business logic belongs in `engine/`.

### Preserve reusable patterns

If a new feature fits an existing shared abstraction, extend that abstraction rather than cloning logic into another panel.

Examples:

- Use `ImagePreviewPanel` for graphics workflows
- Use `Settings` typed properties instead of ad hoc `QSettings` keys
- Use `JobWorker` progress/cancel callbacks instead of ad hoc threading

### Return structured results when helpful

Where an engine produces multiple artifacts, prefer returning:

- an output directory path, or
- a small dict with stable keys such as `output_dir` and `image_paths`

This makes panels easier to keep generic.

### Keep sample outputs reproducible

Canonical reference outputs are maintained in `sample_outputs/` and regenerated by:

```powershell
conda activate path_gen_build
python Unified_App/tools/regenerate_sample_outputs.py
```

If a workflow changes in a way that materially changes expected outputs, contributors should regenerate these samples and update any documentation that refers to them.

## Validation Strategy

The project does not currently rely on a formal pytest-style test suite. Instead, validation is based on:

- targeted engine execution
- UI smoke tests
- canonical sample output regeneration

Useful validation patterns:

- run the app offscreen to verify construction and close behavior
- run individual engine functions against known-good inputs
- regenerate `sample_outputs/` and confirm one canonical set exists per workflow

This is pragmatic, but contributors should consider adding formal automated tests over time where coverage is worth the maintenance cost.

## Known Architectural Tradeoffs

Current design tradeoffs that future contributors should know about:

- `JobManager` serializes panel jobs globally, so only one workflow runs at a time from the UI.
- Thread force-stop uses `QThread.terminate()`, which is a last-resort mechanism and not ideal for graceful cleanup.
- Some workflow sample inputs live outside `Unified_App/`, so packaging and validation still depend on broader workspace artifacts unless dedicated fixtures are added later.
- The UI uses direct panel instantiation in `MainWindow` rather than a plugin/discovery model.

These are acceptable for the current project scale, but they are natural future refactor targets.

## Recommended Future Improvements

If the project grows, these are high-value next steps:

1. Add automated engine-level tests for core workflows.
2. Introduce stable fixture data inside the app repository rather than depending on external workspace paths.
3. Consider a panel registration/plugin pattern if the number of workflows grows substantially.
4. Replace force-stop termination with more graceful cancellation where feasible.
5. Add lightweight CI checks for sample output regeneration or selected engine smoke tests.

## Maintenance Rule For This Document

Treat this file as a living architecture record.

When contributors change any of the following, they should update this document in the same change set:

- shared workflow patterns
- panel/engine extension conventions
- output lifecycle behavior
- settings architecture
- contributor workflow expectations