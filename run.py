'''

Tweak the calibration and clean parameters and the mask below to set the values
for an imaging run of the night sky.

To run (in terminal):
casa -c run.py <measurement sets>

'''

from process_ms import *
import numpy as np

# Calibration Parameters
gc                  =   'zen.2458042.12552.xx.HH.uvR.uvfits.msG.cal'
kc                  =   'zen.2458042.12552.xx.HH.uvR.uvfits.msK.cal'
bc                  =   'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msB.cal'
bc1                 =   'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msc2.msB.cal'
gaintable           =   [kc, gc, bc, bc1]

# Clean Parameters
niter               =   6000
weighting           =   'briggs'
robust              =   -0.5
imsize              =   [512,512]
cell                =   ['250arcsec']
mode                =   'mfs'
nterms              =   1
spw                 =   '0:100~800'
phasecenter         =   ''

img_dir = 'cygnus_a'

if __name__ == '__main__':
    try:
        # Create a variable to hold the filenames of the measurement sets defined
        # by the user and sort them
        folders = sys.argv[3:]
        folders.sort()

        # Check to see that the calibration files exist. If they do not exist,
        # generate them.
        check_f = [os.path.isdir(l) for l in gaintable]
        if not all(check_f):
            gaintable = make_initial_image(folders[0])
            del folders[0]
        # Process each measurement set in the list of measurement sets
        for folder in folders:
            # Create the mask for clean
            tb.open(os.path.join(folder,'SOURCE'))
            angle = tb.getcol('DIRECTION')[0][0]
	    if angle < 0:
		angle += 2*np.pi
	    ra = convert_angle(angle)
            tb.close()
	    fov = .6206 # HERA field of view in radians
	    #Bright sources from Lily's code
	    # Fornax, TGSSADR J020012.1-305327, TGSSADR j045514.2-300650, TGSSADR J174024.3-305744 
	    srcs = {0.884424: ['-37d12m30.0s','2000arcsec'], 0.5245: ['-30d53m27.82s','2000arcsec'], 1.2882: ['-30d6m50.37s','2000arcsec'], 4.62689: ['-30d53m27.82s','8000arcsec']}
	    mask = 'circle[[' + ra + ', -29d00m00.0s], 32000arcsec]'
	    print (angle-fov/2,angle+fov/2)
	    srcs_arr = [src for src,_ in srcs.items() if angle-fov/2 <= src <= angle+fov/2] # check if sources cross into the FOV
            final_srcs = dict([(k,srcs.get(k)) for k in srcs_arr]) 
	    
	    if len(final_srcs) > 0:    
		fname = folder[15:20]+'.rgn'
                with open(fname,'w') as f:
                    f.write('#CRTFv0\n')
                    f.write(mask+'\n')
		    for ra,dec in final_srcs.items():
                    	f.write('circle[[' + convert_angle(ra) + ', ' + dec[0] + '], '+ dec[1]  +']\n')
                    mask = fname
	    # Process measurement set

            make_image(folder,img_dir,gaintable,niter=niter,weighting=weighting,
                       robust=robust, imsize=imsize, cell=cell, mode=mode,
                       nterms=nterms,spw=spw,mask=mask,phasecenter=phasecenter)

    except IndexError:
        print ('File not specified')
