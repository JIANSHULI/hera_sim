import unittest
import io
import numpy as np

class TestIO(unittest.TestCase):
    
    def test_empty_uvdata(self):
        
        # Make sure that empty_uvdata() can produce a UVData object
        nfreqs = 150
        ntimes = 20
        ants = { 
                 0: (1.,2.,3.), 
                 1: (3.,4.,5.)
               }
        antpairs1 = [(0,1), (1,0), (1,1)]
        antpairs2 = [(0,1), (1,0), (1,1), (0,1)] # duplicate baseline
        
        # Build object and check that data_array has correct dimensions
        uvd = io.empty_uvdata(nfreqs, ntimes, ants=ants, antpairs=antpairs1)
        self.assertEqual( uvd.data_array.shape, 
                          (len(antpairs1)*ntimes, 1, nfreqs, 1) )
        
        # Check that duplicate baselines get filtered out
        uvd = io.empty_uvdata(nfreqs, ntimes, ants=ants, antpairs=antpairs2)
        self.assertEqual( uvd.data_array.shape, 
                          (len(antpairs1)*ntimes, 1, nfreqs, 1) )
        
        
if __name__ == '__main__':
    unittest.main()
