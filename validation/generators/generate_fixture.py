"""Independent synthetic fixtures inspired by archived CT overlays; not scanner calibrated."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
SHAPE=(32,320,320); PITCH=35.6

def geometry(g):
    rng=np.random.default_rng(820100+g)
    z,y,x=np.indices(SHAPE,dtype=np.float32)
    z-=(SHAPE[0]-1)/2;y-=(SHAPE[1]-1)/2;x-=(SHAPE[2]-1)/2
    angle=[-15,15,0,30,-35,60,95,135,180,215,250,285,320,-60,45][g]
    t=np.deg2rad(angle);u=x*np.cos(t)+y*np.sin(t);v=-x*np.sin(t)+y*np.cos(t)
    u-=(g%3-1)*4+2*np.sin(z/9);v-=3*np.sin(z/13+g)
    r=float(rng.uniform(87,101));holder=(u*u+v*v<=r*r)&(v<=0)
    span=float(rng.uniform(.66,.95))*r;base=[8,14,21][g%3]
    depth=base+4*np.sin(u/13+g)+3*np.cos(z/7+u/20)+8*np.exp(-((u-.65*span)/18)**2)
    glue=(abs(u)<=span)&(v>=-3)&(v<=depth)
    if g%3==2:glue|=((u-.84*r)**2+(v+1)**2<=15**2)
    glue&=~holder
    uc=u-float(rng.uniform(-13,13))-3*np.sin(z/10+g);vc=v-(72+2*np.sin(z/8))
    rx=float(rng.uniform(59,76));ry=float(rng.uniform(65,76));theta=np.arctan2(vc/ry,uc/rx)
    rad=np.sqrt((uc/rx)**2+(vc/ry)**2);boundary=1+.055*np.sin(3*theta+g+z/18)+.035*np.cos(5*theta-z/10)
    roi=(rad<=boundary)&~holder&~glue
    spacing=[24,29,35,31,27][g%5];thickness=[2.,2.6,3.3,2.3,1.7][g%5]
    seeds=np.array([(a,b,c) for a in np.arange(-45,46,spacing) for b in np.arange(-110,111,spacing) for c in np.arange(-110,111,spacing)],float)
    seeds+=rng.uniform(-.31*spacing,.31*spacing,seeds.shape)
    dist,_=cKDTree(seeds).query(np.column_stack([z[roi],vc[roi],uc[roi]]),k=2,workers=1)
    walls=np.zeros(SHAPE,bool);walls[roi]=dist[:,1]-dist[:,0]<=thickness
    walls|=(rad>=boundary-.035)&roi&(np.sin(4*theta+g+z/12)>-.68)
    labels=np.zeros(SHAPE,np.uint8);labels[roi]=1;labels[walls]=2;labels[glue]=3;labels[holder]=4
    return labels,dict(group=f'F{g+1:02}',seed=820100+g,angle_deg=angle,holder_radius_px=r,glue_half_span_px=span,glue_base_px=base,sample_rx_px=rx,sample_ry_px=ry,cell_seed_spacing_px=spacing,wall_distance_threshold_px=thickness,wrap=bool(g%3==2))

def main(out,groups=15):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];sections=[];params=[]
    for g in range(groups):
        labels,meta=geometry(g);group=meta['group'];split='development' if g<5 else 'test';params.append(meta)
        roi=(labels==1)|(labels==2);por=float((labels==1).sum()/roi.sum());assert all(np.any(labels==k) for k in range(5))
        for variant in ('clean','degraded'):
            case=f'{group}_{variant}';d=out/case;d.mkdir(exist_ok=True)
            rng=np.random.default_rng(830000+g);bg=400.;solid=float(rng.uniform(2300,5100));holder=float(rng.uniform(3800,5900));glue=float(rng.uniform(11000,18000))
            arr=np.array([bg,bg,solid,glue,holder],np.float32)[labels];blur=noise=0.
            if variant=='degraded':
                blur=float(rng.uniform(.55,1.1));noise=float(rng.uniform(30,110));arr=ndi.gaussian_filter(arr,blur)
                arr=arr*np.linspace(.91,1.09,SHAPE[2],dtype=np.float32)[None,None,:]+rng.normal(0,noise,SHAPE).astype(np.float32)
            np.clip(np.rint(arr),0,65535).astype('<u2').tofile(d/(case+'.VOX'))
            (d/(case+'.xml')).write_text(f'<?xml version="1.0" encoding="UTF-8"?><data_info><volume type="word" width="{SHAPE[2]}" height="{SHAPE[1]}" stack="{SHAPE[0]}" pitch="{PITCH}" path="{case}.VOX"/></data_info>')
            np.savez_compressed(d/'truth.npz',labels=labels)
            rows.append(dict(case=case,group=group,split=split,variant=variant,pitch_um=PITCH,shape_zyx='x'.join(map(str,SHAPE)),roi_voxels=int(roi.sum()),porosity=por,glue_voxels=int((labels==3).sum()),holder_voxels=int((labels==4).sum()),background_intensity=bg,solid_intensity=solid,holder_intensity=holder,glue_intensity=glue,blur_sigma_vox=blur,noise_sd=noise))
            for zz in ([4,12,20,28] if g<5 else [4,16,28]):sections.append(dict(case=case,group=group,split=split,variant=variant,z=zz))
        print(group,f'porosity={por:.3f}',flush=True)
    for name,records in [('manifest.csv',rows),('sections.csv',sections)]:
        with (out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (out/'geometry.json').write_text(json.dumps(dict(shape_zyx=SHAPE,pitch_um=PITCH,inspiration_scans=['CT_20260624_143241','CT_20260624_153718','CT_20260626_132154','CT_20260629_143846'],parameters=params),indent=2))
    (out/'README.md').write_text('''# Fixture benchmark v1\nShort synthetic axial segments, not full extrudates or calibrated CT simulations. 15 geometric groups, each clean/degraded, 30 volumes and 100 indexed sections of those same volumes (not independent). Development F01–F05 (10 volumes, 40 slices); reserved test F06–F15 (20 volumes, 60 slices). Truth labels: 0 background, 1 pore inside ROI, 2 sample solid, 3 adhesive, 4 holder. ROI = 1 or 2. Mutually exclusive voxel labels precede intensity simulation. Geometry inspired by archived ROI overlays: circular-segment holder, inclined interface, asymmetric adhesive and porous irregular sample. Dimensions, intensities, blur and noise are model assumptions, not measured native 16-bit scanner calibration. Clean/degraded share geometry. No real data distributed. Test ground truth is supplied but must not be used for development.\n''')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--groups',type=int,default=15,choices=range(1,16));a=p.parse_args();main(a.out,a.groups)
