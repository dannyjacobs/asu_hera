# coding=utf-8
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import healpy as hp
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
from pyuvdata import UVBeam
from astropy.io import fits
import pdb

c                       =   299792458. # Speed of light
wavelength              =   c/150e6 # Average wavelength of interest
max_baseline            =   100. # Length of longgest baseline
ang_res                 =   wavelength/max_baseline * 180./np.pi # Approximate angular resolution in degrees
HERA_center             =   -30.7214 # FoV centered at declination -30.7214 degrees

# Make input() compatible with Python 2 and Python 3
try:
    input                   =   raw_input
except NameError:
    pass

def beam_model(target_long=45, plot=False):
    """Quantify a beam model as a function of declination at 150 MHz.

    Parameters
    ----------
    target_long : float, optional
        Azimuthal angle (in degrees) at which to find power as a function of zenith angle (default: 45 degrees).
    plot : bool, optional
        Whether to plot the beam function (default: False).

    Returns
    -------
    params : array-like
        Parameters (amplitude, mean, and standard deviation) for a Gaussian model of HERA's beam.
    """

    HERA_beam               =   UVBeam()
    HERA_beam.read_beamfits("NF_HERA_power_beam_healpix.fits") # Read the beam model
    nside, hpx_inds         =   HERA_beam.nside, HERA_beam.pixel_array
    colat, long             =   hp.pixelfunc.pix2ang(nside=nside, ipix=hpx_inds, nest=False, lonlat=False) # Convert from HEALPix coordinates to long/zen
    long, colat             =   np.degrees(long), np.degrees(colat)
    power_xx                =   HERA_beam.data_array[0][0][0][50] # Power at 150 MHz - XX polaricolattion

    closest_long            =   find_nearest(long, target_long) # In case the target angle isn't actually in the simulation
    mask                    =   (long == closest_long) # Mask out everything but the closest angle
    new_colat, power        =   colat[mask], power_xx[mask] # Zenith angle and power for the given longimuthal angle
    power_norm              =   power/np.max(power) # Normalize to be used as a scaling factor

    interp_beam             =   interp1d(new_colat, power_norm) # Interpolate the beam as a function of the zenith angle
    colat_interp            =   np.linspace(0.8, 10, 1000)
    power_interp            =   interp_beam(colat_interp)

    params, pcovs           =   curve_fit(gaussian_function, colat_interp, power_interp) # Fit a Gaussian to interpolated beam

    if plot:
        plt.close("all")
        colat_interp                    =   np.linspace(np.min(new_colat), np.max(new_colat), 1000)
        power_interp                    =   interp_beam(colat_interp)
        fig                             =   plt.figure(1, figsize=(10, 8))
        ax                              =   fig.add_subplot(111)
        ax.plot(new_colat, power_norm, color="b", marker=".", linestyle="None") # Model
        ax.plot(colat_interp, power_interp, color="k", linestyle="-") # Interpolation
        ax.set_xlabel("Colatitude [degrees]"); ax.set_ylabel("Power")
        ax.set_yscale("log")
        plt.title("az = " + str(target_long))
        plt.tight_layout(); plt.show(block=False)

    return params

def read_data():
    """Read the data in the TGSS catalog FITS file.

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of all objects in the TGSS catalog.
    """

    hdul                    =   fits.open("TGSSADR1_7sigma_catalog.fits") # Load the data
    name                    =   hdul[1].data["Source_name"] # Get the source names
    RA, dec                 =   hdul[1].data["RA"].astype(np.float), hdul[1].data["dec"].astype(np.float) # Get the location in degrees
    peak_flux, tot_flux     =   hdul[1].data["Peak_flux"].astype(np.float), hdul[1].data["Total_flux"].astype(np.float) # Get flux in mJy/beam
    data                    =   pd.DataFrame({"Name": name, "RA": RA, "dec": dec, "Peak flux": peak_flux, "Total flux": tot_flux})

    return data

def filter_by_location(dec_range=7.):
    """Filter the objects in the TGSS catalog by location.

    Parameters
    ----------
    dec_range : float, optional
        The range in which to search around the center of the HERA FoV, -30.7 degrees (default: 7.0).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of the objects within the given location range.
    """

    data                    =   read_data()
    filtered_data           =   data[(data["dec"] >= (HERA_center - dec_range)) & (data["dec"] <= (HERA_center + dec_range))] # Filter by position

    return filtered_data

def calc_apparent_flux(dec_range=7.):
    """Calculate 'apparent' peak and total flux for each object in the HERA FoV.

    Parameters
    ----------
    dec_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak aparent flux, and total apparent flux of the objects.
    """

    data                    =   filter_by_location(dec_range=dec_range)
    relative_loc            =   data["dec"] - HERA_center # Find location relative to center of HERA FoV
    gauss_params            =   beam_model()
    beam_correction         =   gaussian_function(relative_loc, gauss_params[0], gauss_params[1], gauss_params[2]) # Apply beam correction
    data["Apparent peak flux"]  =   np.multiply(beam_correction, data["Peak flux"]) # Calculate apparent peak flux
    data["Apparent total flux"] =   np.multiply(beam_correction, data["Total flux"]) # Calculate apparent total flux

    return data

def filter_by_flux(dec_range=7., min_flux=10.):
    """Filter the objects in the TGSS catalog by flux.

    Parameters
    ----------
    min_flux : float, optional
        The minimum flux for objects to have (default: 10 Jy).
    dec_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of the objects with flux larger than the
        minimum flux desired.
    """

    min_flux_mJy            =   min_flux * 1000. # Convert to mJy
    data                    =   calc_apparent_flux(dec_range=dec_range) # Find the apparent flux
    filtered_data           =   data[data["Apparent total flux"] >= min_flux_mJy] # Find objects with large flux

    print("Number of objects found in a " + str(dec_range) + " degree band around the center of declination of the HERA FoV " + \
            "with a minimum apparent total flux of " + str(min_flux) + " Jy: " + str(len(filtered_data))) # How many objects fit the criteria

    return filtered_data

def add_fluxes(dec_range=7., min_flux=10.):
    """Add the fluxes of sources within circles centered around the bright sources.

    Parameters
    ----------
    min_flux : float, optional
        The minimum flux for individual objects to have (default: 10 Jy).
    dec_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    regions : DataFrame
        The center and flux of each circular region.
    """

    data                        =   read_data() # The unfiltered data
    filtered_data               =   filter_by_flux(dec_range=dec_range, min_flux=min_flux) # The filtered data (by location and flux)
    radius                      =   ang_res/2. # Radius of the circles enclosing each object
    lo_RA, hi_RA                =   filtered_data["RA"] - radius, filtered_data["RA"] + radius
    lo_dec, hi_dec              =   filtered_data["dec"] - radius, filtered_data["dec"] + radius
    names                       =   [filtered_data["Name"][i] for i in filtered_data.index] # Name of center object
    center_RA                   =   [filtered_data["RA"][i] for i in filtered_data.index] # RA of center
    center_dec                  =   [filtered_data["dec"][i] for i in filtered_data.index] # dec of center
    flux                        =   [] # Empty list to store fluxes

    for i in filtered_data.index:
        # Find all objects in unfiltered data in a square formed around a bright object
        objects                         =   data[(data["RA"] >= lo_RA[i]) & (data["RA"] <= hi_RA[i])] # RA
        objects                         =   objects[(objects["dec"] >= lo_dec[i]) & (objects["dec"] <= hi_dec[i])] # dec
        # Find objects in a circle around a bright object
        RA_dist, dec_dist               =   objects["RA"] - filtered_data["RA"][i], objects["dec"] - filtered_data["dec"][i]
        tot_distance                    =   np.sqrt(RA_dist**2 + dec_dist**2) # Distance of each object from the one in the center
        objects                         =   objects[tot_distance <= radius] # Only keep objects within the circle (not the square)
        tot_flux                        =   np.sum(objects["Total flux"]) # Add up the total flux inside the circle - mJy
        flux.append(tot_flux)

    regions                     =   pd.DataFrame({"Name of Center": names, "RA": center_RA, "Dec": center_dec, "Total flux in region": flux}, columns=["Name of Center", "RA", "Dec", "Total flux in region"]) # Create a dataframe
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

    index                   =   (np.abs(array - value)).argmin()
    return array[index]

def gaussian_function(x, amp, mu, sigma):
    return amp*np.exp(-0.5*((x - mu)/sigma)**2)

if __name__ == "__main__":
    # Limits on location and minimum flux
    dec_range                   =   input("What declination range around the center of the HERA FoV " + \
                                                "would you like to search in? [default: 7 degrees] ")
    if dec_range == "":
        dec_range                       =   "7." # Default declination range

    # Try to convert string to number
    try:
        dec_range                       =   float(dec_range)
    except ValueError:
        print("That is not a valid number. Defaulting to range of 7 degrees.")
        dec_range                       =   7.

    min_flux                    =   input("What minimum flux should the objects have? [default: 10 Jy] ")
    if min_flux == "":
        min_flux                        =   "10." # Default minimum flux

    # Try to convert string to number
    try:
        min_flux                        =   float(min_flux)
    except ValueError:
        print("That is not a valid number. Defaulting to minimum flux of 10 Jy.")
        min_flux                        =   10.

    regions                     =   add_fluxes(dec_range=dec_range, min_flux=min_flux)
    print(regions)
