# Reproducibility of the validation campaign

The frozen snapshot is the exact pre-test source in `validation/audit/final_validation.zip`, including `frozen_source.zip`, `results/frozen_plan.json`, original development reports, case-level CSV/JSON logs and the summary script. The integrated release candidate has an additional CLI option and updated packaging/metadata; do not run the old freeze check against the updated package tree. Instead use `validation/reproduce_frozen.py`, which reads the audit bundle, verifies the two original input archives and the source hashes and uses the original runner. Run in Linux/Colab with the pinned benchmark dependencies; Python 3.13.5 matches the final local campaign. The first run may take several minutes depending on CPU and memory. Use a new output directory.

```sh
python -m pip install -r requirements-benchmark.txt
python validation/reproduce_frozen.py --general /path/SnackMorph_validation_data.zip --fixture /path/SnackMorph_fixture_data_v1.zip --out results/reproduction --workers 2
```

The wrapper runs five frozen jobs (development JPEG/VOX, test JPEG/VOX and test fixture), then recomputes summary.json from outputs and the archived legacy development results. An additional post-hoc fixture diagnostic is provided separately (`fixture_end_to_end.py`). Its results must not be interpreted as a new independent test or used to retune the algorithm. The original held-out plan used a predefined split by geometry, unchanged data, and analyst-defined descriptive thresholds; the test was not blinded. No experimental raw volume is contained in the audit bundle. `review_statistics.py` recomputes stricter match counts, group-level statistics and tail errors from archived case CSVs without re-estimation.

The original audit archive preserves its historical licence placeholder solely for provenance. The current software distribution is covered by the root MIT licence; the audit record must not be edited to fabricate an earlier licensing decision or analysis freeze. Data rights are distinct and should be confirmed by the authors before formal deposit.
