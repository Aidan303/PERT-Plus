# PERT+

PERT+ is a PySide6 desktop application that wraps the copied simulation and analysis workflows from this workspace into a single GUI. It keeps the original source files untouched and runs the adapted logic from the `Unified_App` package only.

## Short Guides

- Quick start: `QUICK_START.md`
- Troubleshooting: `TROUBLESHOOTING.md`
- Settings reference: `SETTINGS_REFERENCE.md`
- Developer guide: `DEVELOPER_GUIDE.md`

## What It Includes

- Monte Carlo simulation for one or more `.rcp` files
- Batch simulation across folders of `.rcp` files
- Single-distribution selection (Beta, Triangular, or Lognormal) in simulation and batch panels
- Percent-error analysis for simulator batch CSV output
- Error graphics from analysis summary JSON files
- Clustering analysis, cluster graphics, and cluster effect-size analysis
- PCA analysis and complexity visualization
- Path generator network visualization with critical path highlighting for one or more RCPs
- Direct complexity-measure extraction from `.rcp` files
- Excel-to-RCP conversion
- Persistent preferences, theme toggle, fixed-seed controls, and best-effort cancel / force-stop controls

## Requirements

- Python 3.12 recommended
- Conda environment used during validation: `path_gen_build`
- Python packages from `requirements.txt`

Install dependencies into the target environment:

```powershell
conda activate path_gen_build
pip install -r requirements.txt
```

If you are using conda for Qt packages, avoid mixing pip-installed and conda-installed `PySide6` packages in the same environment.

## Run

From the `Unified_App` folder:

```powershell
conda activate path_gen_build
python app.py
```

## Build Release (Reusable Script)

From the `Unified_App` folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1
```

Default behavior:

- cleans `build/` and `dist/`
- builds a one-file executable (`PERT+.exe`)
- creates a cleaned release folder at `release/PERT+_windows_x64`
- copies the executable and user docs into the release folder
- writes `SHA256SUM.txt` in the release folder
- removes `dist/` and `build/` after packaging

Common options:

```powershell
# Keep dist/ after packaging
powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1 -KeepDist

# Keep build/ after packaging
powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1 -KeepBuild

# Build with a different conda environment name
powershell -ExecutionPolicy Bypass -File .\tools\build_release.ps1 -CondaEnvName my_env
```

## Portable Settings

PERT+ supports a simple portable mode. If a `settings.ini` file exists next to the executable, the app stores its settings there instead of using the normal platform settings location.

This affects:

- theme selection
- recent input and output directories
- default simulation values
- clustering, PCA, effect-size, graphics, and batch defaults

## Panels And Expected Inputs

Use the left sidebar to switch between the 12 workflows.

| Panel | Primary Input | Primary Output |
| --- | --- | --- |
| Monte Carlo Simulation | One or more `.rcp` files | Simulator batch CSV for the selected single distribution |
| Percent-Error Analysis | Simulator batch CSV | Analysis CSV and summary JSON |
| Error Graphics | Analysis JSON file or folder of JSON files | Temporary PNG chart preview session; optional Save Graphics export |
| Clustering Analysis | Simulator master CSV with complexity and distribution flags | Cluster summary, row-level cluster CSV, tree diagnostics |
| Cluster Effect Sizes | `network_clusters_row_level.csv` | Autosaved effect-size CSV + temporary forest-plot preview session |
| Cluster Graphics | `cluster_summary.csv` | Temporary PNG chart preview session; optional Save Graphics export |
| PCA Analysis | Feature matrix CSV | Autosaved PCA CSV outputs + temporary plot preview session |
| Complexity Visualizer | CSV with complexity columns such as `SP`, `TF`, `AD`, `LA` | Temporary PNG preview session; optional Save Graphics export for PNG/HTML |
| Complexity Measures | One or more `.rcp` files | Complexity metrics output |
| Path Generator | One or more `.rcp` files | Temporary PNG preview session with carousel; optional Save Graphics export |
| Batch Simulation | Folder of `.rcp` files | Batch simulator CSV for the selected single distribution |
| Build RCP | Excel workbook | `.rcp` file |

Important schema note: the analysis, clustering, cluster effect-size, and cluster graphics panels expect the outputs of earlier PERT+ workflows. They are not generic CSV importers.

Error Graphics generation modes:

- Single-result mode: if you pass one analysis summary JSON, PERT+ generates per-distribution charts only (`signed_line.png`, `signed_bar.png`, `absolute_line.png`, `absolute_bar.png`) inside that distribution folder.
- Multi-result mode: if you pass a folder containing summaries for `beta`, `triangular`, and `lognormal`, PERT+ also generates combined comparison charts in `combined/` (`combined_line_signed.png`, `combined_bar_signed.png`, `combined_line_absolute.png`, `combined_bar_absolute.png`) in addition to per-distribution charts.
- Partial multi-result input: if one or more of the three required distributions is missing, PERT+ skips combined charts and still generates the per-distribution charts for the JSON files that are present.
- Distribution labeling: chart titles and output subfolders use the detected distribution name. For older summaries, PERT+ falls back to the paired `*_analysis_results.csv` when needed.

## Preferences

The toolbar exposes:

- theme toggle
- Preferences dialog

The preferences dialog stores defaults for:

- simulation count, optimistic and pessimistic scalars, percentile, fixed seed
- clustering range, feature weights, test split, tree depth, fixed seed
- PCA variance threshold and fixed seed
- effect-size bootstrap count, CI level, fixed seed
- graphics DPI
- batch parallelism and worker count

For full setting-by-setting definitions (purpose, ranges, defaults, and usage notes), see `SETTINGS_REFERENCE.md`.

Each action panel also includes a progress area with:

- live log output
- cancel request
- force-stop request

Cancellation is best-effort and depends on whether the underlying engine is currently at a cancellation checkpoint.

## Graphics Panel Pattern (Scalable)

Graph/image-oriented panels should inherit from `ImagePreviewPanel` and use the shared helpers in that class:

- `_build_graphics_output_group(...)` to create consistent output controls
- `_add_generate_and_preview(...)` to wire generate + in-window preview UI
- `_temp_output_dir_str()` for temp-only image generation
- `_autosave_non_image_to_picker(...)` for automatic CSV/JSON artifact persistence

This pattern gives all graphics panels consistent behavior:

- Generated images are previewed from a temp directory
- Save Graphics copies image/HTML graphics to a user-selected auto-named subfolder
- Don't Save deletes the temp directory
- Temp directories are cleaned on regenerate and app close

Current rules used by built-in panels:

- Non-image artifacts (for example CSV/JSON) remain auto-saved for analysis-style workflows
- HTML artifacts are not previewed in-panel
- Complexity Visualizer HTML is not auto-saved; it is exported only through Save Graphics

## Validation Status

Validation was run in the `path_gen_build` environment against real files from this workspace. The following workflows completed successfully and produced outputs under `Unified_App/sample_outputs`:

- app startup and main-window construction
- settings persistence in portable mode
- worker progress and completion signaling
- Monte Carlo simulation
- percent-error analysis
- error graphics generation
- clustering analysis
- cluster effect-size analysis
- cluster graphics generation
- PCA analysis
- complexity visualization
- Excel-to-RCP conversion
- direct complexity-measure calculation

Representative validation inputs included:

- `MT/MT30/Set 1 SP/EV1.rcp`
- `Simulator Code Correct Version/output/Output 10k Sims Divide by 2/Master_Output_File_CSV_Version.csv`
- `Simulator Code Correct Version/output/Output 10k Sims Divide by 2/PCA_analysis/pca_feature_matrix.csv`
- `DSLIB/Excel/C2011-10 Building a House.xlsx`

## Known Limitations

- The analysis panel requires simulator batch CSV files with the full fixed percentile schema used by the adapted simulator output.
- The clustering panel requires simulator-style CSV input containing columns such as `source_file`, `is_beta`, and `is_lognormal`.
- A non-fatal Qt warning about a missing font directory may appear in offscreen or test launches depending on the environment.
- VS Code may still show unresolved `PySide6` imports if the editor is pointed at a different interpreter than the validated runtime environment.

## Sample Outputs

Canonical sample artifacts are stored in:

- `Unified_App/sample_outputs/simulation`
- `Unified_App/sample_outputs/batch_simulation`
- `Unified_App/sample_outputs/analysis`
- `Unified_App/sample_outputs/error_graphics`
- `Unified_App/sample_outputs/clustering`
- `Unified_App/sample_outputs/cluster_effects`
- `Unified_App/sample_outputs/cluster_graphics`
- `Unified_App/sample_outputs/pca`
- `Unified_App/sample_outputs/complexity_viz`
- `Unified_App/sample_outputs/path_generator`
- `Unified_App/sample_outputs/complexity_measures`
- `Unified_App/sample_outputs/build_rcp`

Regenerate these canonical samples with:

```powershell
conda activate path_gen_build
python Unified_App/tools/regenerate_sample_outputs.py
```

The script clears old sample artifacts before regenerating, so each workflow folder contains a single current reference output set.