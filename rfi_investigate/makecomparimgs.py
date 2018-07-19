# This python script is intended to take a couple of specified images
# and do the appropriate tasks for our imaging pipeline. It is intended to 
# be run using CASA from the command line, and has CASA commands in it.
#
# Run this command using casa -c 

import numpy as np
from casa import *
import os
from glob import glob

#Obserations to Image
filepath1='/data6/HERA/data/2458042'
filepath2='/data6/HERA/data/2458140/dml_uv_files2/'
file_locations1=glob('../../2458042/KM_uvR_files/*xx.HH.uvR.uvfits')
file_locations2=glob(filepath2 + '*.xx.HH.uvc.uvfits')
file_locations1.sort()
file_locations2.sort()
filenameind=len(filepath2)

#file_list1=[file[27:]for file in file_locations1]
file_list2=[file[filenameind:]for file in file_locations2]

#Output path
fileout='/data6/HERA/HERA_imaging/rfi_investigate/dml_img_files/'

#Clean Params
niter=0
weighting='briggs'
robust=-0.5
imsize=[512,512]
cell=['500arcsec']
cell2=['1000arcsec']
mode='mfs'
nterms=1
spw='0:100~800'
phasecenter=''
mask='circle[[256pix,256pix],3200arcsec]'

#start processing
'''
for file in range(len(file_list1)):
	print('Importing '+file_locations1[file])
	importuvfits(file_locations1[file],fileout+file_name1[i]+'.ms')
	print('Flagging '+file_list1[file])
	flagdata(fileout+file_name1[i]+'.ms', autocorr=True)
	# Note: calibration was applied in Jupyter Notebook, this line is no longer valid.
	#print('Calibrating...'+file_list1[file]+'.ms')
	#applycal(fileout+file_list1[i]+'.ms', gaintable=[kc,gc,bc,bc1])
	print ('Clean 1: '+file_list1[file]+'.ms')	
	clean(fileout+file_list1[i]+'.ms',fileout+file_list1[i]+'.ms.img',niter=niter, weighting=weighting, robust=robust, imsize=imsize, cell=cell, mode=mode,nterm=nterm, spw=spw, phasecenter=phasecenter, mask=mask)
	print('Clean 2: '+file_list1[file]+'.ms')
	clean(fileout+file_list1[i]+'.ms',fileout+file_list1[i]+'.ms.img',niter=niter, weighting=weighting, robust=robust, imsize=imsize, cell=cell2, mode=mode,nterm=nterm, spw=spw, phasecenter=phasecenter, mask=mask)

'''

#filestofinish=np.arange(0,72)
for i,file in enumerate(file_list2):
	print('Importing '+file_locations2[i])
        importuvfits(file_locations2[i],fileout+file_list2[i]+'.ms')
        print('Flagging '+file_list2[i]+'.ms')
        flagdata(fileout+file_list2[i]+'.ms', autocorr=True)
        # Note: calibration was applied in Jupyter Notebook, this line is no longer valid.
        #print('Calibrating...'+file_list2[file]+'.ms')
        #applycal(fileout+file_list2[file]+'.ms', gaintable=[kc,gc,bc,bc1])
        print ('Clean 1: '+file_list2[i]+'.ms')      
        clean(file_locations2[i]+'.ms',fileout+file_list2[i]+'.ms.img',niter=niter, weighting=weighting, robust=robust, imsize=imsize, cell=cell, mode=mode,nterms=nterms, spw=spw, phasecenter=phasecenter, mask=mask)
        print('Clean 2: '+file_list2[i]+'.ms')
        clean(file_locations2[i]+'.ms',fileout+file_list2[i]+'.ms.img2',niter=niter, weighting=weighting, robust=robust, imsize=imsize, cell=cell2, mode=mode,nterms=nterms, spw=spw, phasecenter=phasecenter, mask=mask)

'''
#print(file_list1)
print(file_list2)
'''
