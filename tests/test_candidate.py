import numpy as np
from snackmorph import jpeg, vox

def test_subpixel_axis_aligned_width():
    m=np.zeros((41,41),bool); m[5:36,15:25]=True
    w,_,_=jpeg.chord_subpixel(m,19.5,20,1,0)
    assert np.isclose(w,10)

def test_axial_envelope_internal_gap():
    v=np.full((20,40,40),400,dtype=np.uint16)
    v[3:17,8:32,8:32]=4500;v[8:10]=400
    r,meta=vox.roi_axial_envelope(v,max_gap=3)
    assert r[8:10,8:32,8:32].all()
    assert not r[:3].any() and not r[17:].any()
    assert meta['interpolated_slices']==2

def test_midpoint_known_two_phase():
    v=np.full((10,20,20),400.,dtype=np.float32);v[:,:,10:]=4500
    r=np.ones(v.shape,bool)
    _,t,m,p,_=vox.segment_midpoint(v,r,sigma=0,min_obj=1)
    assert t==2450 and np.array_equal(m,v==4500) and np.array_equal(p,v==400)


def test_profile_table_width_method(monkeypatch):
    import pandas as pd
    calls=[]
    def fake_width(mask, *, method):
        calls.append(method)
        return {f: 10.0 if f==.5 else 8.0 for f in jpeg.FRACS}, 50.0
    monkeypatch.setattr(jpeg, 'width_normals', fake_width)
    samples={(0,0):{'A':np.ones((2,2),bool),'B':np.ones((2,2),bool)}}
    cal=pd.DataFrame([dict(lotto='B-02',t_gg=0,tecnologia='MW',potenza=40,tau=.2,d_ini=1.,d_cal=2.)])
    a=jpeg.profile_table(samples,'B02_0',[('B-02',0)],cal)
    b=jpeg.profile_table(samples,'B02_0',[('B-02',0)],cal,width_method='subpixel')
    assert calls==['legacy','legacy','subpixel','subpixel']
    assert len(b)==46 and np.allclose(b.loc[b.f==.5,'D'],2.)
    pd.testing.assert_frame_equal(a,b)
