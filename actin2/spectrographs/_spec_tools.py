"""
ACTIN 2: General functions used to process data from spectrographs.
"""
import numpy as np
import pandas as pd
from astropy.io import fits

# THIS IS A GENERAL FUNCTION, SHOULD GO TO ANOTHER FILE?
def printif(text, verb=True):
    """Print text if verb is True"""
    if verb:
        print(text)


def wave_star_rest_frame(wave, rv):
    """Change wavelength to stellar rest frame
    'wave' must be in the solar system baricentric frame."""
    c = 299792458.0 # [m/s]
    dwave = rv * wave / c
    wave_corr = wave - dwave
    return wave_corr


def wave_corr_berv(wave, berv):
    """Change wavelength to solar system baricentric frame"""
    c = 299792458.0 # [m/s]
    dwave = - berv * wave / c
    wave_corr = wave - dwave
    return wave_corr


def filter_headers(OUT_HDR_KEYS, all_hdr_dict):
    headers = dict()
    for key in OUT_HDR_KEYS:
            if key in all_hdr_dict:
                headers[key] = all_hdr_dict[key]
    return headers


#! Remove from this file: (add as post-processing)
def date_to_jd(dd_mm_yyyy):
    """Date format must be DD/MM/YYYY"""
    day, month, year = dd_mm_yyyy.split("/")
    ts = pd.Timestamp(int(year), int(month), int(day))
    return ts.to_julian_date()

#! Remove from this file: (add as post-processing)
def separate_instr_by_bjd(bjd_sep, bjd, instr, suff_pre='pre', suff_pos='pos'):
    if isinstance(instr, list):
        for i in instr:
            if bjd < bjd_sep:
                instr_new = i + suff_pre
            if bjd >= bjd_sep:
                instr_new = i + suff_pos
    else:
        if bjd < bjd_sep:
                instr_new = instr + suff_pre
        if bjd >= bjd_sep:
            instr_new = instr + suff_pos
    return instr_new


# Just for HARPS/HARPN
def read_fits(fits_file=None, hdu=None, instr=None, calc_x=True):
    if fits_file:
        hdu = fits.open(fits_file)
    y = hdu[0].data
    hdr = hdu[0].header

    hdu.close()

    if calc_x:
        if instr == 'HARPS':
            obs = 'ESO'
        if instr == 'HARPN':
            obs = 'TNG'
        try:
            x = calc_fits_x_2d(hdr, obs)
        except KeyError:
            try:
                x = calc_fits_x_1d(hdr)
            except:
                print("*** Error reading fits x coordinate")
                x = np.nan
        return x, y, hdr
    else:
        return y, hdr


def calc_fits_x_1d(hdr, key_a='CRVAL1', key_b='CDELT1', key_c='NAXIS1'):
    return hdr[key_a] + hdr[key_b] * np.arange(hdr[key_c])


def calc_fits_x_2d(hdr, obs):
    deg = hdr[f'HIERARCH {obs} DRS CAL TH DEG LL'] # polynomial degree

    ll_coeff = np.zeros((hdr['NAXIS2'], deg + 1))

    # Read coefficients
    for i in range(hdr['NAXIS2']):
        for j in range(deg + 1):
            ll_coeff[i, j] = hdr['HIERARCH {} DRS CAL TH COEFF LL{}'.format(obs, (j + (deg + 1)*i))]

    # Evaluate polynomials
    x = np.arange(hdr['NAXIS1'])  # Pixel array
    wave_raw = np.zeros([hdr['NAXIS2'], hdr['NAXIS1']])  # Wavelength 2D array
    for i in range(len(wave_raw)):
        wave_raw[i] = np.poly1d(ll_coeff[i][::-1])(x)
    return wave_raw


# Read fits header data usibg 'headers' dictionary:
def read_headers(hdr, headers, data=None):
    """Read fits header data using 'headers' dictionary.
    Result is included in 'data' dictionary if not 'None'. If 'None' a new dictionary is returned"""
    if not data:
        data = {}

    for key, hdr_id in zip(headers.keys(), headers.values()):
        # if not hdr:
        #     data[key] = np.nan
        #     continue
        try:
            data[key] = hdr[hdr_id]
        except KeyError:
            data[key] = None
    return data