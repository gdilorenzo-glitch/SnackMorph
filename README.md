# SnackMorph

Python research software for multiscale characterisation of expanded snacks from controlled JPEG photographs and reconstructed VOX micro-CT volumes. Authors: Gianfranco Di Lorenzo and Francesco Marra, University of Salerno. Support: gdilorenzo@unisa.it. Code licence: MIT (`LICENSE.txt`). This is release candidate **1.0.0rc1**, not a published final release.

## What it does

* JPEG: chroma segmentation of a three-column grid, paired-specimen separation, curved centreline, perpendicular diameter profile, expansion and relative CIELAB descriptors. `--width-method subpixel` reduces discretisation bias; `legacy` remains the default for historical reproduction.
* VOX: 16-bit volume + matching XML, specimen ROI with fixture-specific holder/adhesive removal or supplied boolean ZYX ROI, porosity and 2D/3D morphology, local thickness, watershed and anisotropy. `physical.configure` exposes spatial rescaling through Python for the original reference geometry. The CLI supports block averaging; see the manual for the Python API and regular-subsampling workflow.
* Reproducibility: frozen source, case-level metrics, validation criteria, source/data hashes and execution logs are provided in `validation/audit/final_validation.zip`. They distinguish synthetic accuracy, historical numerical reproduction and experimental spatial sensitivity.

## Installation and smoke test

Reference Colab: Python 3.12; final local benchmark: Linux, Python 3.13.5. Use a clean virtual environment. From the repository root:

```sh
python -m venv .venv
# Activate .venv (Linux/macOS: source .venv/bin/activate; Windows: .venv\Scripts\Activate.ps1)
python -m pip install -r requirements-benchmark.txt -e '.[test]'
python -m snackmorph --help
python -m snackmorph jpeg --help
python -m snackmorph vox --help
pytest -q
python -m snackmorph verify results/smoke
```

The smoke test and unit tests are software checks, not independent measurement validation. Optional `edt`/`SimpleITK` accelerators are not required for the reference synthetic benchmark. See `docs/USER_GUIDE.md` for inputs, units, output files and safe interpretation.

## Reproduce the published benchmark candidate

Download the original synthetic dataset archives from the repository's [benchmark-data-v1](https://github.com/gdilorenzo-glitch/SnackMorph/releases/tag/benchmark-data-v1) and [fixture-data-v1](https://github.com/gdilorenzo-glitch/SnackMorph/releases/tag/fixture-data-v1) releases. Verify and extract them using the instructions in `docs/REPRODUCIBILITY.md`. The immutable analysis snapshot is embedded in the audit archive; the CLI integration was added afterwards without changing the validated chord function. The original source hashes and criteria remain unchanged. The reproduction wrapper verifies both archives before running, and uses new output directories. The fixture runner requires a filesystem with symlink support; Linux/Colab is recommended.

Held-out synthetic outcomes: 2,154/2,160 matched JPEG instances (2,148 with Dice >= 0.95), 1,076/1,080 fits returned; median absolute relative expansion-degree error 3.64%. With supplied ROI, median pore Dice 0.9976 and median absolute porosity error 0.0168 percentage points, but maximum error 10.35 points. On fixture phantoms, median ROI Dice 0.9546. Full metrics and failures are retained. The split is held out by geometry, not blinded; variants and chords are correlated. Criteria were analyst-defined and are not metrology standards. The extra post-hoc diagnostic is explicitly separate from the frozen assessment.

## Scope and limitations

The JPEG calibration in the original experiment used central caliper diameters and is not an independent accuracy check. Colour values are relative without a calibrated target. Review overlays, pair assignments and failures; resized real photographs can fail quality checks. General VOX automatic ROI is not a universal segmentation method: it assumes the original circular-segment holder and adhesive; use a supplied ROI elsewhere. Fixture intensity/size differ from experimental scans, and automatic ROI validation does not establish accurate porosity. Physical scaling reduces selected grid-dependent differences but does not establish convergence. Exploratory midpoint/axial methods are diagnostics, not the primary algorithms. The experimental raw images/volumes and their independent reference annotations are not distributed here; experimental numerical reproduction is not independent accuracy. No deployed web service or external adoption is claimed.

## Repository layout

`src/snackmorph/` core; `tests/` software tests; `validation/` generators and evaluators; `validation/audit/` frozen plan, code and case-level results; `docs/` guide, validation definitions and metadata. Legacy protocol documents are historical; the frozen plan and reproducibility guide take precedence. `CITATION.cff` records software authorship. The software licence does not automatically license experimental data or synthetic data assets; dataset terms require separate confirmation. A final immutable release/tag and any archival DOI must be created before manuscript submission.
