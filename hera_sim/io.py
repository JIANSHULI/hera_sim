import numpy as np
import pyuvdata as uv
from pyuvdata.utils import get_lst_for_time, polstr2num

SEC_PER_SDAY = 86164.1 # sec per sidereal day
HERA_LOCATION = [5109342.82705015, 2005241.83929272, -3239939.40461961]
HERA_LAT_LON_ALT = (-0.53619179912885, 0.3739944696510935, 1073.0000000074506)


def empty_uvdata(nfreq, ntimes, ants, antpairs, pols=['xx',], 
                 time_per_integ=10.7, min_freq=0.1, channel_bw=0.1/1024., 
                 instrument='hera_sim', telescope_location=HERA_LOCATION, 
                 telescope_lat_lon_alt=HERA_LAT_LON_ALT, 
                 object_name='sim_data', start_jd=2458119.5, 
                 vis_units='uncalib'):
    """
    Create an empty UVData object with valid metadata and zeroed data arrays 
    with the correct dimensions.
    
    Parameters
    ----------
    nfreq : int
        Number of frequency channels.
    
    ntimes : int
        Number of LST bins.
    
    ant : dict
        Dict of antenna positions. The key should be an integer antenna ID, 
        and the value should be a tuple of (x, y, z) positions in the units 
        required by UVData.antenna_positions (meters, position relative to 
        telescope_location). Example: ants = {0 : (20., 20., 0.)}
    
    antpairs : list of len-2 tuples
        List of baselines as antenna pair tuples, e.g. bls = [(1,2), (3,4)]. 
        All antennas must be in the ants dict.
    
    pols : list of str
        List of polarization strings. Default: ['xx']
    
    time_per_integ : float, optional
        Time per integration. Default: 10.7 sec.
    
    min_freq : float, optional
        Minimum frequency of the frequency array, in GHz. Default: 0.1.
    
    channel_bw : float, optional
        Frequency channel bandwidth, in GHz. Default: 0.1 GHz / 1024.
    
    instrument : str, optional
        Name of the instrument. Default: 'hera_sim'.
    
    telescope_location : list of float, optional
        Location of the telescope, in default UVData coordinate system. Expects 
        a list of length 3. Default: HERA_LOCATION.
    
    telescope_lat_lon_alt : tuple of float, optional
        Latitude, longitude, and altitude of telescope, corresponding to the 
        coordinates in telescope_location. Default: HERA_LAT_LON_ALT.
    
    object_name : str, optional
        Name of UVData object. Default: 'simdata'.
    
    start_jd : float, optional
        Julian date of the first time sample in the dataset. Default: 
        2458119.5 (2018-01-01Z00:00:00).
    
    vis_units : str, optional
        Assumed units of the visibility data. Default: 'uncalib'.
    
    Returns
    -------
    uvd : UVData
        A new UVData object containing valid metadata and blank (zeroed) arrays.
    """
    # Generate empty UVData object
    uvd = uv.UVData()
    
    # Basic time and freq. specs
    sim_freq = (min_freq + np.arange(nfreq) * channel_bw) * 1e9 # Hz
    sim_times = start_jd + np.arange(ntimes) * time_per_integ / SEC_PER_SDAY
    sim_pols = pols
    lat, lon, alt = telescope_lat_lon_alt
    sim_lsts = get_lst_for_time(sim_times, lat, lon, alt)
    
    # Basic telescope metadata
    uvd.instrument = instrument
    uvd.telescope_name = uvd.instrument
    uvd.telescope_location = np.array(telescope_location)
    uvd.telescope_lat_lon_alt = telescope_lat_lon_alt
    uvd.history = "Generated by hera_sim"
    uvd.object_name = object_name
    uvd.vis_units = vis_units

    # Fill-in array layout using dish positions
    nants = len(ants.keys())
    uvd.antenna_numbers = np.array([int(antid) for antid in ants.keys()], 
                                   dtype=np.int)
    uvd.antenna_names = ['%d' % antid for antid in uvd.antenna_numbers]
    uvd.antenna_positions = np.zeros((nants, 3))
    uvd.Nants_data = nants
    uvd.Nants_telescope = nants
    
    # Populate antenna position table
    for i, antid in enumerate(ants.keys()):
        uvd.antenna_positions[i] = np.array( ants[antid] )
    
    # Check that baselines only involve antennas that have been defined
    ant1, ant2 = zip(*antpairs)
    defined_ants = ants.keys()
    ants_not_found = []
    for _ant in np.unique((ant1, ant2)):
        if _ant not in defined_ants: ants_not_found.append(_ant)
    if len(ants_not_found) > 0:
        raise KeyError("Baseline list contains antennas that were not "
                       "defined in the 'ants' dict: %s" % ants_not_found)

    # Convert to baseline integers
    bls = [uvd.antnums_to_baseline(*_antpair) for _antpair in antpairs]
    bls = np.unique(bls)
    
    # Convert back to ant1 and ant2 lists
    ant1, ant2 = zip(*[uvd.baseline_to_antnums(_bl) for _bl in bls])
    
    # Add frequency and polarization arrays
    uvd.freq_array = sim_freq.reshape((1, sim_freq.size))
    uvd.polarization_array = np.array(
                                [polstr2num(_pol) for _pol in sim_pols], 
                                dtype=np.int )
    uvd.channel_width = sim_freq[1] - sim_freq[0]
    uvd.Nfreqs = sim_freq.size
    uvd.Nspws = 1
    uvd.Npols = len(sim_pols)

    # Generate LST array (for each LST: Nbls copy of LST)
    # and bls array (repeat bls list Ntimes times)
    bl_arr, lst_arr = np.meshgrid(np.array(bls), sim_lsts)
    uvd.baseline_array = bl_arr.flatten()
    uvd.lst_array = lst_arr.flatten()

    # Time array
    _, time_arr = np.meshgrid(np.array(bls), sim_times)
    uvd.time_array = time_arr.flatten()

    # Set antenna arrays (same shape as baseline_array)
    ant1_arr, _ = np.meshgrid(np.array(ant1), sim_lsts)
    ant2_arr, _ = np.meshgrid(np.array(ant2), sim_lsts)
    uvd.ant_1_array = ant1_arr.flatten()
    uvd.ant_2_array = ant2_arr.flatten()

    # Sets UVWs
    uvd.set_uvws_from_antenna_positions()

    # Populate array lengths
    uvd.Nbls = len(bls)
    uvd.Ntimes = sim_lsts.size
    uvd.Nblts = bl_arr.size

    # Initialise data, flag, and integration arrays
    uvd.data_array = np.zeros((uvd.Nblts, uvd.Nspws, uvd.Nfreqs, uvd.Npols), 
                              dtype=np.complex64)
    uvd.flag_array = np.zeros((uvd.Nblts, uvd.Nspws, uvd.Nfreqs, uvd.Npols), 
                              dtype=bool)
    uvd.nsample_array = np.ones((uvd.Nblts, uvd.Nspws, uvd.Nfreqs, uvd.Npols), 
                                dtype=np.float32)
    uvd.spw_array = np.ones(1, dtype=np.int)
    uvd.integration_time = time_per_integ * np.ones(uvd.Nblts) # per bl-time

    uvd.phase_type = 'drift'

    # Check validity and return
    uvd.check()
    return uvd
    
