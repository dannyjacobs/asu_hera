from pyuvdata import UVData
import numpy as np
from copy import deepcopy
import sys
import os

# This function will split a given folder's uv files into smaller time ranges based on a given arguments

def new_uvs(uv,time,polarization,folder):
	v = deepcopy(uv)
        v.select(times=time)
        v.phase_to_time(np.median(v.time_array))
        #idx = os.path.basename(folder).find(polarization)
        name = os.path.basename(folder)[:20] + str(time[0]).split('.')[1][:5].ljust(5,'0')  + os.path.basename(folder)[27:]
        vis_file = os.path.join(os.path.dirname(folder),name)+'.uvfits'
        print 'Writing: ' + vis_file
	v.write_uvfits(vis_file,spoof_nonessential=True)
	del v

def split_time_uv(folder,n=1,path=None,polarization='xx'):
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

	uv = UVData()
	print 'Reading: ' + folder
	uv.read_miriad(folder)
	times = np.unique(uv.time_array)
	
	if path is not None:
		folder = os.path.join(path,os.path.basename(folder))

	if len(times)%n != 0:
		n_times = int(60/n)
		mod = int(len(times)%n_times)
		ts = times[-mod:]
		times = times[:-mod]
		new_uvs(uv,ts,polarization,folder)
 		n = int(len(times)/n_times)	
	times = np.split(times,n)
		
	for time in times:
		new_uvs(uv,time,polarization,folder)

if __name__ == '__main__':
	n = input('How many segments would you like to split this file into? (Default is 1) ')
	n = int(n)
	try:
                folders = sys.argv[1:]
                folders.sort()
		path = '/data6/HERA/data/IDR2.1/uvOCRSDL_time_split_data'
		for folder in folders:
                    	split_time_uv(folder,n,path=path)
        except IndexError:
                print('No file specified for conversion from miriad to uvfits')	
