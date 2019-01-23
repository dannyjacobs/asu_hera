#!/usr/bin/env python

import numpy as np
import pyuvdata
import sys
from astropy.time import Time

def find_uv_files(pol='xx', ends_with = 'uv', path=None):
	"""

	Finds all of the uv files in a given directory

	Parameters
	----------
	pol : str
		Polarization of the miriad files to search for.
	ends_with: str
		Ending of the miriad file (.uv, .uvR, .uvOR, etc.)
		Default is uv
	path: str
		Path to search for miriad files.
		Default is the current working directory.

	Returns
	-------
	array
		An array of uvfits file names

	"""

	if path is None:
		path = os.getcwd()

	folders = []

	for folder in os,listdir(path):
		#If working with other formats of uv files, such as uvR files
		#Change the end string in the following line to reflect that.
		if folder.endswith(pol + '.HH.' + ends_with):
			folders.append(os.path.join(path,folder))

	folders.sort()
	return (folders)


def miriad_to_uvfits(folder, pol='xx', path=None):
	"""

	Converts a single uv file to uvfits format

	Parameters
	----------
	folder : str
		File path of the uv file to be converted to uvfits format
	path : str
		File path where the new uvfits file will be written.
		Default is the current working directory.

	"""

	if path is not None:
		if os.path.isdir(path):
			vis_file = os.path.join(path,folder) + '.uvfits'
		else:
			raise IOError("%s not found." % path)

	else:
		vis_file = folder + '.uvfits'

	uv = pyuvdata.UVData()
	uv.read_miriad(folder,polarizations=[pol])
	uv.phase_to_time(Time(np.median(uv.time_array),format='jd'))
	uv.write_uvfits(vis_file,spoof_nonessential=True,run_check=False,run_check_acceptability=False)

if __name__ == '__main__':
	try:
		folders = sys.argv[1:]
		for folder in folders:
			miriad_to_uvfits(folder)
	except IndexError:
		print('No file specified for conversion from miriad to uvfits')
