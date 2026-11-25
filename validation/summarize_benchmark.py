"""Descriptive errors only: no retrospective acceptance criteria or independent-replicate claims."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def err(g, pred, ref, scale=1):
    a=pd.to_numeric(g[pred],errors='coerce').to_numpy(); b=pd.to_numeric(g[ref],errors='coerce').to_numpy(); valid=np.isfinite(a)&np.isfinite(b); a,b=a[valid],b[valid]; d=(a-b)*scale
    if not len(d): return dict(n=0)
    nz=b!=0
    return dict(n=len(d),bias=float(d.mean()),MAE=float(abs(d).mean()),RMSE=float(np.sqrt(np.mean(d*d))),median_abs=float(np.median(abs(d))),max_abs=float(abs(d).max()),median_abs_relative_pct=float(np.median(abs((a[nz]-b[nz])/b[nz]))*100) if nz.any() else np.nan)

def summarize(out):
    out=Path(out); rows=[]
    for kind in ('jpeg','vox'):
        p=out/f'{kind}_metrics.csv'
        if not p.exists(): continue
        d=pd.read_csv(p); keys=['split','variant','family']+(['roi_mode'] if kind=='vox' else [])
        pairs= [('length_mm','length_ref_mm',1),('ED','ED_ref',1),('centre_mm','centre_ref_mm',1),('Pk','Pk_ref',1),('Le','Le_ref',1),('L','L_ref',1),('a','a_ref',1),('b','b_ref',1)] if kind=='jpeg' else [('porosity_total','porosity_total_ref',100),('porosity_open','porosity_open_ref',100),('porosity_closed','porosity_closed_ref',100),('roi_mm3','roi_mm3_ref',1),('components','components_ref',1),('pore_thickness_um','pore_thickness_ref_um',1),('wall_thickness_um','wall_thickness_ref_um',1),('pore_thickness_truth_mask_um','pore_thickness_ref_um',1),('wall_thickness_truth_mask_um','wall_thickness_ref_um',1)]
        for k,g in d.groupby(keys,dropna=False):
            base=dict(pipeline=kind,**dict(zip(keys,k)),n_groups=g.group.nunique(),n_rows=len(g))
            for pred,ref,scale in pairs:
                if pred not in g or ref not in g: continue
                rows.append(dict(base,metric=pred,**err(g,pred,ref,scale)))
            for metric in (['dice','iou','deltaE76'] if kind=='jpeg' else ['roi_dice','solid_dice','pore_dice','open_dice','closed_dice']):
                if metric not in g: continue
                x=g[metric].dropna(); rows.append(dict(base,metric=metric,n=len(x),mean=x.mean(),median=x.median(),minimum=x.min(),maximum=x.max()))
        if kind=='jpeg':
            for k,g in d.groupby(keys,dropna=False):
                base=dict(pipeline=kind,**dict(zip(keys,k)),n_groups=g.group.nunique(),n_rows=len(g))
                for m in ['matched','geometry_ok','colour_ok','fit_ok','cell_correct']:
                    if m in g: rows.append(dict(base,metric=m,n=int(g[m].notna().sum()),success_count=int(g[m].eq(True).sum())))
        else:
            for k,g in d.groupby(keys,dropna=False): rows.append(dict(pipeline=kind,**dict(zip(keys,k)),n_groups=g.group.nunique(),n_rows=len(g),metric='status_ok',n=len(g),success_count=int(g.status.eq('ok').sum())))
    p=out/'jpeg_widths.csv'
    if p.exists():
        d=pd.read_csv(p); keys=['split','variant','family'];
        for k,g in d.groupby(keys,dropna=False): rows.append(dict(pipeline='jpeg',**dict(zip(keys,k)),n_groups=g.group.nunique(),n_rows=len(g),metric='width_mm',**err(g,'width_mm','width_ref_mm')))
    if rows: pd.DataFrame(rows).to_csv(out/'descriptive_errors.csv',index=False)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('out');summarize(p.parse_args().out)
