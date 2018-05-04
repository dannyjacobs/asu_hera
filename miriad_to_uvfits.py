#!/usr/bin/env python

import numpy as np
import pyuvdata
import sys


def find_uvR_files(polarization='xx',path=None):
	"""
	
	Finds all of the uvR files in a given directory

	Parameters
	----------
	polarization : str
		Polarization of the uvfits files to search for.
		Default is the current working directory.

	Returns
	-------
	array
		An array of uvfits file names	

	"""
	
	if path is  None:
		path = os.getcwd()

	folders = []

	for folder in os,listdir(path):
		if (folder[-9:]) == polarization + '.HH.uvR':
			folders.append(os.path.join(path,folder))

	folders.sort()
	return (folders)


def miriad_to_uvfits(folder,path=None):
	"""

	Converts a single uvR file to uvfits format

	Parameters
	----------
	folder : str
		File path of the uvR file to be converted to uvfits format
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
	uv.read_miriad(folder)
	uv.phase_to_time(np.median(uv.time_array))
	uv.write_uvfits(vis_file,spoof_nonessential=True)

if __name__ == '__main__':
	try:
		folder = sys.argv[1:]
		if type(folders) == str:
			miriad_to_uvfits(folder)
		else:
			for folder in folders:
				miriad_to_uvfits(folder)
	except IndexError:
		print('No file specified for conversion from miriad to uvfits')
