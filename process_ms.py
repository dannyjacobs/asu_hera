'''

Script to generate image from a measurement set using David's procedure

'''

import os
from casa import *
import numpy as np

def calname(m,c):
    '''
    Returns the file name for the new calibration file to be generated

    Parameters
    ----------
    m : str
        input measurement set file name
    c : str
        calibration being done

    Returns
    -------
    str
        file name of the new calibration file
    '''
    return (os.path.basename(m)+c+".cal")

def flag(infile):
    '''
    Flags the data in a measurement set using auto-correlations

    Parameters
    ----------
    infile : str
        input measurement set file name
    '''
    flagdata(infile, autocorr=True)

def calinitial(infile,cal='GC.cl'):
    '''
    Creates the initial calibration files using a calibration model to applies
    that calibration to a measurement set

    Parameters
    ----------
    infile : str
        input measurement set file name
    cal : str
        file name of the calibration model
        default: GC.cl (galactic model)

    Returns
    -------
    kc, gc : str
        file names of the new calibration files
    '''
    # use the ft function to write the model into a file
    # (not as an actual transform)
    ft(infile, complist=cal, usescratch=True)

    #create calibration files
    kc=calname(infile, "K")
    gaincal(infile, caltable=kc, gaintype='K', solint='inf', refant='11', minsnr=1, spw='0:100~130, 0:400~600')

    #check for frequency errors
    gc=calname(infile, "G")
    gaincal(infile, caltable=gc, gaintype='G', solint='inf', refant='11', minsnr=2, calmode='ap', gaintable=kc)

    # Apply the calibration to the infile
    apply_cal(infile, kc, gc)
    return (kc,gc)

def apply_cal(infile,gaintable):
    '''
    Applies a set of calibration files to a measurement set

    Parameters
    ----------
    infile : str
        input measurement set file name
    gaintable : str, list
        Takes a string or list of strings that are the file names of the
        calibration files being applied to the measurement sets

    '''
    applycal(infile,gaintable=gaintable)

def do_split(infile,outfile,spw=""):
    '''
    Creates a measurement subset from an existing measurement set to trick casa
    to allow another calibration

    Parameters
    ----------
    infile : str
        input measurement set file name
    outfile : str
        output measurement set file name
    spw : str
        spectral window for the split to isolate
            default : ""
    '''
    #split to trick casa into allowing  another calibration
    split(infile, outfile, datacolumn="corrected", spw=spw)

def do_clean(infile, imgname):
    '''
    Deconvolves a measurement set and produces an image

    Parameters
    ----------
    infile : str
        input measurement set file name
    imgname : str
        file name of the output image files
    '''
    tb.open(os.path.join(file_to_clean,'SOURCE'))
    ra = convert_angle(tb.getcol('DIRECTION')[0][0])
    tb.close()
    clean(vis=infile, imagename=imgname, niter=500, weighting='briggs',
          robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs',nterms=1,
          spw='0:150~900',mask="circle[["+ ra +", -29d.00m.00.0s], 32000arcsec]")

def do_band_pass(infile):
    '''
    Creates a bandpass calibration solution

    Parameters
    ----------
    infile : str
        input measurement set file name
    '''
    bc=calname(infile, "B")
    bandpass(vis=infile, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(infile, gaintable=[bc])
    return (bc)

def clean_final(infile,imgname,**kwargs):
    '''
    Deconvolves a measurement set and produces an image

    Parameters
    ----------
    infile : str
        input measurement set file name
    imgname : str
        file name of the output image files

    Other Parameters
      ----------------
        **kwargs : casa "clean" properties.
            examples : clean_final(..., ..., niter = 1000)
    '''
    clean(infile, imgname, kwargs)

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
    '''
    Runs the full processing algorithm including calibration file creation on
    a measurement set. This is used to calibrate subsequent files to an initial
    source

    Parameters
    ----------
    infile : str
        input measurement set file name
    img_dir : str
        directory name where image files are written
    '''
    if not os.path.exists(img_dir):
        os.makedirs(directory)

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nInitial Calibration...\n')
    kc, gc = calinitial(infile)
    imgname = os.path.basename(infile)+ ".init.img"
    file_to_clean = os.path.basename(infile) + "split" + ".ms"

    print ('\nSplitting Columns...\n')
    do_split(infile,os.path.basename(infile) + "split" + ".ms")

    print ('\nCleaning Data...\n')
    do_clean(file_to_clean, imgname)

    print ('\nRunning Band Pass...\n')
    bc = do_band_pass(file_to_clean)

    print ('\nSplitting Columns...\n')
    do_split(file_to_clean,os.path.basename(infile) + "c2" + ".ms",spw="0:100~800")
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

def make_image(infile, gaintable, niter = 5000, weighting = 'briggs', robust = -0.5,
               imsize = [512,512], cell = ['250arcsec'], mode = 'mfs', nterms = 1
               spw = '0:100~800'):
    '''
    Flags, calibrates, and cleans a measurement single measurement set

    Parameters
    ----------
    infile : str
        name of the measurement set to process
    gaintable : str, list
        string or list of strings of calibration file names to use to calibrate
        measurement sets
    '''
    print ('Running File: ' + infile)
    img_dir='imgs'
    if not os.path.exists(img_dir):
        os.makedirs(directory)

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nCalibrating Data...\n')
    apply_cal(infile,gaintable)
    imgnameFinal = infile + "Final.combined.img"
    imgnameFinal = os.path.join(img_dir,os.path.basename(imgnameFinal))

    print ('\nCleaning...\n')
    clean(infile, imgnameFinal, niter=niter,weighting=weighting,
               robust=robust, imsize=imsize, cell=cell, mode=mode,
               nterms=nterms,spw=spw,mask=mask)

    exportfits(imagename=(imgnameFinal+'.image'),fitsimage=(imgnameFinal+'.fits'))
