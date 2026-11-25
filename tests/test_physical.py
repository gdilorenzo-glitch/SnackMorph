import unittest, tempfile
from pathlib import Path
import numpy as np
from snackmorph import vox
from snackmorph.physical import configure

class PhysicalTests(unittest.TestCase):
    def test_reference_identity(self):
        rows, ds=configure(4,8.9,(1938,2128,1744),'physical')
        self.assertEqual(ds,1)
        self.assertTrue(all(r['reference_value']==r['effective_value'] for r in rows))
    def test_scaled(self):
        rows,ds=configure(3,8.9,(1938,2128,1744),'physical')
        self.assertEqual(ds,1)
        self.assertAlmostEqual(vox.SEG_SIGMA,4/3)
        self.assertAlmostEqual(vox.WATERSHED_H,4/3)
        self.assertEqual(vox.MIN_PORE_VOXELS,48)
        self.assertEqual(vox.MIN_OBJECT_VOXELS,19)
        self.assertEqual(vox.STEP_2D,4)
        self.assertEqual(vox.WEDGE_OPEN,16)
        self.assertEqual(vox.ROI_SMOOTH_Z,7)
        self.assertEqual(vox.SURFACE_EROSION,3)
    def test_legacy_reset(self):
        configure(3,8.9,(1938,2128,1744),'physical')
        configure(3,8.9,(1938,2128,1744),'legacy')
        self.assertEqual(vox.MIN_PORE_VOXELS,20)
        self.assertEqual(vox.ROI_WORKING_SIZE,512)
    def test_full_small_known_roi(self):
        z,y,x=np.mgrid[:40,:48,:48]
        roi=((z-20)**2+(y-24)**2+(x-24)**2)<18**2
        pores=(((z-20)**2+(y-21)**2+(x-24)**2)<8**2)|(((z-20)**2+(y-32)**2+(x-24)**2)<6**2)
        rng=np.random.default_rng(1)
        im=np.where(roi&~pores,15000,300)+rng.normal(0,15,roi.shape)
        im=im.astype(np.uint16)
        for step in [4,3]:
            configure(step,8.9,(1938,2128,1744),'physical')
            vox.SAVE_EXAMPLES=False
            with tempfile.TemporaryDirectory() as td:
                r,_,df=vox.analyze_volume(im,roi,str(Path(td)/'test'),8.9*step,1)
                for key in ['porosita_totale','parete_spessore_mediana_um','poro_spessore_mediana_um','n_pori_separati','DA_MIL_max_su_min']:
                    self.assertTrue(np.isfinite(r[key]),key)
                self.assertTrue(0<r['porosita_totale']<1)
                self.assertFalse(df.empty)
if __name__=='__main__': unittest.main(verbosity=2)
