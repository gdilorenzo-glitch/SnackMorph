import numpy as np
import pytest
from snackmorph import vox


@pytest.mark.parametrize("shape", [(5, 25), (3, 5, 25)])
def test_strict_component_size_threshold(shape):
    mask = np.zeros(shape, dtype=bool)
    plane = mask if mask.ndim == 2 else mask[1]
    plane[0, :19] = True
    plane[2, :20] = True
    plane[4, :21] = True
    expected = mask.copy()
    (expected if mask.ndim == 2 else expected[1])[0, :19] = False
    np.testing.assert_array_equal(vox._remove_small_objects_legacy(mask, 20), expected)
    np.testing.assert_array_equal(vox._remove_small_objects_legacy(mask, 1), mask)
    assert mask.sum() == 60
