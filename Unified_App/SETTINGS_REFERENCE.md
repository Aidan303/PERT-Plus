# PERT+ Settings Reference

This guide explains each user-facing setting, what it controls, valid range/options, defaults, and practical notes.

## How Settings Work

- Global defaults are managed in Preferences and stored in `settings.ini` (portable mode) or platform settings.
- Panel controls are initialized from saved defaults.
- Some panels include extra run-specific controls that are not global defaults.
- `Reset to Defaults` in Preferences clears saved settings and restores built-in defaults.

## Simulation Settings

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| Simulations per run | Integer | 100 to 1,000,000 | 10,000 | Number of Monte Carlo draws per job | Higher = more stable percentiles, longer runtime, more memory |
| Optimistic scalar | Float | 0.01 to 0.99 | 0.5 | Multiplier for optimistic activity durations | Must stay below 1.0 by design |
| Pessimistic scalar | Float | 1.01 to 10.0 | 1.5 | Multiplier for pessimistic activity durations | Must stay above 1.0 by design |
| Completion percentile | Float | 0.5 to 0.9999 | 0.999 | Percentile target used in deterministic/summary metrics | Higher values emphasize right-tail risk |
| Distribution | Choice | Beta, Triangular, Lognormal | Beta | Single distribution used by Simulation and Batch runs | One distribution per run |
| Enable fixed seed | Boolean | On / Off | Off | Reproducible random sampling | Use with Seed value |
| Seed value | Integer | 0 to 999999 | 42 | RNG seed when fixed seed is enabled | Ignored when fixed seed is off |

## Batch Execution Settings

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| Enable parallel execution | Boolean | On / Off | Off | Run file jobs concurrently | Parallelism is per file job |
| Max worker threads | Integer | 1 to 32 | 4 | Thread pool size when parallel is enabled | Effective concurrency is `min(total_jobs, max_workers)` |

## Clustering Settings

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| K min | Integer | 2 to 20 | 2 | Minimum cluster count to evaluate | Keep `K min <= K max` |
| K max | Integer | 2 to 50 | 10 | Maximum cluster count to evaluate | Wider search increases runtime |
| Complexity feature weight | Float | 0.0 to 10.0 | 1.0 | Weight on complexity features | Larger values increase complexity feature influence |
| Dummy feature weight | Float | 0.0 to 10.0 | 0.5 | Weight on dummy/indicator features | Tune relative to complexity weight |
| Decision tree test size | Float | 0.05 to 0.5 | 0.2 | Holdout fraction for decision tree diagnostics | Higher values reduce training split |
| Decision tree max depth | Integer | 1 to 20 | 4 | Maximum depth for tree diagnostics | Larger depth can overfit |
| Enable fixed seed | Boolean | On / Off | Off | Reproducible clustering diagnostics | Use with Seed value |
| Seed value | Integer | 0 to 999999 | 42 | RNG seed when fixed seed is enabled | Ignored when fixed seed is off |

## PCA Settings

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| Variance threshold | Float | 0.5 to 0.9999 | 0.95 | Retained explained variance target | Higher threshold keeps more components |
| Enable fixed seed | Boolean | On / Off | Off | Reproducible PCA-adjacent random steps | Use with Seed value |
| Seed value | Integer | 0 to 999999 | 42 | RNG seed when fixed seed is enabled | Ignored when fixed seed is off |

## Effect Size Settings

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| Bootstrap samples | Integer | 100 to 100000 | 2000 | Number of bootstrap resamples | Higher values improve CI stability, increase runtime |
| CI level | Float | 0.5 to 0.999 | 0.95 | Confidence interval level | Common values: 0.90, 0.95, 0.99 |
| Enable fixed seed | Boolean | On / Off | Off | Reproducible bootstrap sampling | Use with Seed value |
| Seed value | Integer | 0 to 999999 | 42 | RNG seed when fixed seed is enabled | Ignored when fixed seed is off |

## Graphics Setting

| Setting | Type | Range / Options | Default | What It Controls | Notes |
| --- | --- | --- | --- | --- | --- |
| Output DPI | Integer | 72 to 600 | 300 | Pixel density for generated image outputs | Higher DPI improves sharpness but increases file size and render time |

## Panel-Specific Runtime Settings

These are user-facing controls that are not all persisted as global defaults.

### Path Generator

| Setting | Type | Range / Options | Default Behavior | Notes |
| --- | --- | --- | --- | --- |
| RCP file(s) | Multi-file input | One or more `.rcp` files | Required each run | Generates one PNG per selected file |
| Output DPI | Integer | 72 to 600 | Uses saved Output DPI default | Same quality/performance trade-off as graphics DPI |

### Graphics Preview Session (Image Panels)

These controls are shared across image-producing panels.

| Control | Type | Behavior | Notes |
| --- | --- | --- | --- |
| Save Graphics | Action button | Prompts for a destination folder and exports generated image/HTML graphics into an auto-named subfolder | Does not affect non-image auto-saved artifacts |
| Don't Save | Action button | Deletes the current temporary graphics session directory | Also clears in-panel preview |
| Carousel arrows | Action buttons | Navigate multiple generated images in the preview area | Disabled when there is only one image |

Cleanup lifecycle for temporary graphics:

- Deleted when Don't Save is pressed
- Deleted when Generate is run again in that panel
- Deleted on application close
- Not deleted when switching panels

### Simulation Panel (run-time controls)

| Setting | Type | Range / Options | Notes |
| --- | --- | --- | --- |
| Run files in parallel | Boolean | On / Off | Uses Simulation parallel defaults |
| Max workers | Integer | 1 to 32 | Uses Simulation worker defaults |

### Batch Simulation Panel (run-time controls)

| Setting | Type | Range / Options | Notes |
| --- | --- | --- | --- |
| Run files in parallel | Boolean | On / Off | Uses Batch parallel defaults |
| Max workers | Integer | 1 to 32 | Uses Batch worker defaults |

## Operational Guidance

- If CPU is low and memory is high, increasing workers may not help and can hurt performance.
- Start with 2 to 4 workers, then increase gradually while monitoring runtime and memory pressure.
- Use fixed seeds when you need reproducible comparisons between runs.
- Use 300 DPI for report-quality graphics; use lower DPI for quick iteration.
