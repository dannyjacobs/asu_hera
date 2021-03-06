# coding=utf-8
import numpy as np
import pandas as pd
import re
import healpy as hp
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from pyuvdata import UVBeam
from astropy.io import fits
import json


c = 299792458.  # Speed of light
wavelength = c/150e6  # Average wavelength of interest
max_baseline = 100.  # Length of longest baseline in meters
ang_res = wavelength/max_baseline * 180./np.pi  # Angular resolution
HERA_center = -30.7214  # Center of FoV

# Make input() compatible with Python 2 and Python 3
try:
    input = raw_input
except NameError:
    pass


def beam_model(target_long=45):
    """Quantify a beam model as a function of declination at 150 MHz.

    Parameters
    ----------
    target_long : float, optional
        Azimuthal angle (in degrees) at which to find power as a function of
        zenith angle (default: 45 degrees).

    Returns
    -------
    beam_model : function
        Gaussian fit to the simulated beam
    """
    HERA_beam = UVBeam()
    HERA_beam.read_beamfits("../beam_mapping/sims/NF_HERA_power_beam_healpix.fits")
    nside, hpx_inds = HERA_beam.nside, HERA_beam.pixel_array
    colat, long = hp.pixelfunc.pix2ang(nside=nside, ipix=hpx_inds, nest=False,
                                       lonlat=False)  # HEALPix to az/za
    long, colat = np.degrees(long), np.degrees(colat)
    # Power at 150 MHz, XX polarization
    power_xx = HERA_beam.data_array[0][0][0][50]

    # In case the target angle isn't actually in the simulation
    closest_long = find_nearest(long, target_long)
    # Mask out everything but the closest angle
    mask = (long == closest_long)
    # Zenith angle and power for the given azimuthal angle
    new_colat, power = colat[mask], power_xx[mask]
    # Normalize to the peak power at center of beam
    power_norm = power / np.max(power)

    # Interpolate the beam as a function of the zenith angle and fit Gaussian
    interp_beam = interp1d(new_colat, power_norm)
    colat_interp = np.linspace(0.8, 10, 1000)
    power_interp = interp_beam(colat_interp)
    params, pcovs = curve_fit(gaussian_function, colat_interp,
                              power_interp)
    def beam_model(x):
        return np.exp(-0.5*((x - params[1])/params[2])**2)
    return beam_model


def read_data():
    """Read the data in the TGSS catalog FITS file.

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of
        all objects in the TGSS catalog.
    """
    hdul = fits.open("TGSSADR1_7sigma_catalog.fits")
    name = hdul[1].data["Source_name"]  # Get the source names

    # Get the location in degrees
    RA = hdul[1].data["RA"].astype(np.float)
    dec = hdul[1].data["dec"].astype(np.float)

    # Get flux in mJy/beam
    peak_flux = hdul[1].data["Peak_flux"].astype(np.float)
    tot_flux = hdul[1].data["Total_flux"].astype(np.float)

    # Manually add Fornax A (NGC 1316)
    name = np.append(name, "Fornax A")
    RA, dec = np.append(RA, 50.673825), np.append(dec, -37.208227)
    peak_flux, tot_flux = np.append(peak_flux, 7.5e5), np.append(tot_flux, 7.5e5)
    data = pd.DataFrame({"Name": name, "RA": RA, "dec": dec,
                        "Peak flux": peak_flux, "Total flux": tot_flux})
    return data


def filter_by_location(RA_range, dec_range=7.):
    """Filter the objects in the TGSS catalog by location.

    Parameters
    ----------
    RA_range : tuple of strings
        Range of right ascensions to search, in the form (hh:mm:ss, hh:mm:ss),
        with the lower RA as the first element.
    dec_range : float, optional
        The range in which to search around the center of HERA's FoV
        (default: 7.0).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of
        the objects within the given location range.
    """
    data = read_data()
    lo_RA = [float(RA_range[0].split(":")[i]) for i in range(3)]
    lo_RA_decimal = 15. * (lo_RA[0] + lo_RA[1]/60. + lo_RA[2]/3600.)
    hi_RA = [float(RA_range[1].split(":")[i]) for i in range(3)]
    hi_RA_decimal = 15. * (hi_RA[0] + hi_RA[1]/60. + hi_RA[2]/3600.)

    # Filter by RA and dec
    filtered_data = data[(data["RA"] >= lo_RA_decimal) & (data["RA"]
                         <= hi_RA_decimal)]
    filtered_data = filtered_data[(filtered_data["dec"] >= (HERA_center - dec_range)) &
                                  (filtered_data["dec"] <= (HERA_center + dec_range))]
    return filtered_data


def calc_apparent_flux(RA_range, dec_range=7.):
    """Calculate apparent peak and total flux for each object in the FoV.

    Parameters
    ----------
    RA_range : tuple of strings
        Range of right ascensions to search, in the form (hh:mm:ss, hh:mm:ss),
        with the lower RA as the first element.
    dec_range : float, optional
        The range in which to search around the center of HERA's FoV
        (default: 7.0).

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak aparent flux, and total
        apparent flux of the objects.
    """
    data = filter_by_location(RA_range=RA_range, dec_range=dec_range)
    # Relative location of center of HERA's FoV
    relative_loc = data["dec"] - HERA_center
    beam_gauss = beam_model()
    beam_corr = beam_gauss(relative_loc)  # Apply beam correction

    # Calculate apparent peak flux
    data["Apparent peak flux"] = np.multiply(beam_corr, data["Peak flux"])
    # Calculate apparent total flux
    data["Apparent total flux"] = np.multiply(beam_corr, data["Total flux"])
    return data


def filter_by_flux(RA_range, dec_range=7., min_flux=10.):
    """Filter the objects in the TGSS catalog by flux.

    Parameters
    ----------
    RA_range : tuple of strings
        Range of right ascensions to search, in the form (hh:mm:ss, hh:mm:ss),
        with the lower RA as the first element.
    dec_range : float, optional
        The range in which to search around the center of HERA's FoV
        (default: 7.0).
    min_flux : float, optional
        The minimum flux for objects to have in Jy (default: 10 Jy).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of
        the objects with flux larger than the minimum flux desired.
    """
    min_flux_mJy = min_flux * 1000.  # Convert to mJy
    # Find the apparent flux
    data = calc_apparent_flux(RA_range=RA_range, dec_range=dec_range)
    # Find objects with large apparent flux
    filtered_data = data[data["Apparent total flux"] >= min_flux_mJy]
    return filtered_data


def add_fluxes(RA_range, dec_range=7., min_flux=10.):
    """Add the fluxes of sources in circles centered on the bright sources.

    Parameters
    ----------
    RA_range : tuple of strings
        Range of right ascensions to search, in the form (hh:mm:ss, hh:mm:ss),
        with the lower RA as the first element.
    dec_range : float, optional
        The range in which to search around the center of HERA's FoV
        (default: 7.0).
    min_flux : float, optional
        The minimum flux for objects to have in Jy (default: 10 Jy).

    Returns
    -------
    regions : DataFrame
        The center and flux of each circular region.
    """
    data = read_data()
    beam_corr_data = calc_apparent_flux(RA_range=RA_range, dec_range=dec_range)
    # Filter by location and apparent flux
    filtered_data = filter_by_flux(RA_range=RA_range, dec_range=dec_range,
                                   min_flux=min_flux)
    radius = ang_res/2.  # Radius of the circles enclosing each object
    lo_RA, hi_RA = filtered_data["RA"] - radius, filtered_data["RA"] + radius
    lo_dec, hi_dec = filtered_data["dec"] - radius, filtered_data["dec"] + radius
    # Names, RAs, and decs of center objects
    names = [filtered_data["Name"][i] for i in filtered_data.index]
    center_RA = [filtered_data["RA"][i] for i in filtered_data.index]
    center_dec = [filtered_data["dec"][i] for i in filtered_data.index]

    flux, app_flux = [], []  # To store actual and apparent fluxes
    for i in filtered_data.index:
        # Find objects in a square formed around a bright object
        objects = data[(data["RA"] >= lo_RA[i]) & (data["RA"] <= hi_RA[i])]
        objects = objects[(objects["dec"] >= lo_dec[i]) & (objects["dec"] <= hi_dec[i])]
        # Find objects in a circle around a bright object and add their flux
        RA_dist = objects["RA"] - filtered_data["RA"][i]
        dec_dist = objects["dec"] - filtered_data["dec"][i]
        tot_distance = np.sqrt(RA_dist**2 + dec_dist**2)
        objects = objects[tot_distance <= radius]
        tot_flux = np.sum(objects["Total flux"])

        # Beam correct the total flux inside the circle
        tot_flux_corr = np.sum(np.array([beam_corr_data['Apparent total flux'][i]
                                         for i in objects.index]))
        flux.append(tot_flux)
        app_flux.append(tot_flux_corr)

    # Create a dataframe
    regions = pd.DataFrame({"Name": names, "RA": center_RA, "Dec": center_dec,
                           "Apparent flux": app_flux, "Total flux": flux},
                           columns=["Name", "RA", "Dec", "Apparent flux", "Total flux"])

    # Print information about chosen parameters
    lo_RA_disp = RA_range[0][:2] + "h" + RA_range[0][3:5] + "m" + RA_range[0][6:] + "s"
    hi_RA_disp = RA_range[1][:2] + "h" + RA_range[1][3:5] + "m" + RA_range[1][6:] + "s"
    print("\nRight ascension:\n\tLower: " + lo_RA_disp + " \n\tUpper: " +
          hi_RA_disp)
    print("Declination:\n\tLower: " + str(HERA_center - dec_range) +
          " degrees\n\tUpper: " + str(HERA_center + dec_range) + " degrees")
    print("Minimum flux: " + str(min_flux) + " Jy")
    print("Number of regions found: " + str(len(regions)) + "\n")
    print(regions)
    return regions


def find_nearest(array, value):
    """Find the nearest value in an array.

    Parameters
    ----------
    array : array
        The array to search.
    value : int or float
        The value to search for the closest element in the array.

    Returns
    -------
    element : float
        The value of the closest element in the array.
    """
    index = (np.abs(array - value)).argmin()
    closest = array[index]
    return closest


def reformat_df(df,save_json=False,json_name='sources.json'):
    src_dict = {v["Name"]: {"Dec": v["Dec"], "RA": v["RA"],
                "Apparent_flux": v["Apparent flux"],
                "Total_flux": v["Total flux"]} for _,v in df.iterrows()}
    print(src_dict)
    if save_json:
        with open(json_name, 'w') as f:
            json.dump(src_dict, f)


def gaussian_function(x, amp, mu, sigma):
    return amp*np.exp(-0.5 * ((x-mu)/sigma)**2)


if __name__ == "__main__":
    # Limit on RA
    print("What range of right ascension would you like to search in?")
    flag_lo = False
    rexp = re.compile("^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$")  # To check format of string
    while not flag_lo:
        lo_RA = input("\tLower [hh:mm:ss]: ")
        # Check if format of lo_RA string is correct
        if rexp.match(lo_RA):
            flag_lo = True
        else:
            print("Please input a right ascension in the form hh:mm:ss.")

    flag_hi = False
    while not flag_hi:
        hi_RA = input("\tUpper [hh:mm:ss]: ")
        # Check if format of hi_RA string is correct
        if rexp.match(hi_RA):
            flag_hi = True
        else:
            print("Please input a right ascension in the form hh:mm:ss.")

    # Limit on declination
    dec_range = input("What declination range around the center of the HERA FoV " +
                      "would you like to search in? [default: 7 degrees] ")
    if dec_range == "":
        dec_range = "7."  # Default declination range
    # Try to convert to number
    try:
        dec_range = float(dec_range)
    except ValueError:
        print("That is not a valid number. Defaulting to range of 7 degrees.")
        dec_range = 7.

    # Limit on minimum flux
    min_flux = input("What minimum flux should the objects have (Jy)? [default: 10 Jy] ")
    if min_flux == "":
        min_flux = "10."  # Default minimum flux
    # Try to convert to number
    try:
        min_flux = float(min_flux)
    except ValueError:
        print("That is not a valid number. Defaulting to minimum flux of 10 Jy.")
        min_flux = 10.

    # Find regions
    regions = add_fluxes(RA_range=(lo_RA, hi_RA), dec_range=dec_range, min_flux=min_flux)
    reformat_df(regions, save_json=True, json_name='mask_sources.json')
