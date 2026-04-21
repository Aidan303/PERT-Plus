# PERT+ Troubleshooting

Use this guide for the most common issues while running or testing PERT+.

## App Does Not Start

Symptoms:

- Launch command exits immediately.
- Qt/PySide import or DLL errors.

Checks:

1. Confirm environment:

```powershell
conda activate path_gen_build
python -c "import ctypes, PySide6.QtWidgets; print('ok')"
```

2. Confirm launch location:

```powershell
cd Unified_App
python app.py
```

Likely cause:

- Mixed pip/conda Qt stack in the same environment.

Fix approach:

- Keep one consistent Qt stack in `path_gen_build` (prefer conda-forge stack if you use conda Qt packages).

## VS Code Shows PySide6 Unresolved Import

Symptom:

- Editor warning says `PySide6` cannot be resolved, but app still runs from terminal.

Cause:

- VS Code interpreter is not set to `path_gen_build`.

Fix:

- Switch the Python interpreter in VS Code to the same environment used in terminal (`path_gen_build`).

## Analysis Panel Fails With Missing Percentile Columns

Symptom:

- Error lists missing fields like `sim_p1`, `pert_p1`, `bb2_p1`, `lognormal_p1`, etc.

Cause:

- Input CSV is not from the expected simulator batch schema.

Fix:

- Feed analysis with simulator output produced by PERT+ simulation/batch workflows.

## Analysis Panel Error: `'str' object has no attribute 'mkdir'`

Symptom:

- Analysis fails with `[ERROR] 'str' object has no attribute 'mkdir'`.

Status:

- Fixed in current Unified_App code.

If you still see it:

1. Restart the app to ensure latest code is loaded.
2. Rerun analysis on the same input CSV.

## Clustering Panel Fails With Missing Columns

Symptom:

- Missing `source_file`, `is_beta`, or `is_lognormal`.

Cause:

- Input CSV is not a simulator master-style dataset.

Fix:

- Use a compatible master simulator CSV, for example:
  `Simulator Code Correct Version/output/Output 10k Sims Divide by 2/Master_Output_File_CSV_Version.csv`

## Error Graphics Panel Produces No Combined Charts

Symptom:

- Distribution-specific charts are generated but no combined charts.

Cause:

- Combined graphics require summaries for all three distributions: beta, triangular, lognormal.

Fix:

- Provide a folder containing all required JSON summaries.

## Error Graphics Produces Only Line Charts

Symptom:

- Single-result graphics output contains only line charts.

Status:

- Fixed in current Unified_App code. Single-result mode now generates both line and bar charts.

Expected single-result outputs:

- `signed_line.png`
- `signed_bar.png`
- `absolute_line.png`
- `absolute_bar.png`

## Graphics Were Previewed But Not Found On Disk

Symptom:

- You generated charts and saw them in preview, but nothing appeared in your normal output folder.

Cause:

- Image-producing panels now generate graphics in a temporary preview session first.

Expected behavior:

- Use Save Graphics to export generated graphics to a chosen destination.
- PERT+ creates an auto-named subfolder at save time.
- If you press Don't Save, generate again, or close the app before saving, temporary graphics are deleted.

Note:

- Switching panels does not delete temporary graphics.

## Complexity Visualizer HTML Not Visible In Preview

Symptom:

- PNG previews show normally, but HTML outputs do not appear in the preview area.

Expected behavior:

- HTML outputs are intentionally not previewed in-panel.
- Complexity Visualizer HTML is not auto-saved; export via Save Graphics.

## Error Graphics Title Shows Generic "Distribution"

Symptom:

- Chart titles use a generic distribution label instead of beta/triangular/lognormal.

Cause:

- Older summary files may not include distribution metadata.

Current behavior:

- PERT+ first uses summary metadata, then falls back to input filename parsing, and finally to paired `*_analysis_results.csv` when available.

If it still appears generic:

1. Regenerate the analysis summary JSON from the current Analysis panel code.
2. Rerun Error Graphics with the refreshed JSON.

## Build RCP Fails On Excel Input

Checks:

1. File is `.xlsx`/supported workbook and readable.
2. Workbook structure matches expected project format.

Known good validation input:

- `DSLIB/Excel/C2011-10 Building a House.xlsx`

## Cancel / Force Stop Feels Delayed

Expected behavior:

- Cancel is best-effort and works at engine cancellation checkpoints.
- Force-stop requests immediate thread stop, but cleanup timing depends on current operation.

## Non-Fatal Qt Font Warning

Symptom:

- Warning about missing Qt font directory in some launches/tests.

Status:

- Known non-fatal warning observed in offscreen/test contexts.

## Quick Diagnostic Commands

```powershell
conda activate path_gen_build
python -c "import ctypes, pandas, PySide6.QtWidgets; print('runtime imports ok')"
python Unified_App/app.py
```

## Sample Outputs Need Refresh

Symptom:

- The `Unified_App/sample_outputs` folder is missing, stale, or was modified during manual testing.

Fix:

```powershell
conda activate path_gen_build
python Unified_App/tools/regenerate_sample_outputs.py
```

Behavior:

- The regeneration script recreates a single canonical sample set per workflow.
- Any legacy `Unified_App/test_outputs` folder is removed.

## If You Need A Clean Retest

Use a fresh output folder and rerun in this order:

1. Monte Carlo Simulation
2. Percent-Error Analysis
3. Error Graphics
4. Clustering Analysis
5. Cluster Effect Sizes
6. Cluster Graphics