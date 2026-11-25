"""Exploratory fixture diagnostic, independent 2D labels; not calibrated scanner data.
Does not alter the versioned benchmark archive or use the held-out cases.
"""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from snackmorph import vox


def fixture(angle=0, blur=0., seed=2026):
    # Porous ring / web, glue touches its bottom; triangular support touches glue.
    y,x=np.ogrid[:192,:192]; x=x-96; y=y-96
    roi=(x*x+(y+24)**2<=42**2)
    holes=np.zeros_like(roi)
    for cy in (-48,-24,0):
        for cx in (-24,0,24):
            holes|=((x-cx)**2+(y-cy)**2<=8**2)
    walls=roi&~holes
    glue=(abs(x)<=13)&(y>=16)&(y<=29)&~roi
    wedge=(y>=30)&(y<=76)&(abs(x)<=16+(y-30)*.9)
    masks=np.stack([roi,walls,glue,wedge])
    if angle:
        masks=np.stack([ndi.rotate(m.astype('uint8'),angle,reshape=False,order=0)>0 for m in masks])
    roi,walls,glue,wedge=masks
    im=np.full(roi.shape,400.,np.float32); im[walls]=4500; im[wedge]=5000; im[glue]=15000
    if blur:
        im=ndi.gaussian_filter(im,blur); im+=np.random.default_rng(seed).normal(0,25,im.shape).astype('float32')
    return im,dict(roi=roi,walls=walls,glue=glue,wedge=wedge)


def dice(a,b):
    den=int(a.sum()+b.sum()); return 2*int((a&b).sum())/den if den else 1.


def main(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True); rows=[]
    for angle in (0,30,60):
        for blur in (0.,.75):
            im,t=fixture(angle,blur); name=f'angle{angle}_blur{blur}'; row=dict(case=name,angle_deg=angle,blur_sigma=blur)
            try:
                r=vox.make_roi_slice(im,**vox.roi_params()); row.update(status='ok',**{k+'_dice':dice(r[k],t[k]) for k in ('roi','glue','wedge')},fixture_leak_pixels=int((r['roi']&(t['glue']|t['wedge'])).sum()),sample_loss_fraction=float((t['roi']&~r['roi']).sum()/t['roi'].sum()),t1=r['t1'],t2=r['t2']); np.savez_compressed(out/(name+'.npz'),image=im,**{'truth_'+k:v for k,v in t.items()},**{'pred_'+k:r[k] for k in ('roi','glue','wedge')})
            except Exception as e: row.update(status='failed',error=str(e))
            rows.append(row); print(row,flush=True)
    pd.DataFrame(rows).to_csv(out/'fixture_diagnostic.csv',index=False)
    (out/'limitations.json').write_text(json.dumps({'purpose':'exploratory slice-level fixture separation','calibration':'arbitrary geometry and attenuation; not measured support/glue','scope':'not full 3D ROI interpolation validation, not held-out test, no tuning'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);main(p.parse_args().out)
