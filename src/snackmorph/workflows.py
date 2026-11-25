"""Explicit local entry points; never overwrite inputs. Not a validated web service."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from . import jpeg, vox

def run_jpeg(path, calibration_csv, output, *, photo_key, lots, nrows, crop=None, width_method="legacy"):
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    im,samples=jpeg.segment_photo(str(path),nrows,crop)
    if len(samples)!=nrows*3:
        raise ValueError(f'Expected {nrows*3} grid cells; detected {len(samples)}')
    cal=jpeg.load_caliper(calibration_csv)
    prof=jpeg.profile_table(samples,photo_key,lots,cal,width_method=width_method)
    if prof.empty: raise ValueError('No matching calibration rows')
    fit=jpeg.fit_all_profiles(prof)
    lab,bg=jpeg.photo_lab(im,samples)
    col,cp,ref=jpeg.colour_tables({photo_key:(im,samples,lab,bg)},{photo_key:lots})
    cm=jpeg.fit_colour_profiles(cp)
    import cv2
    cv2.imwrite(str(out/'overlay.png'),cv2.cvtColor(jpeg.overlay_photo(im,samples),cv2.COLOR_RGB2BGR))
    for name,df in [('profiles',prof),('fit_legacy',fit),('fit_explicit_units',jpeg.explicit_amplitude(fit)),('colour',jpeg.colour_descriptors(col)),('colour_profiles',cp),('colour_fit',cm)]:
        df.to_csv(out/(name+'.csv'),index=False)
    (out/'run.json').write_text(json.dumps(dict(width_method=width_method,photo_key=photo_key,lots=lots,nrows=nrows,crop=crop,detected_cells=len(samples),fitted_samples=len(fit),expected_samples=2*len(samples)*len(lots),colour_Lref=float(ref),colour_reference_scope='single photograph; original cross-photo Lref requires joint processing'),indent=2))
    return fit

def run_vox(path, output, *, step, roi_path=None):
    if type(step) is not int or step<1: raise ValueError('Explicit positive sampling step required')
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    st=vox.resolve_settings(str(path)); reader=vox.open_volume(str(path),st)
    red=vox.sample_volume(reader,'media',step,step,step)
    pitch=st['pitch']*step
    if roi_path is None:
        roi,params=vox.roi_volume(red,vox.roi_params(),vox.ROI_STEP,vox.ROI_SMOOTH_Z,vox.roi_ds(red.shape)); mode='automatic_unvalidated'
    else:
        roi=np.load(roi_path,allow_pickle=False)
        if roi.dtype!=bool or roi.shape!=red.shape: raise ValueError('ROI must be a boolean .npy on the sampled ZYX grid')
        params={}; mode='supplied'
    if not roi.any(): raise ValueError('Empty ROI')
    np.save(out/'roi.npy',roi)
    summary,dist,df=vox.analyze_volume(red,roi,str(out/'scan'),pitch,vox.ANALYSIS_DS)
    pd.DataFrame([summary]).to_csv(out/'summary.csv',index=False)
    (out/'run.json').write_text(json.dumps(dict(sampling_step=step,sampling_mode='media',pitch_original_um=st['pitch'],working_voxel_um=pitch*vox.ANALYSIS_DS,roi_mode=mode,roi_parameters=params,fast_edt_available=vox._edt_mod is not None,fast_sitk_available=vox._sitk is not None),indent=2,default=str))
    return summary

