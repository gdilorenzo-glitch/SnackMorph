"""Check reference file integrity, not SnackMorph accuracy."""
import argparse,csv,json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from collections import Counter,defaultdict

def read(p):
 with p.open(newline='') as f:return list(csv.DictReader(f))
def check(root):
 root=Path(root);j=root/'JPEG';v=root/'VOX';jm=read(j/'manifest.csv');om=read(j/'objects_truth.csv');pm=read(j/'profiles_truth.csv');vm=read(v/'manifest_truth.csv');assert len(jm)==100 and len(om)==3600 and len(pm)==82800 and len(vm)==30
 for manifest in (jm,vm):
  groups=defaultdict(set)
  for r in manifest:groups[r['group']].add(r['split'])
  assert all(len(s)==1 for s in groups.values())
 for r in jm:
  id=r['image_id'];size=int(r['width']),int(r['height']);im=Image.open(j/'images'/f'{id}.jpg');m=Image.open(j/'labels'/f'{id}.png');assert im.size==m.size==size and set(np.unique(m))==set(range(37));im.verify()
 for r in vm:
  id=r['volume_id'];p=v/id;meta=ET.parse(p/f'{id}.xml').find('volume').attrib;shape=tuple(int(meta[k]) for k in ('stack','height','width'));assert shape==(128,)*3 and float(meta['pitch'])==float(r['pitch_um']);assert (p/f'{id}.VOX').stat().st_size==np.prod(shape)*2
  with np.load(p/'truth.npz',allow_pickle=False) as a:
   roi,solid,pores,opened,closed=[a[k] for k in ('roi','solid','pores','open_pores','closed_pores')];assert all(x.shape==shape and x.dtype==bool for x in (roi,solid,pores,opened,closed));assert np.array_equal(solid|pores,roi) and not np.any(solid&pores);assert np.array_equal(opened|closed,pores) and not np.any(opened&closed);assert roi.sum()==int(r['roi_voxels']) and pores.sum()==int(r['pore_voxels']);assert np.isclose(pores.sum()/roi.sum(),float(r['porosity_total'])) and np.isclose(opened.sum()/roi.sum(),float(r['porosity_open'])) and np.isclose(closed.sum()/roi.sum(),float(r['porosity_closed']))
 return {'JPEG':len(jm),'JPEG_groups':len(set(r['group'] for r in jm)),'JPEG_split':dict(Counter(r['split'] for r in jm)),'JPEG_instance_observations':len(om),'JPEG_profile_rows':len(pm),'VOX':len(vm),'VOX_groups':len(set(r['group'] for r in vm)),'VOX_split':dict(Counter(r['split'] for r in vm)),'porosity_range_percent':[100*min(float(r['porosity_total']) for r in vm),100*max(float(r['porosity_total']) for r in vm)],'status':'integrity checks passed; not a validation result'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');args=p.parse_args();print(json.dumps(check(args.root),indent=2))
