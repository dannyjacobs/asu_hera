'''

Script to generate image from ms data sets using David's procedure

Usage:
    casa -c gen_image.py zen.2450842.*.xx.HH.uvR.uvfits.ms

'''

import os
from casa import *
import numpy as np

def calname(m,c):
    return (os.path.basename(m)+c+".cal")

def flag(infile):
    #flag autocorrelations
    flagdata(infile, autocorr=True)

def calinitial(infile,cal='GC.cl'):
    # use the ft function to write the model into a file
    # (not as an actual transform)
    ft(infile, complist=cal, usescratch=True)

    #create calibration files
    kc=calname(infile, "K")
    gaincal(infile, caltable=kc, gaintype='K', solint='inf', refant='11', minsnr=1, spw='0:100~130, 0:400~600')

    #check for frequency errors
    gc=calname(infile, "G")
    gaincal(infile, caltable=gc, gaintype='G', solint='inf', refant='11', minsnr=2, calmode='ap', gaintable=kc)
    apply_cal(infile, kc, gc)
    return (kc,gc)

def apply_cal(infile,*argv):
    applycal(infile,gaintable=argv)

def split_initial(infile):
    #split to trick casa into allowing  another calibration
    split(infile, os.path.basename(infile) + "split" + ".ms", datacolumn="corrected", spw="")

def do_clean(infile, imgname):
    #cleaning the data
    tb.open(os.path.join(file_to_clean,'SOURCE'))
    ra = convert_angle(tb.getcol('DIRECTION')[0][0])
    tb.close()
    clean(vis=infile, imagename=imgname, niter=500, weighting='briggs',
          robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs',nterms=1,
          spw='0:150~900',mask="circle[[17h45m00.0s, -29d.00m.00.0s], 32000arcsec]")

def do_band_pass(infile,bc=None):
    #apply bandpass on split data
    if bc is None:
        bc=calname(infile, "B")
    bandpass(vis=infile, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(infile, gaintable=[bc])
    return (bc)

def do_split(infile):
    #split again for the same reasons
    split(file_to_clean, os.path.basename(infile) + "c2" + ".ms",
          datacolumn="corrected", spw="0:100~800")

def clean_final(infile,imgname,mask=None):
    '''

    '''
    tb.open(os.path.join(infile,'SOURCE'))
    ra = convert_angle(tb.getcol('DIRECTION')[0][0])
    tb.close()
    if mask is None:
        mask = 'circle[['+ ra +', -29d00m00.0s], 32000arcsec]'
    clean(vis=infile, imagename=imgname, niter=5000, weighting='briggs',
          robust=-0.5, imsize=[512,512], cell=['250arcsec'], mode='mfs',
          nterms=1, spw='0:100~800', mask=mask)

def convert_angle(angle):
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


def make_initial_image(infile,img_dir='imgs'):
    if not os.path.exists(img_dir):
        os.makedirs(directory)

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nInitial Calibration...\n')
    kc, gc = calinitial(infile)
    imgname = os.path.basename(infile)+ ".init.img"
    file_to_clean = os.path.basename(infile) + "split" + ".ms"

    print ('\nSplitting Columns...\n')
    split_initial(infile)

    print ('\nCleaning Data...\n')
    do_clean(file_to_clean, imgname)

    print ('\nRunning Band Pass...\n')
    bc = do_band_pass(file_to_clean)

    print ('\nSplitting Columns...\n')
    do_split(file_to_clean)
    file_2_clean= os.path.basename(file_to_clean) + "c2" + ".ms"
    imgname2= os.path.basename(file_to_clean)+".init.img"

    print ('\nCleaning Data...\n')
    do_clean(file_2_clean,imgname2)

    print ('\nRunning Band Pass...\n')
    bc1 = do_band_pass(file_2_clean)
    file_3_clean = file_2_clean
    imgnameFinal = infile + "Final.combined.img"
    imgnameFinal = os.path.join(img_dir,os.path.basename(imgnameFinal))

    print ('\nFinal Clean...\n')
    clean_final(file_3_clean, imgnameFinal)

    return (kc,gc,bc,bc1)

def make_image(infile,kc,gc,bc,bc1):
    '''
    Flags, calibrates, and cleans a measurement single measurement set

    Parameters
    ----------
    infile : str
        Name of the measurement set to process
    kc : str
        File name of
    '''
    print ('Running File: ' + infile)
    img_dir='imgs'
    if not os.path.exists(img_dir):
        os.makedirs(directory)

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nInitial Calibration...\n')
    apply_cal(infile,kc,gc,bc,bc1)
    imgnameFinal = infile + "Final.combined.img"
    imgnameFinal = os.path.join(img_dir,os.path.basename(imgnameFinal))

    print ('\nFinal Clean...\n')
    clean_final(infile, imgnameFinal)
    exportfits(imagename=(imgnameFinal+'.image'),fitsimage=(imgnameFinal+'.fits'))


if __name__ == "__main__":
    try:
        #
        folders = sys.argv[3:]
        folders.sort()

        # Default calibration files to apply calibration to
        gc = 'zen.2458042.12552.xx.HH.uvR.uvfits.msG.cal'
        kc = 'zen.2458042.12552.xx.HH.uvR.uvfits.msK.cal'
        bc = 'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msB.cal'
        bc1 = 'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msc2.msB.cal'

        # If these files do not exist, create calibration files from the first
        # measurement set in the list of measurement sets
        check_f = [os.path.isfile(l) for l in [gc,kc,bc,bc1]]
        if all(check_f):
            kc,gc,bc,bc1 = make_initial_image(folders[0])
            del folders[0]

        # Process each measurement set in the list of measurement sets
        for folder in folders:
            make_image(folder,kc,gc,bc,bc1)
    except IndexError:
        print ('File not specified')
