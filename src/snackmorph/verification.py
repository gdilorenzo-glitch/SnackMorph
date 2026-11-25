"""Reproducible synthetic diagnostics, not independent experimental validation."""
from pathlib import Path
import json, tempfile
import numpy as np
import pandas as pd
from . import jpeg, vox

def run(output):
    out=Path(output); out.mkdir(parents=True,exist_ok=False)
    im,truth=jpeg.synthetic_photo()
    mask,hsv=jpeg.get_mask(im); cells=jpeg.cell_regions(mask,6)
    V=jpeg.cv2.GaussianBlur(hsv[...,2].astype(np.float32),(0,0),1.5)
    Vl=jpeg.cv2.GaussianBlur(hsv[...,2].astype(np.float32),(0,0),9)
    samples=jpeg.refine_with_chroma(im,{k:jpeg.split_cell(reg,V,Vl)[0] for k,reg in sorted(cells.items())})
    errors=[]; rows=[]; pk={}
    for (r,c),(di,A,s,m) in truth.items():
        tech,pw,tau=jpeg.layout('B02_15',r,c,'B-02'); pk[(tech,pw,tau)]=(di+A)/di
        rows.append(dict(lotto='B-02',t_gg=15,tecnologia=tech,potenza=pw,tau=tau,d_ini=di*.25,d_cal=(di+A)*.25))
    for k,d in samples.items():
        di,A,_,_=truth[k]
        for mk in (d['A'],d['B']):
            w,_=jpeg.width_normals(mk); errors.append(w[.5]-di-A)
    prof=jpeg.profile_table(samples,'B02_15',[('B-02',15)],pd.DataFrame(rows)); fit=jpeg.fit_all_profiles(prof)
    fit['Pk_true']=[pk[(t,p,a)] for t,p,a in zip(fit.tecnologia,fit.potenza,fit.tau)]
    lab,bg=jpeg.photo_lab(im,samples); c,cp,_=jpeg.colour_tables({'B02_15':(im,samples,lab,bg)},{'B02_15':[('B-02',15)]}); cm=jpeg.fit_colour_profiles(cp)
    fit=jpeg.explicit_amplitude(fit); fit.to_csv(out/'jpeg_synthetic_fits.csv',index=False)
    jpeg.colour_descriptors(c).to_csv(out/'jpeg_synthetic_colour.csv',index=False)
    jpeg.cv2.imwrite(str(out/'jpeg_overlay.png'),jpeg.cv2.cvtColor(jpeg.overlay_photo(im,samples,.3),jpeg.cv2.COLOR_RGB2BGR))
    result={'jpeg':dict(cells=len(cells),samples=len(fit),colour_fits=len(cm),diameter_bias_px=float(np.mean(errors)),diameter_sd_px=float(np.std(errors)),median_R2=float(fit.R2.median()),Pk_r=float(np.corrcoef(fit.Pk,fit.Pk_true)[0,1]),Pk_bias=float((fit.Pk-fit.Pk_true).mean()))}
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'synthetic.vox'; fraction,known=vox.synthetic_vox(str(path)); st=vox.resolve_settings(str(path)); reader=vox.open_volume(str(path),st); red=vox.sample_volume(reader,'media',1,1,1)
        summary,_,_=vox.analyze_volume(red,known,str(out/'known_roi'),st['pitch'],1)
        auto,params=vox.roi_volume(red,vox.roi_params(),vox.ROI_STEP,vox.ROI_SMOOTH_Z,vox.roi_ds(red.shape))
        dice=2*(auto&known).sum()/(auto.sum()+known.sum())
        result['vox']=dict(porosity_true=1-fraction,porosity_known_roi=summary['porosita_totale'],dice_auto_roi=float(dice),roi_true_voxels=int(known.sum()),roi_auto_voxels=int(auto.sum()),fast_edt_available=vox._edt_mod is not None,fast_sitk_available=vox._sitk is not None)
        np.savez_compressed(out/'roi_synthetic_central_slice.npz',image=red[len(red)//2],known=known[len(red)//2],automatic=auto[len(red)//2])
    result['interpretation']='Synthetic tests only; low Dice is an unresolved limitation, not a pass.'
    (out/'metrics.json').write_text(json.dumps(result,indent=2))
    return result
