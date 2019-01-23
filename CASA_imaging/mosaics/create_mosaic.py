#!/usr/bin/env python

'''
To run in terminal use:
python create_mosaic.py <directory of 'img.image.npz' files>
'''

import sys, os
import matplotlib.pyplot as plt
import healpy as hp
from pyuvdata import UVBeam
import numpy as np
import time

def create_beam_avg(fitsfile):
	hera_beam = UVBeam()
	hera_beam.read_beamfits(fitsfile)
	fullbeamavg=np.zeros_like(hera_beam.data_array[0][0][0][0])
	for i in range(101):
		fullbeamavg+=hera_beam.data_array[0][0][0][i]/np.max(hera_beam.data_array[0][0][0][i])
	fullbeamavg=fullbeamavg/101
	return fullbeamavg

def find_npz_files(path=None):
	'''
	Used to find image files.
	Argument:
		path - path to directory of 'img.image' files
	'''
	if path is  None:
		path = os.getcwd()

	folders = []

	for folder in os.listdir(path):
	    if folder.endswith("image.npz"):
			folders.append(os.path.join(path,folder))

	folders.sort()
	return (folders)

def beam_factor_2D(ra, dec, hera_zen_ra):
    """
    Outputs the beam factor of an objects's specified RA and Dec.
    """
    hera_ra    = ra                                    
    hera_dec   = dec                           
    rel_dec    = hera_dec + 30.72152612068925          
    rel_ra     = (hera_ra - hera_zen_ra)
    rel_ra[rel_ra > 180] -= 360
    rel_ra[rel_ra < -180] +=360
    rel_dec    = np.sqrt(rel_dec**2 + rel_ra**2)       
    np_ra      = np.arctan2(rel_dec,rel_ra)            
    np_ra      = np.rad2deg(np_ra)                     
    np_dec     = rel_dec + 90 

    global fullbeamavg

    return hp.get_interp_val(fullbeamavg,np_ra,np_dec, lonlat=True)

def data_paste_mod(npz):
    data=np.load(npz)
    coords=data['coords']
    vals=data['vals']
    nside=512
    global emptymap
    global new_beam_countl
    vals=vals.reshape(512**2)
    center_ra_dec=np.rad2deg(coords[256,256,:2])
    coords=coords.reshape((512**2,4))
    pixels=[]
    
    coords = np.rad2deg(coords[:, 0:2])
    pixels = hp.ang2pix(nside, coords[:, 0], coords[:, 1], lonlat=True)
    new_beam_count[pixels] += beam_factor_2D(coords[:, 0], coords[:, 1],center_ra_dec[0])        
            
    emptymap[pixels]+=vals
    return emptymap


if __name__ == '__main__':
	try:
		arg = sys.argv[-2:]
		print 'Directory of image dictionaries being used is:'+arg[0]
		print 'Beam fitsfile being used is:'+arg[1]
		folders = find_npz_files(arg[0])
		nside=512
		fullbeamavg = create_beam_avg(arg[1])
		emptymap=np.zeros(hp.nside2npix(nside))
		new_beam_count=np.zeros(hp.nside2npix(nside))
		for folder in folders:
			data_paste_mod(folder)
		beam_sum_map = hp.mollview(new_beam_count,return_projected_map=True)
		projected_map = hp.mollview(emptymap+2,norm='log',max=2.05,xsize=4800,return_projected_map=True)
		#beam_sum_map.savefig(str(time.time())+'beam_sum_map',format='png')
		#projected_map.savefig(str(time.time())+'projected_map', format='png')
		plt.show()
	except IndexError:
		print('No file specified')

'''
nside=512
emptymap=np.zeros(hp.nside2npix(nside))
new_beam_count=np.zeros(hp.nside2npix(nside))

for i in log_progress(range(len(newlist[:]))):
    data_paste_mod(newlist[i])
'''

