import os
from casa import *

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

def split_initial(infile):
    #split to trick casa into allowing  another calibration
    split(infile, os.path.basename(infile) + "split" + ".ms", datacolumn="corrected", spw="")

def file_to_name(infile):
    #initialize variables for cleaning
    imgname=os.path.basename(infile)+ ".init.img"
    file_to_clean=os.path.basename(infile) + "split" + ".ms"
    return (file_to_clean,imgname)

def do_clean(file_to_clean, imgname):
    #cleaning the data
    clean(vis=file_to_clean, imagename=imgname, niter=500, weighting='briggs',robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs',nterms=1,spw='0:150~900',mask="circle[[17h45m00.0s, -29d.00m.00.0s], 32000arcsec]")

def do_band_pass(find_to_clean):
    #apply bandpass on split data
    bc=calname(file_to_clean, "B")
    bandpass(vis=file_to_clean, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(file_to_clean, gaintable=[bc])

def do_split(file_to_clean):
    #split again for the same reasons
    split(file_to_clean, os.path.basename(file_to_clean) + "c2" + ".ms", datacolumn="corrected", spw="0:100~800")

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

def clean_final(file_3_clean,imgnameFinal):
    clean(vis=file_3_clean, imagename=imgnameFinal, niter=5000, weighting='briggs', robust=-0.5, imsize=[512,512], cell=['250arcsec'],mode='mfs',nterms=1, spw='0:60~745', mask="circle[[17h45m00.0s, -29d00m00.0s], 32000arcsec]")

if __name__ == "__main__":
    infile = sys.argv[3]
    print ('\n\nFlagging Data...\n\n')
    flag(infile)
    print ('\n\nInitial Calibration...\n\n')
    kc,gc = calinitial(infile)
    file_to_clean, imgname = file_to_name(infile)
    print ('\n\nSplitting Columns...\n\n')
    split_initial(infile)
    print ('\n\nCleaning Data...\n\n')
    try:
        do_clean(file_to_clean, imgname)
    except:
        pass
    print ('\n\nRunning Band Pass...\n\n')
    do_band_pass(file_to_clean)
    print ('\n\nSplitting Columns...\n\n')
    do_split(file_to_clean)
    file_2_clean,imgname2 = file_2_names(file_to_clean)
    print ('\n\nCleaning Data...\n\n')
    try:
        do_clean(file_2_clean,imgname2)
    except:
        pass
    print ('\n\nRunning Band Pass...\n\n')
    do_band_pass(file_2_clean)
    file_3_clean, imgnameFinal = file_3_names(file_2_clean)
    print ('\n\nFinal Clean...\n\n')
    try:
        clean_final(file_3_clean, imgnameFinal)
    except:
        pass
