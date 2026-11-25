import numpy as np
import pandas as pd
from snackmorph import jpeg, vox
from snackmorph.statistics import compare_ct_blocks

def test_fit_units_and_identity():
    f=np.array(jpeg.FRACS); di=5.5; A=4.4
    r=jpeg.fit_profile(f,jpeg.profile_model(f,di,A,.4,5.6),di)
    out=jpeg.explicit_amplitude(pd.DataFrame([dict(d_ini=di,**r)])).iloc[0]
    assert len(f)==23
    assert np.isclose(out.A_mm,A,atol=1e-6)
    assert np.isclose(out.a,.8,atol=1e-6)
    assert np.isclose(out.Pk,1+out.a)
    assert np.isclose(out.ED_model,1+out.a*out.Le)

def test_colour_descriptors():
    d=jpeg.colour_descriptors(pd.DataFrame({'Lc':[50.,50.],'ac':[3.,0.],'bc':[4.,0.]}))
    assert np.isclose(d.Cstar.iloc[0],5)
    assert np.isclose(d.h_deg.iloc[0],53.130102354)
    assert np.isnan(d.h_deg.iloc[1])
    assert np.isclose(jpeg.delta_e76([50,3,4],[50,0,0]),5)

def test_vox_roundtrip(tmp_path):
    x=np.arange(3*4*5,dtype=np.uint16).reshape(3,4,5); p=tmp_path/'tiny.vox'
    vox.write_vox(str(p),x,8.9); st=vox.resolve_settings(str(p)); r=vox.open_volume(str(p),st)
    assert r.shape==x.shape
    assert np.isclose(st['pitch'],8.9)
    np.testing.assert_array_equal(vox.sample_volume(r,'media',1,1,1),x)

def test_jpeg_source_manifest_separate_lots():
    assert jpeg.PHOTOS['B03_0']['lots']==[('B-03',0)]
