# User guide

Run commands from an installed environment; use a new output directory. Review all masks and diagnostics before interpreting quantities.

## JPEG

Input: top-view JPEG, light background, three columns of paired specimens and explicit row count, optional crop. The laboratory workflow also needs a calibration CSV with the columns used by `jpeg.load_caliper` (`lotto,t_gg,tecnologia,potenza,tau,d_ini,d_cal`; inspect code for original layout and aliases). Lot/photo key and day must correspond to the original grid mapping. Do not assume arbitrary photo names are supported. Example syntax (replace input paths and IDs with actual experiment values):

```sh
python -m snackmorph jpeg photo.jpg caliper.csv results/jpeg --photo-key B02_0 --lot B-02 --day 0 --rows 6 --width-method subpixel
```

The output includes overlay.png, profiles.csv, fit_legacy.csv (legacy column naming, regardless of estimator), fit_explicit_units.csv, colour.csv, colour_profiles.csv, colour_fit.csv and run.json. Physical length is in mm; ED, Pk and Le are dimensionless; Lab values are relative when no colour target is used. The calibration uses central diameters by design; independent metric verification must use an externally determined scale. With a known scale `p` (mm/pixel), call `jpeg.segment_photo` and `jpeg.width_normals(mask, method="subpixel")`; multiply the returned widths and axis length by `p`. The benchmark uses this independent-scale route with analytic references. `width_normals` reports widths in pixels at 23 fractions. Do not change historical measurements by substituting a new estimator retrospectively.

## VOX

Input: reconstructed 16-bit VOX and matching XML; select an integer sampling step. ROI .npy must be boolean and have exactly the shape of the sampled ZYX volume. The CLI uses block-mean sampling. Example:

```sh
python -m snackmorph vox sample.VOX results/vox --step 4 --roi sample_roi.npy
```

Without `--roi` the original fixture-specific algorithm is used. Review holder/adhesive removal and specimen boundaries; it is not appropriate for arbitrary phantom geometries. `summary.csv`, `roi.npy`, `run.json` and scan-prefixed tables/diagnostics contain the outputs. Porosity in the core summary is a fraction (multiply by 100 for percent); pitches and thicknesses are in µm, volumes in mm³. Connectivity density and watershed count are distinct descriptors. The local-thickness values depend on voxel sampling and discrete sphere levels.

For regular subsampling and physical scaling, use the Python API in a separate process (the configuration changes module parameters):

```python
from snackmorph import vox
from snackmorph.physical import configure
settings = vox.resolve_settings("sample.VOX")
reader = vox.open_volume("sample.VOX", settings)
step = 3
controls, roi_ds = configure(step, settings["pitch"], reader.shape, "physical")
image = vox.sample_volume(reader, "ogni N", step, step, step)
roi, params = vox.roi_volume(image, vox.roi_params(), vox.ROI_STEP, vox.ROI_SMOOTH_Z, roi_ds)
summary, distributions, objects = vox.analyze_volume(image, roi, "results/scan", settings["pitch"] * step, vox.ANALYSIS_DS)
```

Create `results/` first, save `controls`, and review `roi` before analysis. The policy assumes the original fourfold reference sampling and a reference ROI XY grid factor of one; it rejects incompatible grids. It does not guarantee native-resolution accuracy. Reconstructed volume and phase metrics on the synthetic truth set use the frozen case functions, not every descriptor in the full CLI. The data assets contain exact runnable inputs for benchmarking; historical raw scans are restricted.
