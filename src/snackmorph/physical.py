"""Parameter policy: match the 35.6 µm reference in physical units where discrete algorithms permit."""
import math
from . import vox
ROI_LENGTH = ['GLUE_MARGIN','WEDGE_MARGIN','WEDGE_OPEN','TOPHAT_R','CLOSE_R','OUTER_MARGIN','CAVITY_CLOSE_R','ATTACH_DIST','WEDGE_REC_MIN_R','WEDGE_INNER_OPEN_R','WEDGE_CLOSE_MIN_R','CAND_OPEN_R','ROI_OPEN_R','CAVITY_NEAR_R']
ROI_AREA = ['MIN_AREA','ATTACH_MIN_AREA','GLUE_MIN_AREA']
LENGTH = ['PAD_VOXELS','SURFACE_EROSION','STEP_2D','ROI_STEP']
AREA = ['MIN_PORE_PIXELS_2D','MIN_ROI_PIXELS_2D']
VOLUME = ['MIN_OBJECT_VOXELS','MIN_PORE_VOXELS','GEOMETRY_MIN_VOXELS']
FLOAT = ['SEG_SIGMA','WATERSHED_H','WATERSHED_SIGMA','SURFACE_SIGMA']
ODD = ['ROI_SMOOTH_Z','ANOMALY_WINDOW']
KEYS = ROI_LENGTH+ROI_AREA+LENGTH+AREA+VOLUME+FLOAT+ODD+['SIGMA','ROI_WORKING_SIZE']
BASE = {k:getattr(vox,k) for k in KEYS}
def nearest(x): return int(math.floor(x+0.5))
def odd(x): return max(1,2*nearest((x-1)/2)+1)
def configure(step, original_pitch, shape, policy):
    for k,v in BASE.items(): setattr(vox,k,v)
    if policy not in ('legacy','physical'): raise ValueError(policy)
    pitch=step*original_pitch
    ref_pitch=4*original_pitch
    ref_shape=tuple(d//4 for d in shape); cur_shape=tuple(d//step for d in shape)
    ref_ds=vox.roi_ds(ref_shape)
    # Keep internal ROI XY grid native for this experiment (historical grid ds=1 for B02).
    if policy=='physical':
        if ref_ds!=1: raise ValueError('Reference ROI grid ds != 1; review policy for this scan')
        vox.ROI_WORKING_SIZE=0
    cur_ds=vox.roi_ds(cur_shape)
    rows=[]
    def setp(k, power, rp, cp, kind):
        old=BASE[k]; target=old*(rp/cp)**power
        if policy=='legacy': new=old
        elif kind=='float': new=target
        elif kind=='odd': new=odd(target)
        elif kind=='minimum': new=max(1,math.ceil(target-1e-10))
        else: new=max(1,nearest(target)) if old else 0
        setattr(vox,k,new)
        rows.append(dict(parameter=k,dimension=power,reference_value=old,effective_value=new,reference_pitch_um=rp,current_pitch_um=cp,reference_physical=old*rp**power,effective_physical=new*cp**power,rounding=kind,relative_physical_error_pct=100*(new*cp**power/(old*rp**power)-1) if old else 0))
    for k in ROI_LENGTH: setp(k,1,ref_pitch*ref_ds,pitch*cur_ds,'nearest')
    for k in ROI_AREA: setp(k,2,ref_pitch*ref_ds,pitch*cur_ds,'minimum')
    setp('SIGMA',1,ref_pitch*ref_ds,pitch*cur_ds,'float')
    for k in LENGTH: setp(k,1,ref_pitch,pitch,'nearest')
    for k in AREA: setp(k,2,ref_pitch,pitch,'minimum')
    for k in VOLUME: setp(k,3,ref_pitch,pitch,'minimum')
    for k in FLOAT: setp(k,1,ref_pitch,pitch,'float')
    for k in ODD: setp(k,1,ref_pitch,pitch,'odd')
    return rows,cur_ds
