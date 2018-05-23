'''

Tweak the calibration and clean parameters and the mask below to set the values
for an imaging run of the night sky.

To run (in terminal):
casa -c run.py <measurement sets>

'''

from process_ms import *

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
            ra = convert_angle(tb.getcol('DIRECTION')[0][0])
            tb.close()
            mask = 'circle[['+ ra +', -29d00m00.0s], 32000arcsec]'
            # Process measurement set
            make_image(folder,gaintable=gaintable,niter=niter,weighting=weighting,
                       robust=robust, imsize=imsize, cell=cell, mode=mode,
                       nterms=nterms,spw=spw,mask=mask)

    except IndexError:
        print ('File not specified')
