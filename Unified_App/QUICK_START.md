# PERT+ Quick Start

This is the short runbook for launching and using PERT+ quickly.

For complete setting definitions and ranges, see `SETTINGS_REFERENCE.md`.

## 1) Open Environment

From workspace root:

```powershell
conda activate path_gen_build
cd Unified_App
```

If dependencies are not installed yet:

```powershell
pip install -r requirements.txt
```

## 2) Launch App

```powershell
python app.py
```

## 3) Fast Test Flow (Recommended)

Run these panels in order for a complete path check:

1. Monte Carlo Simulation
2. Percent-Error Analysis
3. Error Graphics
4. Path Generator

Why this order:

- Simulation and Batch panels now use a single distribution selector (Beta, Triangular, or Lognormal) per run.
- Analysis expects simulator-style batch CSV output.
- Error Graphics expects analysis JSON output.
- Graph/image panels generate images into a temporary preview session first; use Save Graphics to export what you want to keep.

Error Graphics result modes:

- One JSON input: generates `signed_line.png`, `signed_bar.png`, `absolute_line.png`, and `absolute_bar.png` for that distribution.
- Folder input with all three distributions (`beta`, `triangular`, `lognormal`): generates the same per-distribution charts plus combined charts under `combined/`.
- Folder input missing one or more distributions: generates per-distribution charts only (no combined charts).
- Distribution naming in output/title: uses summary metadata when available, with fallback inference for older summary files.

## 4) Known Good Sample Inputs

- RCP: `MT/MT30/Set 1 SP/EV1.rcp`
- Clustering input: `Simulator Code Correct Version/output/Output 10k Sims Divide by 2/Master_Output_File_CSV_Version.csv`
- PCA / complexity viz input: `Simulator Code Correct Version/output/Output 10k Sims Divide by 2/PCA_analysis/pca_feature_matrix.csv`
- Build RCP input: `DSLIB/Excel/C2011-10 Building a House.xlsx`

## 5) Where Outputs Go

Output behavior now depends on artifact type:

- Non-image analysis files (for example CSV/JSON) auto-save to the panel autosave folder when that panel provides one.
- Image outputs are generated in a temporary directory for preview first.
- Use Save Graphics to export image artifacts to a chosen folder (PERT+ creates an auto-named subfolder).
- Use Don't Save to discard temporary graphics immediately.
- Temporary graphics are also cleaned when you generate again or close the app.

Special case:

- Complexity Visualizer HTML files are not previewed and not auto-saved; they are exported only through Save Graphics.

Canonical reference outputs for packaging/demo are available in:

- `Unified_App/sample_outputs/`

To refresh them:

```powershell
conda activate path_gen_build
python Unified_App/tools/regenerate_sample_outputs.py
```

## 6) Portable Settings (Optional)

If `settings.ini` exists next to the executable, PERT+ uses it for local portable settings storage.