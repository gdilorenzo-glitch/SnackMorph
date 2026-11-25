# SnackMorph — private release candidate
Python tools for multi-scale characterisation of expanded snacks from JPEG photographs and VOX micro-CT volumes. **Draft repository, not yet a SoftwareX-compliant public release.** Derived from the authors' original Colab notebook. Independent synthetic benchmark generators are included; their targets are not generated with SnackMorph. No experimental raw data or private results are included.

## Install
Python 3.10+ (use 3.12 for the reference environment if supported). In a clean virtual environment:
```sh
python -m pip install -e '.[test]'
python -m snackmorph --help
pytest -q
```
Optional accelerated CT dependencies: `python -m pip install -e '.[fast]'`. The historical environment is recorded in `requirements-tested.txt`; re-test and lock dependencies for the release. Generator requirements: `python -m pip install pillow numpy scipy`.

## Example use
```sh
python -m snackmorph verify results/smoke
python validation/generators/generate_jpeg.py --out validation_data/JPEG
python validation/generators/generate_vox.py --out validation_data/VOX
```
The `verify` command is the earlier internal smoke test, not independent validation. The new generators produce 100 JPEG images with instance labels and 30 VOX phantoms with theoretical masks. `validation/check_dataset.py` checks their integrity. See `docs/VALIDATION_PROTOCOL.md` for measurement definitions and the development/test split. Full scientific evaluation of the benchmark is pending. The test split is held out by geometry, not blinded.

For a real JPEG use the legacy laboratory layout with explicit lot, photo key, rows, and independent calibration file as shown by `python -m snackmorph jpeg --help`. The historical central-diameter calibration is inappropriate for testing independent dimensional accuracy; use external mm/pixel and the lower-level `width_normals` interface. The 11 experimental photographs are independent; the B-04 day-zero mapping must be verified before including those records. For a VOX file place its XML alongside it, then `python -m snackmorph vox sample.VOX results/ct --step 4`. This legacy CLI uses block averaging; specify historical regular subsampling using the lower-level `vox.sample_volume` interface. Inspect ROI and diagnostic images; automatic ROI is not universally validated. A supplied ROI must be boolean and aligned with the sampled grid. Physical scaling for the CT experiment is in `src/snackmorph/physical.py`; the legacy CLI does not yet automatically activate it. JPEG physical scaling was evaluated in separate experiment scripts and is not yet integrated here. Web app and full batch orchestration remain pending.

## Structure
- `src/snackmorph/` core Python modules and local CLI
- `tests/` software regression/unit tests, not evidence of independent accuracy
- `validation/` independent synthetic data generators and integrity checks
- `docs/` validation protocol, release checklist and metadata worksheet
- `.github/workflows/` basic CI configuration (not yet run on GitHub)

## Citation, licence and data
Authors and copyright holder must approve an OSI-recognised code licence and create `LICENSE.txt` before a public release; no licence is selected here. Replace support/contact and citation placeholders at release; add a DOI if archived. Share experimental data only with rights-holder permission via an appropriate research-data repository, not the Git history. The original Colab notebook and historical experimental outputs are preserved separately.
