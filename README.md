# Project Completion Time Analysis App

This repository root is the project-level container for the PERT+ desktop application and related assets.

## High-Level Goal

The goal of this project is to provide a practical, GUI-based toolkit for project completion time analysis workflows, including:

- Monte Carlo simulation of project schedules from `.rcp` files
- Percent-error and comparative analysis of simulation outputs
- Visualization workflows for error trends, clusters, PCA, and path structures
- Supporting utilities such as complexity measure extraction and Excel-to-RCP conversion

The core application is implemented in the `Unified_App/` folder.

## Why The App Is Nested In `Unified_App/`

The application code and its documentation are intentionally contained in the `Unified_App/` subfolder so the repository can also host additional non-app content at the root level over time.

Examples of content that may be added outside `Unified_App/` include:

- research notes and experiments
- external datasets or references
- packaging and deployment artifacts
- process documentation or planning material

Keeping the app self-contained makes growth at the repository root easier without mixing unrelated files into the app package.

## Repository Layout

```text
Project Completion Time Analysis App/
|-- README.md                        # Project-level overview (this file)
|-- Unified_App/                     # Self-contained PERT+ application package
|   |-- app.py
|   |-- README.md
|   |-- QUICK_START.md
|   |-- DEVELOPER_GUIDE.md
|   |-- ...
|-- (future root-level content)      # Notes, datasets, planning, packaging, etc.
```

## Application Documentation

All app-specific documentation lives in `Unified_App/`:

- Main app overview: [Unified_App/README.md](Unified_App/README.md)
- Quick start: [Unified_App/QUICK_START.md](Unified_App/QUICK_START.md)
- Troubleshooting: [Unified_App/TROUBLESHOOTING.md](Unified_App/TROUBLESHOOTING.md)
- Settings reference: [Unified_App/SETTINGS_REFERENCE.md](Unified_App/SETTINGS_REFERENCE.md)
- Developer guide: [Unified_App/DEVELOPER_GUIDE.md](Unified_App/DEVELOPER_GUIDE.md)

## Primary App Location

- Application entry point: `Unified_App/app.py`
- Python dependencies: `Unified_App/requirements.txt`
- Sample outputs: `Unified_App/sample_outputs/`
