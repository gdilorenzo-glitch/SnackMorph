"""Evaluate legacy fixture ROI, including axial interpolation and slice fixture masks."""
import argparse,json,time
from pathlib import Path
import numpy as np
import pandas as pd
from snackmorph import vox

def metrics(pred,truth):
    a=int(pred.sum());b=int(truth.sum());tp=int((pred&truth).sum());u=a+b-tp
    return dict(dice=2*tp/(a+b) if a+b else 1.,iou=tp/u if u else 1.,precision=tp/a if a else (1. if not b else 0.),recall=tp/b if b else (1. if not a else 0.))

def roi_metrics(pred,labels):
    truth=(labels==1)|(labels==2);m=metrics(pred,truth);a=int(pred.sum());b=int(truth.sum())
    m.update(sample_loss_fraction=float((truth&~pred).sum()/b),fixture_fraction_of_pred=float((pred&((labels==3)|(labels==4))).sum()/a) if a else 0.,glue_leak_voxels=int((pred&(labels==3)).sum()),holder_leak_voxels=int((pred&(labels==4)).sum()),relative_volume_error=(a-b)/b)
    return m

def main(data,out,split):
    data=Path(data);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    manifest=pd.read_csv(data/'manifest.csv');sections=pd.read_csv(data/'sections.csv');cases=manifest[manifest.split==split]
    if cases.empty:raise ValueError('No cases in split')
    for i,row in enumerate(cases.itertuples(),1):
        case=row.case;dest=out/(case+'.json');print(f'[{i}/{len(cases)}] {case}',flush=True)
        if dest.exists():print('  checkpoint',flush=True);continue
        d=data/case;start=time.monotonic();volume=dict(case=case,group=row.group,split=split,variant=row.variant);slices=[]
        try:
            path=str(d/(case+'.VOX'));st=vox.resolve_settings(path);reader=vox.open_volume(path,st)
            with np.load(d/'truth.npz') as f:labels=f['labels']
            if tuple(reader.shape)!=labels.shape or not np.isin(labels,[0,1,2,3,4]).all():raise ValueError('Invalid labels or dimensions')
            if reader.header_bytes!=0 or abs(reader.pitch-row.pitch_um)>1e-8:raise ValueError('Unexpected header or pitch')
            p=vox.roi_params();ds=vox.roi_ds(reader.shape)
            if ds!=1:raise ValueError('Fixture grid expected no extra XY subsampling')
            pred,used=vox.roi_volume(reader,p,step=vox.ROI_STEP,smooth_z=vox.ROI_SMOOTH_Z,ds=ds)
            volume.update(status='ok',**roi_metrics(pred,labels),t1=used['t1'],t2=used['t2'],step_z=vox.ROI_STEP,smooth_z=vox.ROI_SMOOTH_Z)
            for z in sections.loc[sections.case==case,'z']:
                z=int(z);s=dict(case=case,group=row.group,variant=row.variant,z=z,status='ok')
                try:
                    r=vox.make_roi_slice(reader[z],**used);lab=labels[z]
                    for name,mask in [('roi',(lab==1)|(lab==2)),('glue',lab==3),('wedge',lab==4)]:s.update({name+'_'+k:v for k,v in metrics(r[name],mask).items()})
                    s.update({'roi_'+k:v for k,v in roi_metrics(r['roi'],lab).items()});s['interpolated_roi_dice']=roi_metrics(pred[z],lab)['dice']
                except Exception as e:s.update(status='failed',error=repr(e))
                slices.append(s)
        except Exception as e:volume.update(status='failed',error=repr(e))
        volume['seconds']=time.monotonic()-start;tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(dict(volume=volume,slices=slices),indent=2));tmp.replace(dest);print(volume,flush=True)
    records=[json.loads((out/(c+'.json')).read_text()) for c in cases.case]
    vol=pd.DataFrame([r['volume'] for r in records]);sl=pd.DataFrame([s for r in records for s in r['slices']]);vol.to_csv(out/'volume_metrics.csv',index=False);sl.to_csv(out/'slice_metrics.csv',index=False)
    print(vol[['case','status']+[k for k in ['dice','sample_loss_fraction','fixture_fraction_of_pred'] if k in vol]].to_string(index=False),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',required=True);p.add_argument('--out',required=True);p.add_argument('--split',choices=['development','test'],default='development');a=p.parse_args();main(a.data,a.out,a.split)
