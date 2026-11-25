"""Independent digital phantoms, ZYX little-endian uint16 plus XML; no SnackMorph imports."""
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi

def main(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];features=[];N=128;families=['closed_spheres','open_channels','lamellae','oriented_ellipsoids','mixed_network'];pitches=[8.9,17.8,26.7,35.6,35.6]
 for g in range(15):
  group=f'V{g+1:02}';split='development' if g<5 else 'test';family=families[g%5];level=g//5;p=pitches[(g+level)%5];z,y,x=np.ogrid[:N,:N,:N];z=(z-(N-1)/2)*p;y=(y-(N-1)/2)*p;x=(x-(N-1)/2)*p;R=48*p;H=104*p;roi=np.broadcast_to((x*x+y*y<=R*R)&(abs(z)<=H/2),(N,N,N)).copy();pore=np.zeros_like(roi)
  def record(kind,**kw):features.append(dict(group=group,type=kind,**kw))
  if family=='closed_spheres':
   r=p*[6,9,12][level]
   for cz,cy,cx in [(-23,-20,-22),(23,20,-22),(0,-19,22),(0,20,22)]:
    pore|=((x-cx*p)**2+(y-cy*p)**2+(z-cz*p)**2<=r*r);record('sphere',diameter_um=2*r,volume_um3=4*math.pi*r**3/3,center_zyx_um=[cz*p,cy*p,cx*p])
  elif family=='open_channels':
   spacing=[24,20,19][level]*p;r=[7,8,8.5][level]*p
   for cy in range(-2,3):
    for cx in range(-2,3):
     if math.hypot(cx*spacing,cy*spacing)+r<R-2*p:
      pore|=np.broadcast_to((x-cx*spacing)**2+(y-cy*spacing)**2<=r*r,roi.shape);record('axial_cylinder',diameter_um=2*r,volume_um3=math.pi*r*r*H,center_yx_um=[cy*spacing,cx*spacing],axis='z')
  elif family=='lamellae':
   wall=[6,4,3][level]*p;gap=[7,10,17][level]*p;pore|=np.broadcast_to(np.mod(z+H/2,wall+gap)>=wall,roi.shape);record('lamellae',wall_nominal_um=wall,gap_nominal_um=gap,axis='z',note='Edges truncated; nominal interior thickness only')
  elif family=='oriented_ellipsoids':
   a=[15,18,22][level]*p;b=[6,8,10][level]*p;theta=np.deg2rad([0,30,55][level]);c,s=np.cos(theta),np.sin(theta)
   for cy in [-22,22]:
    for cx in [-20,20]:
     xx=x-cx*p;yy=y-cy*p;u=c*z+s*xx;v=-s*z+c*xx;pore|=((u/a)**2+(v/b)**2+(yy/b)**2<=1);record('ellipsoid',major_diameter_um=2*a,minor_diameter_um=2*b,volume_um3=4*math.pi*a*b*b/3,orientation_degrees_from_z=[0,30,55][level])
  else:
   spacing=[25,21,18][level]*p;r=[6,7,7.5][level]*p
   for a in [-1,0,1]:
    for b in [-1,0,1]:
     pore|=np.broadcast_to((x-a*spacing)**2+(y-b*spacing)**2<=r*r,roi.shape);pore|=np.broadcast_to((z-a*spacing)**2+(y-b*spacing)**2<=r*r,roi.shape);pore|=np.broadcast_to((z-a*spacing)**2+(x-b*spacing)**2<=r*r,roi.shape)
   record('intersecting_channel_network',channel_diameter_um=2*r,spacing_um=spacing,note='Overlaps: do not sum primitive volumes')
  pore&=roi;solid=roi&~pore;st=ndi.generate_binary_structure(3,1);labels,n=ndi.label(pore,structure=st);ids=np.unique(labels[ndi.binary_dilation(~roi,structure=st)&pore]);ids=ids[ids>0];opened=np.isin(labels,ids);closed=pore&~opened
  for variant in ['clean','degraded']:
   vid=f'{group}_{variant}';folder=out/vid;folder.mkdir(exist_ok=True);arr=np.full(roi.shape,400,np.float32);arr[solid]=4500
   if variant=='degraded':
    support=np.broadcast_to((z<-56*p)&(x*x+y*y<(45*p)**2),roi.shape);arr[support]=2500;arr=ndi.gaussian_filter(arr,.75);arr+=np.random.default_rng(930000+g).normal(0,18,arr.shape).astype(np.float32)
   np.clip(np.rint(arr),0,65535).astype('<u2').tofile(folder/f'{vid}.VOX');(folder/f'{vid}.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><data_info><volume type="word" width="{N}" height="{N}" stack="{N}" pitch="{p}" path="{vid}.VOX"/></data_info>');np.savez_compressed(folder/'truth.npz',roi=roi,solid=solid,pores=pore,open_pores=opened,closed_pores=closed);v=roi.sum();rows.append(dict(volume_id=vid,group=group,split=split,family=family,variant=variant,shape_zyx='128x128x128',pitch_um=p,roi_voxels=v,solid_voxels=solid.sum(),pore_voxels=pore.sum(),roi_mm3=v*(p/1000)**3,porosity_total=pore.sum()/v,porosity_open=opened.sum()/v,porosity_closed=closed.sum()/v,connected_pore_components_6=n,open_components_6=len(ids),closed_components_6=n-len(ids),noise_sd=18 if variant=='degraded' else 0,blur_sigma_vox=.75 if variant=='degraded' else 0))
  print(group,family,round(pore.sum()/roi.sum(),3),flush=True)
 with (out/'manifest_truth.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (out/'primitive_geometry.json').write_text(json.dumps(features,indent=2));(out/'README.md').write_text('''# Independent synthetic VOX benchmark\n15 geometries, each clean/degraded: 30 volumes. Five development and ten test groups. Synthetic headerless little-endian uint16 arrays and XML, not scanner exports. Truth.npz contains ROI, solid, pores, open and closed pore masks. Porosities are exact discrete mask fractions; open pores use six-neighbour connectivity to exterior. Match connectivity convention. Watershed objects are not connected components. Primitive dimensions are continuous mathematical reference values; ellipsoid orientation is not a numerical reference for MIL anisotropy. Lamellar thickness is nominal interior only. For sampled grids create aligned reference masks, record crop and phase. Degraded cases simulate blur, noise and separate support but are not calibrated scanner models. Evaluate known ROI and automatic ROI separately; freeze settings on development groups before test. The test reference is supplied, not cryptographically blind.\n''')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);main(p.parse_args().out)
