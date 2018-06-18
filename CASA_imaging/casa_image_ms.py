'''
Tweak the calibration and clean parameters in the run.json file
for an imaging run of the sky.

To run (in terminal):
casa -c casa_image_ms.py -p <run paramters>.json -f <measurement sets>.ms

'''
from casa import *
import numpy as np
import os
import json
import argparse
from process_ms import CASA_Imaging

def rad_to_hms(angle):
    '''
    Converts an angle in radians to a right ascension

    Parameters
    ----------
    angle : float
        angle to be converted in radians

    Returns
    -------
    ra : string
        right ascension calculated from the angle given in hours, minutes, and seconds
    '''
    if (angle < 0):
        angle += (2*np.pi)
    time = (angle/(2*np.pi))*24
    hours = int(time)
    time = (time%1)*60
    mins = int(time)
    secs = (time%1)*60
    ra = str(hours) + 'h' + str(mins) + 'm' + str(secs) + 's'
    return (ra)

def dd_to_dms(angle):
    '''
    Converts an angle in decimal degrees to a degrees, minutes, and seconds

    Parameters
    ----------
    angle : float
        angle to be converted in decimal degrees

    Returns
    -------
    ra : string
        right ascension calculated from the angle given in degrees, minutes, and seconds
    '''
    neg = degs < 0
    degs = (-1) ** neg * degs
    degs, d_int = np.modf(degs)
    mins, m_int = np.modf(60 * degs)
    secs        =           60 * mins
    if neg:
        return (str(int(-d_int)) + 'd' + str(int(m_int)) +'m'+ str(secs) + 's')
    return (str(int(d_int)) + 'd' + str(int(m_int)) +'m'+ str(secs) + 's')

def find_ra_dec(folder):
    tb.open(os.path.join(folder,'SOURCE'))
    angle_ra = tb.getcol('DIRECTION')[0][0]
    angle_dec = tb.getcol('DIRECTION')[1][0]
    ra = rad_to_hms(angle_ra)
    dec = dd_to_dms(np.rad2deg(angle_dec))
    tb.close()
    return ra, dec


def set_mask(ra, dec, srcs, mask_size='32000arcsec', imsize=512, cell_size=250):
    fov = np.deg2rad((imsize * cell_size)/3600)
    mask = 'circle[[' + ra + ', ' + dec + '], ' + mask_size + ']'
    final_srcs = {k: src for k,src in srcs.iteritems() if angle_ra-fov/2 <= src['RA'] <= angle_ra+fov/2} # check if sources cross into the FOV
    if len(final_srcs) > 0:
        fname = 'mask.rgn'
        with open(fname,'w') as f:
            f.write('#CRTFv0\n')
            f.write(mask+'\n')
            for _,v in final_srcs.iteritems():
                f.write('circle[[' + convert_angle(v['RA']) + ', ' + dd_to_dms(v['DEC']) + '], 2000arcsec]\n')
        mask = fname
    return mask

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Get some files according to a pattern')
    parser.add_argument("-p", "--params", required=True,
                        help="Name of the parameter file for this particular run")
    parser.add_argument('-f','--run_files', type=str, action='store', nargs='+',
                        help="Name of the measurement set(s) being processed by \
                              the run script.")
    args = parser.parse_args()

    folders = args.run_files
    folders.sort()

    config = args.params

    with open(config) as f:
        config_data = json.load(f)

    ci = CASA_Imaging(config_data)

    if config_data['new_calibration']:
        gaintable = create_cal_files()

    sources_file = config_data['clean_mask_sources']['file_name']
    mask_dec = config_data['base_mask_params']['dec']
    mask_radius = config_data['base_mask_params']['radius']
    
    with open(sources_file) as f:
        sources = json.load(f)

    for folder in folders:
        ra, _ = find_ra_dec(folder)
        mask = set_mask(ra,mask_dec,sources,mask_size=mask_radius)
        ci.make_image(folder)
