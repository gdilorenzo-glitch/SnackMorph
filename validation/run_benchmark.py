"""Independent benchmark of core SnackMorph routines. Development first; test only after protocol freeze."""
import argparse, hashlib, json, platform, sys, time, traceback, warnings
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import numpy as np
import pandas as pd
import cv2
from scipy import ndimage as ndi
from scipy.optimize import linear_sum_assignment
from PIL import Image
from snackmorph import jpeg, vox
from snackmorph.physical import configure

ROOT=Path(__file__).resolve().parents[1]
FRACS=np.asarray(jpeg.FRACS)

def dice(a,b):
    den=int(a.sum()+b.sum()); return 2*int(np.count_nonzero(a&b))/den if den else 1.

def raw_colour(m, lab):
    # Same body selection and uncorrected median as jpeg.colour_tables; no reference-based correction.
    yy,xx=np.nonzero(m); pts=np.c_[xx,yy].astype(float); p=pts-pts.mean(0)
    u=np.linalg.svd(p,full_matrices=False)[2][0]; s=p@u
    body=np.zeros_like(m); keep=abs(s-np.median(s))<=.3*np.ptp(s)
    body[yy[keep],xx[keep]]=True; body &= ndi.binary_erosion(m,iterations=3)
    if not body.any(): return np.full(3,np.nan)
    return np.median(lab[body],axis=0)

def jpeg_case(root, row, truth, profiles):
    iid=row.image_id; px=float(row.pixel_size_mm); t0=time.perf_counter()
    truth=truth.sort_values('label').reset_index(drop=True)
    labels=np.asarray(Image.open(root/'labels'/f'{iid}.png'))
    im,samples=jpeg.segment_photo(str(root/'images'/f'{iid}.jpg'),int(row.rows))
    lab=cv2.cvtColor(im.astype(np.float32)/255,cv2.COLOR_BGR2LAB)
    preds=[]; cover=np.zeros(labels.shape,np.uint8)
    for (r,c),d in sorted(samples.items()):
        y0,y1,x0,x1=d['box']; sl=(slice(y0,y1),slice(x0,x1))
        for name in ('A','B'):
            m=d[name]
            if m.any():
                preds.append((r,c,name,sl,m)); cover[sl]+=m.astype(np.uint8)
    area=np.bincount(labels.ravel(),minlength=37)[1:37].astype(float)
    overlap=np.array([np.bincount(labels[sl][m],minlength=37)[1:37] for _,_,_,sl,m in preds]).reshape(-1,36)
    predarea=np.array([m.sum() for _,_,_,_,m in preds]); union=predarea[:,None]+area[None,:]-overlap
    iou=np.divide(overlap,union,out=np.zeros_like(overlap,dtype=float),where=union>0)
    pi,ti=linear_sum_assignment(-iou); matches={int(t):int(p) for p,t in zip(pi,ti) if overlap[p,t]>0}
    records=[]; widths=[]
    for t,ref in truth.iterrows():
        rec=dict(image_id=iid,group=row.group,split=row.split,variant=row.variant,label=int(ref.label),family=ref.family,matched=False,geometry_ok=False,colour_ok=False,fit_ok=False,dice=0.,iou=0.)
        records.append(rec)
        if t not in matches: continue
        p=matches[t]; r,c,name,sl,m=preds[p]; rec.update(matched=True,iou=iou[p,t],dice=2*overlap[p,t]/(area[t]+predarea[p]),cell_correct=bool(r==ref.row and c==ref.col),pred_row=r,pred_col=c,pred_object=name)
        try:
            w,L=jpeg.width_normals(m); D=np.asarray([w[f]*px for f in FRACS]); L=float(L)*px
            # Same preprocessing as width_normals, for orientation only. Reverse on reference axis dot product, not on errors.
            yy,xx=np.nonzero(m); oy,ox=max(yy.min()-15,0),max(xx.min()-15,0)
            ax=jpeg.axis_pca(jpeg.clean(m[oy:yy.max()+16,ox:xx.max()+16]))
            pr=profiles.loc[profiles.label==ref.label].sort_values('fraction')
            direction=pr[['centre_x_px','centre_y_px']].iloc[-1].to_numpy()-pr[['centre_x_px','centre_y_px']].iloc[0].to_numpy()
            reverse=bool(np.dot(ax[-1]-ax[0],direction)<0)
            if reverse: D=D[::-1]
            if not np.all(np.isfinite(D)) or np.any(D<=0) or not np.isfinite(L) or L<=0: raise ValueError('invalid width/length')
            ed=float(D[np.isin(FRACS,[.125,.375,.625,.875])].mean()/ref.d_initial_mm)
            rec.update(geometry_ok=True,length_mm=L,length_ref_mm=ref.length_mm,ED=ed,ED_ref=ref.ED_ref,orientation_reversed=reverse,centre_mm=D[np.argmin(abs(FRACS-.5))],centre_ref_mm=ref.centre_diameter_mm)
            for f,d,dr in zip(FRACS,D,pr.diameter_mm): widths.append(dict(image_id=iid,group=row.group,split=row.split,variant=row.variant,family=ref.family,label=int(ref.label),fraction=f,width_mm=d,width_ref_mm=dr,dice=rec['dice']))
            if pd.notna(ref.Pk_model_ref):
                fit=jpeg.fit_profile(FRACS,D,float(ref.d_initial_mm)); rec.update(fit_ok=True,Pk=fit['Pk'],Pk_ref=ref.Pk_model_ref,Le=fit['Le'],Le_ref=ref.Le_model_ref,R2=fit['R2'])
        except Exception as e: rec['geometry_error']=f'{type(e).__name__}: {e}'
        if str(ref.uniform_colour).lower()=='true':
            try:
                colour=raw_colour(m,lab[sl]); target=np.array([ref.L_ref,ref.a_ref,ref.b_ref],float)
                rec.update(colour_ok=bool(np.isfinite(colour).all()),L=colour[0],a=colour[1],b=colour[2],L_ref=target[0],a_ref=target[1],b_ref=target[2],deltaE76=np.linalg.norm(colour-target))
            except Exception as e: rec['colour_error']=f'{type(e).__name__}: {e}'
    log=dict(image_id=iid,group=row.group,split=row.split,variant=row.variant,status='ok',predicted=len(preds),expected=36,matched=len(matches),unmatched_truth=36-len(matches),unmatched_predicted=len(preds)-len(matches),overlap_pixels=int((cover>1).sum()),foreground_dice=dice(cover>0,labels>0),runtime_s=time.perf_counter()-t0)
    return records,widths,log

def voxel_case(root,row,features):
    vid=row.volume_id; folder=root/vid; t0=time.perf_counter(); path=str(folder/f'{vid}.VOX')
    st=vox.resolve_settings(path); reader=vox.open_volume(path,st); red=vox.sample_volume(reader,'ogni N',1,1,1)
    raw=np.fromfile(path,dtype='<u2').reshape((128,)*3)
    if tuple(st['shape'])!=(128,)*3 or not np.isclose(st['pitch'],row.pitch_um) or reader.header_bytes!=0 or not np.array_equal(red,raw): raise ValueError('raw read mismatch')
    with np.load(folder/'truth.npz',allow_pickle=False) as d: truth={k:d[k] for k in d.files}
    # Legacy defaults, no downsampling or tuning. Disable optional accelerators for reproducible SciPy path.
    configure(1,float(row.pitch_um),red.shape,'legacy'); vox._edt_mod=vox._sitk=None
    p=float(row.pitch_um); records=[]; rois={'known':truth['roi']}
    auto_error=None
    try: rois['automatic'],_=vox.roi_volume(red,vox.roi_params(),vox.ROI_STEP,vox.ROI_SMOOTH_Z,vox.roi_ds(red.shape))
    except Exception as e: auto_error=f'{type(e).__name__}: {e}'
    for mode in ('known','automatic'):
        rec=dict(volume_id=vid,group=row.group,split=row.split,variant=row.variant,family=row.family,roi_mode=mode,read_ok=True,pitch_um=p,status='ok',porosity_total_ref=row.porosity_total,porosity_open_ref=row.porosity_open,porosity_closed_ref=row.porosity_closed,roi_mm3_ref=row.roi_mm3,components_ref=row.connected_pore_components_6)
        records.append(rec); start=time.perf_counter()
        try:
            if mode not in rois: raise ValueError(auto_error)
            roi=rois[mode]; rec.update(roi_dice=dice(roi,truth['roi']),roi_mm3=float(roi.sum())*(p/1000)**3)
            if not roi.any(): raise ValueError('empty ROI')
            img,roi_c,info=vox.prepare_working(red,roi,1,vox.PAD_VOXELS)
            gs,T,material,pores,exterior=vox.segment(img,roi_c,vox.SEG_SIGMA,vox.THRESHOLD,vox.MIN_OBJECT_VOXELS)
            por,labels,lut=vox.porosity_open_closed(pores,exterior,roi_c,vox.CONNECTIVITY)
            sl=tuple(slice(o,o+s) for o,s in zip(info['origin'],roi_c.shape)); full=np.zeros(red.shape,bool); full[sl]=material; rec['solid_dice']=dice(full,truth['solid']); full[sl]=pores; rec['pore_dice']=dice(full,truth['pores']); full[sl]=lut[labels]; rec['open_dice']=dice(full,truth['open_pores']); full[sl]=pores&~lut[labels]; rec['closed_dice']=dice(full,truth['closed_pores'])
            rec.update(threshold=T,porosity_total=por['porosita_totale'],porosity_open=por['porosita_aperta'],porosity_closed=por['porosita_chiusa'],components=por['n_pori_connessi'])
            # Nominal thickness on simple geometry only. Whole sphere/cylinder median is a defined benchmark target;
            # lamella interior excludes edges, no numerical truth for network/ellipsoid.
            if mode=='known' and row.family in ('closed_spheres','open_channels','lamellae'):
                f=features[0]; zz,yy,xx=np.ogrid[tuple(slice(o,o+s) for o,s in zip(info['origin'],roi_c.shape))]; z=(zz-63.5)*p; y=(yy-63.5)*p; x=(xx-63.5)*p
                if row.family=='closed_spheres': core=np.ones(roi_c.shape,bool); target=f['diameter_um']
                elif row.family=='open_channels': target=f['diameter_um']; core=np.broadcast_to(abs(z)<(52*p-target),roi_c.shape)
                else: target=f['gap_nominal_um']; core=np.broadcast_to((abs(z)<(52*p-2*max(target,f['wall_nominal_um'])))&(x*x+y*y<(24*p)**2),roi_c.shape)
                sel=core&pores&truth['pores'][sl]; lt,_=vox.local_thickness(pores,p,vox.PSD_LEVELS)
                rec.update(pore_thickness_ref_um=target,pore_thickness_um=float(np.median(lt[sel])) if sel.any() else np.nan,pore_thickness_eval_voxels=int(sel.sum())); del lt
                if row.family=='lamellae':
                    sel=core&material&truth['solid'][sl]; lt,_=vox.local_thickness(material,p,vox.PSD_LEVELS); rec.update(wall_thickness_ref_um=f['wall_nominal_um'],wall_thickness_um=float(np.median(lt[sel])) if sel.any() else np.nan,wall_thickness_eval_voxels=int(sel.sum())); del lt
        except Exception as e: rec.update(status='failed',error=f'{type(e).__name__}: {e}')
        rec['runtime_s']=time.perf_counter()-start
    return records,dict(volume_id=vid,group=row.group,split=row.split,variant=row.variant,status='ok',runtime_s=time.perf_counter()-t0)

def fingerprint():
    paths=sorted((ROOT/'src'/'snackmorph').glob('*.py'))+[Path(__file__),ROOT/'validation/generators/generate_jpeg.py',ROOT/'validation/generators/generate_vox.py',ROOT/'requirements-tested.txt']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--data',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--split',choices=['development','test'],default='development'); ap.add_argument('--mode',choices=['jpeg','vox','both'],default='both'); ap.add_argument('--pilot',action='store_true'); ap.add_argument('--approved-plan',type=Path); a=ap.parse_args()
    if a.split=='test':
        if a.pilot or not a.approved_plan: ap.error('Test requires an approved frozen analysis plan (no pilot).')
        plan=json.loads(a.approved_plan.read_text());
        if plan.get('code_sha256')!=fingerprint() or not plan.get('criteria') or not plan.get('approved'): ap.error('Plan must contain matching code_sha256, agreed criteria, approved=true.')
    a.out.mkdir(parents=True,exist_ok=True); cv2.setNumThreads(1)
    env={'python':platform.python_version(),'platform':platform.platform(),'split':a.split,'pilot':a.pilot,'mode':a.mode,'code_sha256':fingerprint(),'configuration':{'jpeg':'native segmentation; independent mm/pixel; raw Lab body; maximum IoU assignment with positive overlap; orientation by axis dot product','vox':'native grid; legacy defaults; 6-connected; SciPy; known vs automatic ROI; core descriptors only'}}
    for pkg in ['numpy','pandas','scipy','scikit-image','opencv-python-headless','scikit-learn','Pillow']:
        try: env[pkg]=version(pkg)
        except PackageNotFoundError: env[pkg]='not installed'
    (a.out/'environment.json').write_text(json.dumps(env,indent=2))
    if a.approved_plan: (a.out/'approved_plan.json').write_bytes(a.approved_plan.read_bytes())
    for kind in ['jpeg','vox'] if a.mode=='both' else [a.mode]:
        root=a.data/kind.upper(); m=pd.read_csv(root/('manifest.csv' if kind=='jpeg' else 'manifest_truth.csv')); m=m[m.split==a.split]; idcol='image_id' if kind=='jpeg' else 'volume_id'
        if a.pilot: m=m[(m.variant=='clean') & (m.group.isin(['J01','J02','J03','J04'] if kind=='jpeg' else ['V01','V02','V03','V04','V05']))]
        if kind=='jpeg':
            tr=pd.read_csv(root/'objects_truth.csv'); tr=tr[tr.split==a.split]; pr=pd.read_csv(root/'profiles_truth.csv'); pr=pr[pr.image_id.isin(m.image_id)]
        else: features=json.loads((root/'primitive_geometry.json').read_text())
        for row in m.itertuples(index=False):
            iid=getattr(row,idcol); dest=a.out/kind/iid; dest.mkdir(parents=True,exist_ok=True)
            if (dest/'DONE').exists(): continue
            print(iid,flush=True)
            try:
                with warnings.catch_warnings(record=True) as ws:
                    warnings.simplefilter('always')
                    if kind=='jpeg':
                        records,widths,log=jpeg_case(root,row,tr[tr.image_id==iid],pr[pr.image_id==iid]); pd.DataFrame(widths).to_csv(dest/'widths.csv',index=False)
                    else: records,log=voxel_case(root,row,[f for f in features if f['group']==row.group])
                    pd.DataFrame(records).to_csv(dest/'metrics.csv',index=False)
                    log['warnings']=[str(w.message) for w in ws]
            except Exception as e: log={idcol:iid,'group':row.group,'split':row.split,'variant':row.variant,'status':'failed','error':f'{type(e).__name__}: {e}','traceback':traceback.format_exc()}
            (dest/'log.json').write_text(json.dumps(log,indent=2,default=str)); (dest/'DONE').touch()
            print(iid,log['status'],flush=True)
        for file in ['metrics.csv','widths.csv']:
            dfs=[]
            for path in sorted((a.out/kind).glob('*/'+file)):
                try: dfs.append(pd.read_csv(path))
                except pd.errors.EmptyDataError: pass
            if dfs: pd.concat(dfs,ignore_index=True).to_csv(a.out/f'{kind}_{file}',index=False)
        pd.DataFrame([json.loads(p.read_text()) for p in sorted((a.out/kind).glob('*/log.json'))]).to_csv(a.out/f'{kind}_log.csv',index=False)
if __name__=='__main__': main()
