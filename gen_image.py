import os
import casa

def calname(m,c):
    return os.path.basename(m)+c+".cal"

def make_image(infile,cal):
    #flag autocorrelations
    flagdata(infile, autocorr=True)
    print  ('\n\n\n\nFlag\n\n\n\n')
    # use the ft function to write the model into a file
    # (not as an actual transform)
    ft(infile, complist="GC.cl", usescratch=True)
    print  ('\n\n\n\nft\n\n\n\n')

    #create calibration files
    kc=calname(infile, "K")
    gc=calname(infile, "G")
    print (kc,gc)
    print  ('\n\n\n\nCalibration\n\n\n\n')
    #check for delays and errors

    gaincal(infile, caltable=kc, gaintype='K', solint='inf', refant='11', minsnr=1, spw='0:100~130, 0:400~600')
    #check for frequency errors
    gaincal(infile, caltable=gc, gaintype='G', solint='inf', refant='11', minsnr=2, calmode='ap', gaintable=kc)

    print  ('\n\n\n\nCalibration\n\n\n\n')

    #split to trick casa into allowing  another calibration
    applycal(infile, gaintable=[kc, gc])
    split(infile, os.path.basename(infile) + "split" + ".ms", datacolumn="corrected", spw="")

    print  ('\n\n\n\nCalibration\n\n\n\n')

    #initialize variables for cleaning
    imgname=os.path.basename(infile)+ ".init.img"
    file_to_clean=os.path.basename(infile) + "split" + ".ms"

    print  ('\n\n\n\nCalibration\n\n\n\n')

    #cleaning the data
    clean(vis=file_to_clean, imagename=imgname, niter=500, weighting='briggs',robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs',nterms=1,spw='0:150~900',mask='circle[[17h45m00.0s, -29d.00m.00.0s], 32000arcsec]')

    #apply bandpass on split data
    bc=calname(file_to_clean, "B")
    bandpass(vis=file_to_clean, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(file_to_clean, gaintable=[bc])

    #split again for the same reasons
    split(file_to_clean, os.path.basename(file_to_clean) + "c2" + ".ms", datacolumn="corrected", spw="0:100~800")

    #clean this new split
    file_2_clean=os.path.basename(file_to_clean) + "c2" + ".ms"
    imgname2=os.path.basename(file_2_clean)+".init.img"
    clean(vis=file_2_clean, imagename=imgname2, niter=500, weighting='briggs', robust=-0.5,imsize=[512,512], cell=['500arcsec'], mode='mfs', nterms=1, spw='0:150~900', mask='circle[[17h45m00.0s, -29d00m00.0s], 32000arcsec]')

    #bandpass again on the new clean data
    bc=calname(file_2_clean, "B")
    bandpass(vis=file_2_clean, spw="", minsnr=1, solnorm=F, bandtype="B", caltable=bc)
    applycal(file_2_clean, gaintable=[bc])

    #final cleaning pass on the double-split cleaned data
    file_3_clean=file_2_clean
    imgnameFinal=file_3_clean + "Final.combined" + ".img"

    clean(vis=file_3_clean, imagename=imgnameFinal, niter=5000, weighting='briggs', robust=-0.5, imsize=[512,512], cell=['250arcsec'],mode='mfs',nterms=1, spw='0:60~745', mask='circle[[17h45m00.0s, -29d00m00.0s], 32000arcsec]')

if __name__ == "__main__":
    folder = sys.argv[3]
    print (folder)
    make_image(folder,'GC.cl')
