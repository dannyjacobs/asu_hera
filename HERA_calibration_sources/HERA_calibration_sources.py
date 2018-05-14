# coding=utf-8

import numpy as np
import pandas as pd
import healpy as hp
from pyuvdata import UVBeam
from astropy.io import fits
from astropy import wcs
import pdb

c                       =   299792458.0 # Speed of light
wavelength              =   c/150e6 # Average wavelength of interest
max_baseline            =   100.0 # Length of longest baseline
ang_res                 =   wavelength/max_baseline * 180./np.pi # Approximate angular resolution in degrees
HERA_center             =   -30.7214 # FoV centered at declination -30.7214 degrees

# Make input() compatible with Python 2 and Python 3
try:
    input                   =   raw_input
except NameError:
    pass

def read_beam():
    HERA_beam               =   UVBeam()
    HERA_beam.read_beamfits("NF_HERA_power_beam_healpix.fits")
    nside, hpx_inds         =   HERA_beam.nside, HERA_beam.pixel_array
    az_za                   =   hp.pix2ang(nside=nside, ipix=hpx_inds, nest=False, lonlat=True)
    freq_50Hz               =   HERA_beam.data_array[0][0][0][50]
    # hdul.close()
    pdb.set_trace()

def read_data():
    """Read the data in the TGSS catalog FITS file.

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of all objects in the TGSS catalog.
    """

    hdul                    =   fits.open("TGSSADR1_7sigma_catalog.fits") # Load the data
    name                    =   hdul[1].data["Source_name"] # Get the source names
    RA, DEC                 =   hdul[1].data["RA"].astype(np.float), hdul[1].data["DEC"].astype(np.float) # Get the location in degrees
    peak_flux, tot_flux     =   hdul[1].data["Peak_flux"].astype(np.float), hdul[1].data["Total_flux"].astype(np.float) # Get flux in mJy/beam
    data                    =   pd.DataFrame({"Name": name, "RA": RA, "DEC": DEC, "Peak flux": peak_flux, "Total flux": tot_flux})
    hdul.close()
    return data

def filter_by_location(DEC_range=7.0):
    """Filter the objects in the TGSS catalog by location.

    Choose objects in the TGSS catalog in a declination band centered at -30.7 degrees (the center of the HERA field of view).

    Parameters
    ----------
    DEC_range : float, optional
        The range in which to search around the center of the HERA FoV, -30.7 degrees (default: 7.0).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of the objects within the given location range.
    """

    data                    =   read_data()
    filtered_data           =   data[(data["DEC"] >= (HERA_center - DEC_range)) & (data["DEC"] <= (HERA_center + DEC_range))] # Filter by position
    return filtered_data

def calc_apparent_flux(DEC_range=7.0):
    """Calculate 'apparent' peak and total flux for each object in the HERA FoV.

    Calculate 'apparent' flux according to Gaussian as a function of distance from -30.7 degrees for each object.

    Parameters
    ----------
    DEC_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    data : DataFrame
        The names, right ascension, declination, peak aparent flux, and total apparent flux of the objects.
    """

    data                    =   filter_by_location(DEC_range=DEC_range)
    relative_loc            =   data["DEC"] - HERA_center # Find location relative to center of HERA FoV
    std_dev                 =   np.std(relative_loc)
    exp_factor              =   np.exp(-abs(relative_loc)) # Apply decaying exponential scaling factor according to distance
    app_peak_flux           =   exp_factor * data["Peak flux"] # Calculate apparent peak flux
    app_tot_flux            =   exp_factor * data["Total flux"] # Calculate apparent total flux
    data["Apparent peak flux"]  =   app_peak_flux
    data["Apparent total flux"] =   app_tot_flux
    return data

def filter_by_flux(DEC_range=7.0, min_flux=500.0):
    """Filter the objects in the TGSS catalog by flux.

    Choose objects in the TGSS catalog with a total (apparent) flux greater than the given minimum flux (with
    location penalty applied).

    Parameters
    ----------
    min_flux : float, optional
        The minimum flux for objects to have.
    DEC_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    filtered_data : DataFrame
        The names, right ascension, declination, peak flux, and total flux of the objects with flux larger than the
        minimum flux desired.
    """

    data                        =   calc_apparent_flux(DEC_range=DEC_range) # Find the apparent flux
    filtered_data               =   data[data["Apparent total flux"] >= min_flux] # Find objects with large flux

    print("Number of objects found in a " + str(DEC_range) + " degree band around the center of declination of the HERA FoV " +
            "with a minimum apparent flux of " + str(min_flux/1000.0) + " Jy: " + str(len(filtered_data))) # How many objects fit the criteria

    return filtered_data

def add_fluxes(DEC_range=7.0, min_flux=500.0):
    """Add the fluxes of sources within circles centered around the bright sources.

    Add up the total fluxes of each source within a circle around a bright source. The circles
    have a radius of half the angular resolution of HERA.

    Parameters
    ----------
    min_flux : float, optional
        The minimum flux for individual objects to have, to initially find locations to locate other sources.
    DEC_range : float, optional
        The range in which to search around the HERA FoV center of -30.7 degrees (default: 7.0).

    Returns
    -------
    regions : DataFrame
        The center and flux of each circular region.
    """

    data                        =   read_data() # The unfiltered data
    filtered_data               =   filter_by_flux(DEC_range=DEC_range, min_flux=min_flux) # The filtered data (by location and flux)
    print(filtered_data)
    radius                      =   ang_res/2.0 # Radius of the circles enclosing each object
    lo_RA, hi_RA                =   filtered_data["RA"] - radius, filtered_data["RA"] + radius
    lo_DEC, hi_DEC              =   filtered_data["DEC"] - radius, filtered_data["DEC"] + radius
    names                       =   [filtered_data["Name"][i] for i in filtered_data.index] # Name of center object
    center_RA                   =   [filtered_data["RA"][i] for i in filtered_data.index] # RA of center
    center_DEC                  =   [filtered_data["DEC"][i] for i in filtered_data.index] # DEC of center
    flux                        =   [] # Empty list to store fluxes

    for i in filtered_data.index:
        # Find all objects in unfiltered data in a square formed around a bright object
        objects                         =   data[(data["RA"] >= lo_RA[i]) & (data["RA"] <= hi_RA[i])] # RA
        objects                         =   objects[(objects["DEC"] >= lo_DEC[i]) & (objects["DEC"] <= hi_DEC[i])] # DEC
        # Find objects in a circle around a bright object
        RA_dist, DEC_dist               =   objects["RA"] - filtered_data["RA"][i], objects["DEC"] - filtered_data["DEC"][i]
        tot_distance                    =   np.sqrt(RA_dist**2 + DEC_dist**2) # Distance of each object from the one in the center
        objects                         =   objects[tot_distance <= radius] # Only keep objects within the circle (not the square)
        tot_flux                        =   np.sum(objects["Total flux"]) # Add up the total flux inside the circle - mJy
        flux.append(tot_flux)

    regions                     =   pd.DataFrame({"Name of Center": names, "RA": center_RA, "DEC": center_DEC, "Total flux": flux}, columns=["Name of Center", "RA", "DEC", "Total flux"]) # Create a dataframe
    return regions

if __name__ == "__main__":
    # Limits on location and minimum flux
    DEC_range                   =   input("What declination range around the center of the HERA FoV " + \
                                                "would you like to search in? [default: 7 degrees] ")
    if DEC_range == "":
        DEC_range                       =   "7.0" # Default declination range

    # Try to convert string to number
    try:
        DEC_range                       =   float(DEC_range)
    except ValueError:
        print("That is not a valid number. Defaulting to range of 7 degrees.")
        DEC_range                       =   7.0

    min_flux                    =   input("What minimum flux should the objects have? [default: 7 Jy] ")
    if min_flux == "":
        min_flux                        =   "7000.0" # Default minimum flux

    # Try to convert string to number
    try:
        min_flux                        =   float(min_flux) * 1000.0
    except ValueError:
        print("That is not a valid number. Defaulting to minimum flux of 7 Jy.")
        min_flux                        =   7000.0

    regions                     =   add_fluxes(DEC_range=DEC_range, min_flux=min_flux)
    print(regions)
