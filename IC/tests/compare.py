#!/usr/bin/env python

import numpy as np
import numpy.testing as npt
import pynbody
import sys
import glob
import os.path
import warnings

def compare(f1,f2) :
    npt.assert_almost_equal(f1['mass'],f2['mass'],decimal=6)
    npt.assert_almost_equal(f1['eps'],f2['eps'],decimal=6)

    # 1/02/2017 - due to a normalisation error fixed in the tipsy output, rather than rewrite all the
    # reference files, the test here scales the velocities appropriately
    tipsy_normalisation_error = 1.1571/1.1578
    npt.assert_almost_equal(f1['vel'],f2['vel']/tipsy_normalisation_error,decimal=4)
    npt.assert_almost_equal(f1['pos'],f2['pos'],decimal=4)
    print "Particle output matches"

def compare_grids(ref, test):
    list_of_grids = [os.path.basename(x) for x in glob.glob(ref+"grid-?.npy")]
    list_of_grids.sort()
    for grid in list_of_grids:
        grid_ref = np.load(ref+grid)
        grid_test = np.load(test+grid)
        npt.assert_almost_equal(grid_ref, grid_test, decimal=4)
    print "Grid output matches"

def compare_ps(ref, test):
    ref_vals = np.loadtxt(ref)
    test_vals = np.loadtxt(test)
    npt.assert_allclose(ref_vals, test_vals, rtol=1e-4)
    print "Power-spectrum output %s matches"%ref


if __name__=="__main__":
    warnings.simplefilter("ignore")
    assert len(sys.argv)==2
    if os.path.exists(sys.argv[1]+"/reference_grid"):
        compare_grids(sys.argv[1]+"/reference_grid/",sys.argv[1]+"/")

    powspecs = sorted(glob.glob(sys.argv[1]+"/*.ps"))
    powspecs_test = sorted(glob.glob(sys.argv[1]+"/reference_ps/*.ps"))
    for ps, ps_test in zip(powspecs, powspecs_test):
        compare_ps(ps,ps_test)

    output_file = glob.glob(sys.argv[1]+"/*.tipsy")
    assert len(output_file)==1, "Could not find a unique output file to test against"
    compare(pynbody.load(output_file[0]),pynbody.load(sys.argv[1]+"/reference_output"))
