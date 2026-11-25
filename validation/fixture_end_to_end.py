"""Post-hoc diagnostic on existing reserved fixtures; no model tuning."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
import cv2
from snackmorph import vox
from snackmorph.physical import configure

def evaluate(args):
    root,case,group,variant=args
    cv2.setNumThreads(1)
    d=Path(root)/case; path=str(d/(case+'.VOX'))
    st=vox.resolve_settings(path); reader=vox.open_volume(path,st)
    img=vox.sample_volume(reader,'ogni N',1,1,1)
    with np.load(d/'truth.npz',allow_pickle=False) as f: lab=f['labels']
    true_roi=(lab==1)|(lab==2); true_pores=lab==1
    pitch=float(reader.pitch)
    configure(1,pitch,img.shape,'legacy'); vox._edt_mod=vox._sitk=None
    auto,_=vox.roi_volume(reader,vox.roi_params(),step=vox.ROI_STEP,smooth_z=vox.ROI_SMOOTH_Z,ds=vox.roi_ds(reader.shape))
    truth=100*true_pores.sum()/true_roi.sum(); out=[]
    for mode,roi in [('known',true_roi),('fixture_auto',auto)]:
        r=dict(case=case,group=group,variant=variant,mode=mode,reference_porosity_pct=truth)
        try:
            im,rc,info=vox.prepare_working(img,roi,1,vox.PAD_VOXELS)
            _,T,material,pores,exterior=vox.segment(im,rc,vox.SEG_SIGMA,vox.THRESHOLD,vox.MIN_OBJECT_VOXELS)
            por,_,_=vox.porosity_open_closed(pores,exterior,rc,vox.CONNECTIVITY)
            pred=np.zeros(lab.shape,bool); sl=tuple(slice(o,o+s) for o,s in zip(info['origin'],rc.shape));pred[sl]=pores
            r.update(status='ok',porosity_pct=100*por['porosita_totale'],signed_error_pp=100*por['porosita_totale']-truth,pore_dice=2*(pred&true_pores).sum()/(pred.sum()+true_pores.sum()),threshold=T,roi_dice=2*(roi&true_roi).sum()/(roi.sum()+true_roi.sum()))
        except Exception as e:r.update(status='failed',error=repr(e))
        out.append(r)
    return out

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=2);a=p.parse_args()
    m=pd.read_csv(a.data/'manifest.csv');m=m[m.split=='test'];jobs=[(str(a.data),r.case,r.group,r.variant) for r in m.itertuples()]
    a.out.parent.mkdir(parents=True,exist_ok=True);rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for j,rs in enumerate(ex.map(evaluate,jobs),1):
            rows.extend(rs);pd.DataFrame(rows).to_csv(a.out,index=False);print(j,len(jobs),rs,flush=True)
if __name__=='__main__':main()
