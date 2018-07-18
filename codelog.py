#This is a recreation of the codelog used in creating images using the undergrad HERA Imaging pipeline.
#It is based on Hunter's Log, which can be found in the HERA_Imaging Google Drive.

#We start by defining the file we want to work with.
infile='zen.2458042.12552.xx.HH.uv.ms'

#If we do not have this file, create it from uvfits.
# importuvfits('zen.2458042.12552.xx.HH.uv.uvfits', infile)

#If we wish, we can inspect the MS file and visibilities.
# plotms(vis=infile, averagedata=True, avgtime='100000')

#Flag the autocorrelations
flagdata(infile, autocorr=True)

#First, we orient towards the Galactic Center.
fixvis(infile, infile, phasecenter='J2000 17h45m40s -29d00m28s')

#We need to define a source for the Galactic Center
cl.addcomponent(flux=1.0, fluxunit='Jy',shape='point',dir='J2000 17h45m40.0409s -29d0m28.118s')
cl.rename("GC.cl")
cl.close()

#use an FT to write model data into the file
ft(infile,complist='GC.cl', usescratch=True)

#make a function to create calibration file names.
def calname(m,c):return os.path.basename(m)+c+'.cal'

#Make a few filenames.
kc=calname(infile,'K')
gc=calname(infile,'G')

#Solve for the delays
#first one looks for delay errors in gains
gaincal(infile, caltable=kc, gaintype='K', solint='inf',refant='11', minsnr=1, spw='0:100~130,0:400~600')
#second one looks for frequency errors in gains
gaincal(infile, caltable=gc,gaintype='G',solint='inf',refant='11', minsnr=2,calmode='ap',gaintable=kc)

#apply this calibration to our file.
applycal(infile,gaintable=[kc, gc])

#Split our data to allow the creation of more calibration files (turn the corrected data tables into raw data tables)
split(infile, os.path.basename(infile)+'split'+'.ms',datacolumn='corrected',spw='')

#now make the first clean image
#start with init
imgname=os.path.basename(infile)+'init.img'
file_to_clean='zen.2458042.12552.xx.HH.uv.mssplit.ms'

#clean the calibrated data
clean(vis=file_to_clean,imagename=imgname,niter=500, weighting='briggs', robust=-0.5,imsize=[512,512],cell=['500arcsec'],mode='mfs',nterms=1, spw='0:150~900',mask='circle[[17h45m00.0s,-29d00m00.00s],32000arcsec]')

#show the new image:
# viewer(imagename+'.image')

#run a bandpass calibration on the first set of split data
bc=calname(file_to_clean, 'B')

bandpass(vis=file_to_clean,spw="",minsnr=1,solnorm=F,bandtype='B', caltable=bc)

applycal(file_to_clean, gaintable=[bc])

#Do another split for the same reasons
split(file_to_clean, os.path.basename(file_to_clean)+'c2.ms',datacolumn='corrected',spw='0:100~800')

#clean the new split
file_2_clean='zen.2458042.12552.xx.HH.uv.mssplit.msc2.ms'
imgname2=os.path.basename(file_2_clean)+'init.img'

clean(vis=file_2_clean, imagename=imgname2, niter=500, weighting='briggs', robust=-0.5, imsize=[512,512], cell=['500arcsec'],mode='mfs', nterms = 1, spw = '0:150~900', mask='circle[[17h45m00.0s, -29d00m00.00s ], 32000arcsec]')

#do another bandpass on this cleaned data
bc2=calname(file_2_clean, 'B')
bandpass(vis=file_2_clean, spw='', minsnr=1, solnorm=F,bandtype='B', caltable=bc2)
applycal(file_2_clean, gaintable=[bc2])

#do a final cleaning on the twice-split data
file_3_clean='zen.2458042.12552.xx.HH.uv.mssplit.msc2.ms'
imgnameFinal_redo='GC_redo.combined.img'

clean(vis = file_3_clean, imagename=imgnameFinal_redo, niter=5000, weighting = 'briggs', robust = -0.5, imsize = [512, 512], cell = ['250arcsec'], mode='mfs', nterms = 1, spw = '0:60~745', mask='circle[[17h45m00.0s, -29d00m00.00s ], 32000arcsec]')

imggal='GC_redo.combined.galcord'
imregrid(imagename=imgnameFinal_redo + '.image', output=imggal, template='GALACTIC')

#now we can view it

# viewer('GC_redo.combined.img.image')






















