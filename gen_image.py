'''

Script to generate image from ms data sets using David's procedure

'''


import os
from casa import *
from astropy.time import Time


def calname(m,c):
    return os.path.basename(m)+c+".cal"

def flag(infile):
    #flag autocorrelations
    flagdata(infile, autocorr=True)

def calinitial(infile):
    # use the ft function to write the model into a file
    # (not as an actual transform)
    ft(infile, complist="GC.cl", usescratch=True)

    #create calibration files
    kc=calname(infile, "K")
    gc=calname(infile, "G")
    #check for delays and errors
    gaincal(infile, caltable=kc, gaintype='K', solint='inf', refant='11', minsnr=1, spw='0:100~130, 0:400~600')
    #check for frequency errors
    gaincal(infile, caltable=gc, gaintype='G', solint='inf', refant='11', minsnr=2, calmode='ap', gaintable=kc)
    applycal(infile, gaintable=[kc, gc])
    return (kc,gc)


def apply_cal(infile,kc,gc,bc,bc1):
    applycal(infile,gaintable=[kc,gc,bc,bc1])

def split_initial(infile):
    #split to trick casa into allowing  another calibration
    split(infile, os.path.basename(infile) + "split" + ".ms", datacolumn="corrected", spw="")

def file_to_name(infile):
    #initialize variables for cleaning
    imgname=os.path.basename(infile)+ ".init.img"
    file_to_clean=os.path.basename(infile) + "split" + ".ms"
    return (file_to_clean, imgname)

def do_clean(file_to_clean, imgname):
    #cleaning the data
    clean(vis=file_to_clean, imagename=imgname, niter=500, weighting='briggs',
          robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs',nterms=1,
          spw='0:150~900',mask="circle[[17h45m00.0s, -29d.00m.00.0s], 32000arcsec]")

def do_band_pass(file_to_clean,bc=None):
    #apply bandpass on split data
    if bc is None:
        bc=calname(file_to_clean, "B")
    bandpass(vis=file_to_clean, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(file_to_clean, gaintable=[bc])
    return (bc)

def do_split(file_to_clean):
    #split again for the same reasons
    split(file_to_clean, os.path.basename(file_to_clean) + "c2" + ".ms",
          datacolumn="corrected", spw="0:100~800")

def file_2_names(file_to_clean):
    #clean this new split
    file_2_clean=os.path.basename(file_to_clean) + "c2" + ".ms"
    imgname2=os.path.basename(file_2_clean)+".init.img"
    return (file_2_clean, imgname2)


def file_3_names(file_2_clean):
    #final cleaning pass on the double-split cleaned data
    file_3_clean=file_2_clean
    imgnameFinal=file_3_clean + "Final.combined" + ".img"
    return (file_3_clean,imgnameFinal)

def deg_to_ra():
    pass

def clean_final(file_3_clean,imgnameFinal):
    tb.open(file_3_clean+'/FIELD')
    t_mjd = Time(np.median(tb.getcol('TIME'))/(60*60*24), format='mjd', scale='utc', location=(21.42822, -30.72146))
    sidereal = t_mjd.sidereal_time('apparent')
    clean(vis=file_3_clean, imagename=imgnameFinal, niter=5000, weighting='briggs',robust=-0.5, imsize=[512,512], cell=['250arcsec'],mode='mfs',nterms=1,spw='0:60~745', mask=('circle[['+ sidereal +', -29d00m00.0s], 32000arcsec]'))

def make_initial_image(infile):
    img_dir = 'imgs'

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nInitial Calibration...\n')
    kc, gc = calinitial(infile)
    file_to_clean, imgname = file_to_name(infile)

    print ('\nSplitting Columns...\n')
    split_initial(infile)

    print ('\nCleaning Data...\n')
    try:
        do_clean(file_to_clean, imgname)
    except:
        pass

    print ('\nRunning Band Pass...\n')
    bc = do_band_pass(file_to_clean)

    print ('\nSplitting Columns...\n')
    do_split(file_to_clean)
    file_2_clean,imgname2 = file_2_names(file_to_clean)

    print ('\nCleaning Data...\n')
    try:
        do_clean(file_2_clean,imgname2)
    except:
        pass

    print ('\nRunning Band Pass...\n')
    bc1 = do_band_pass(file_2_clean)
    file_3_clean, imgnameFinal = file_3_names(file_2_clean)
    imgnameFinal = os.path.join(img_dir,os.path.basename(imgnameFinal))

    print ('\nFinal Clean...\n')
    try:
        clean_final(file_3_clean, imgnameFinal)
    except:
        pass

    return (kc,gc,bc,bc1)

def make_image(infile,kc,gc,bc,bc1):
    img_dir = 'imgs'

    print ('\nFlagging Data...\n')
    flag(infile)

    print ('\nInitial Calibration...\n')
    apply_cal(infile,kc,gc,bc,bc1)
    file_to_clean, imgnameFinal = file_3_names(infile)
    imgnameFinal = os.path.join(img_dir,os.path.basename(imgnameFinal))

    print ('\nFinal Clean...\n')
    clean_final(file_to_clean, imgnameFinal)

    return (kc,gc,bc,bc1)

def find_ms_files(path=None):
    """

    Finds all of the uvfits files in a given directory

    Parameters
    ----------
    path : str
        Folder path where the function looks for uvfits files.
        Default is the current working directory.
    polarization : str
        Polarization of the uvfits files to search for.
        Default is xx polarization

    Returns
    -------
    array
        An array of uvfits file names

    """

    if path is None:
        path = os.getcwd()

    folders = []

    for folder in os.listdir(path):
        if folder.endswith('.ms'):
            folders.append(os.path.join(path,folder))

    folders.sort()
    return (folders)




if __name__ == "__main__":
    folders = sys.argv[3:]
    folders.sort()
    #gc,kc,bc,bc1 = make_initial_image(folders[0])
    print (folders)
    gc = 'zen.2458042.12552.xx.HH.uvR.uvfits.msG.cal'
    kc = 'zen.2458042.12552.xx.HH.uvR.uvfits.msK.cal'
    bc = 'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msB.cal'
    bc1 = 'zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msc2.msB.cal'
    for folder in folders:
        make_image(folder,kc,gc,bc,bc1)
