"""
Provides a number of mappings which may be useful for visibility simulators.
"""
import healpy
import numpy as np


def beam_healpix_to_lm(hmap, n_pix_lm=63, nest=False):
    """
    Convert a beam contained in a healpix map to (l,m) co-ordinates,
    assuming the zenith is where???

    Args:
        hmap (1D array): array representing a healpix map.
            Must have length 12*N^2 for some N.
        n_pix_lm (int): number of pixels on a size for the beam map cube.
        nest (bool): whether the healpix scheme is NEST (default is RING).

    Returns:
        ndarray, shape[beam_px, beam_px]: the beam map cube.
    """

    # X is 3rd dim, Y is 2nd dim
    l = np.linspace(-1, 1, n_pix_lm, dtype=np.float32)
    l, m = np.meshgrid(l, l)
    l = l.flatten()
    m = m.flatten()

    lsqr = l ** 2 + m ** 2
    n = np.where(lsqr < 1, np.sqrt(1 - lsqr), -1)

    hp_pix = healpy.vec2pix(healpy.get_nside(hmap), l, m, n, nest=nest)

    bm = np.where(n > 0, hmap[hp_pix], 0)
    bm = np.reshape(bm, (n_pix_lm, n_pix_lm))

    if np.max(hmap) > 0:
        bm /= np.max(hmap)

    return bm


def eq2top_m(ha, dec):
    """
    Return the 3x3 matrix converting equatorial coordinates to topocentric
    at the given hour angle (ha) and declination (dec).

    Ripped straight from aipy.
    """
    sin_H, cos_H = np.sin(ha), np.cos(ha)
    sin_d, cos_d = np.sin(dec), np.cos(dec)
    zero = np.zeros_like(ha)

    map = np.array([[sin_H, cos_H, zero],
                    [-sin_d * cos_H, sin_d * sin_H, cos_d],
                    [cos_d * cos_H, -cos_d * sin_H, sin_d]])

    if len(map.shape) == 3:
        map = map.transpose([2, 0, 1])

    return map


def healpix_to_crd_eq(h, nest=False):
    """
    Determine equatorial co-ordinates of a healpix map's pixels.

    Args:
        h (1D array): the healpix array (must have size 12*N^2 for some N).
        nest (bool, optional): whether the healpix array is in NEST configuration.

    Returns:
        2D array, shape[12*N^2, 3]: the equatorial co-ordinates of each pixel.
    """
    assert h.ndim == 1, "h must be a 1D array"

    px = np.arange(len(h))
    crd_eq = np.array(healpy.pix2vec(healpy.get_nside(h), px, nest=nest), dtype=np.float32)
    return crd_eq