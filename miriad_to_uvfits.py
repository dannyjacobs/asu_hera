#!/usr/bin/env casapy

import pyuvdata
import sys


def miriad_to_uvfits(folder):
	uv = pyuvdata.UVData()
	uv.read_miriad(folder)
	uv.phase_to_time(uv.time_array.median())
	uv.write_uvfits(folder + '.uvfits',spoof_nonessential=True)

if __name__ == '__main__':
	try:
		folder = sys.argv[1]
		miriad_to_uvfits(folder)
	except IndexError:
		print('No file specified for conversion from miriad to uvfits')
