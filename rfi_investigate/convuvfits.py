#Quick script to convert UVOR files here into uvfits

import numpy as np
import pyuvdata
from pyuvdata import UVData
from hera_cal import apply_cal as ac
from glob import glob

#calfile='../zen.2458140.31206.xx.HH.uv.first.calfits'
calfile='../zen.2458140.45373.xx.HH.uv.first.calfits'

'''
uv=UVData()
file_list=glob('../*.uv')
file_list.sort()
file_list=[file[3:]for file in file_list]
print(file_list)
'''

uv=UVData()
file_list=glob('../*.uv')
#file_list=['../zen.2458140.66252.xx.HH.uv']
file_list.sort()
file_names=[file[3:] for file in file_list]
#file_out=['../dml_uv_files/'+file+'c' for file in file_names]
file_out=['../dml_uv_files2/'+file+'c' for file in file_names] #second run with different cal file
file_names2=[file+'c' for file in file_names]

'''
for i in range(len(file_list)):
	print('Accessing '+file_list[i]+'...')
	uv.read_miriad('../'+file_list[i])
	print('Phasing...')
	uv.phase_to_time(np.median(uv.time_array))
	print('Writing...')
	uv.write_uvfits('../dml_uvfits/'+file_list[i]+'.uvfits', force_phase=True, spoof_nonessential=True)
	print('Done!')
'''

for i in range(len(file_list)):
    #calibrate
    print('Calibrating '+file_names[i]+'...')
    ac.apply_cal(file_list[i],file_out[i],calfile)
    #read
    print('Accessing ' +file_names2[i]+'...')
    uv.read_miriad(file_out[i])
    print('Phasing...')
    uv.phase_to_time(np.median(uv.time_array))
    print('Writing...')
    uv.write_uvfits(file_out[i]+'.uvfits', force_phase=True, spoof_nonessential=True)
