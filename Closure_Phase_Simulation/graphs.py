
# coding: utf-8

# In[ ]:


from astropy.io import fits
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
from astropy.wcs import WCS
from HERA_calibration_sources import add_fluxes

plt.rc('font', family='serif')
plt.rc('xtick', labelsize='small')
plt.rc('ytick', labelsize='small')


# In[ ]:


files = np.sort(glob('/home/kalbal/data/IDR2-1_run_3.1_imgs/*.fits'))
HDUS = []
files = files
for f in files:
    HDUS.append(fits.open(f))
# In[ ]:
tb = add_fluxes(RA_range=('00:00:00','13:00:00'),dec_range=20, min_flux=10)
tb
# In[ ]:
plot_data = {v['Name of Center']: {'RA_diff': [], 'Flux': [], 'time': [],'Pixel_x': [],'Pixel_y': []} for _,v in tb.iterrows()}
source_info = {v['Name of Center']: {'RA': v['RA'], 'DEC': v['Dec'],
        'Total_Flux': v['Total flux in region']}
         for _,v in tb.iterrows()}


# In[ ]:


err = 3

f_count = len(files)
t = 0.0

c_prev = 0

for HDU,f in zip(HDUS,files):
    print ('Processing: ', f)
    # Read in file information
    fits_info = HDU[0].header
    ax1        = fits_info['NAXIS1']
    ax2        = fits_info['NAXIS2']
    units      = fits_info['BUNIT']
    c_ra       = fits_info['OBSRA']
    c_dec      = fits_info['OBSDEC']
    pix_size   = fits_info['CDELT2']
    c_pix1     = fits_info['CRPIX1']
    c_pix2     = fits_info['CRPIX2']

    data = HDU[0].data
    data = np.flip(data[0][0],axis=0)

    w = WCS(f)
    l_bound = w.all_pix2world(c_pix1,0,0,0,0)[0]
    r_bound = w.all_pix2world(c_pix1,ax2,0,0,0)[0]

    t += 1.0

    for _,src in tb.iterrows():
        # Convert a position to pixel values
        i,j = w.all_world2pix(src['RA'],src['Dec'],0,0,0)[:2]
        try:
            i = int(i)
            j = int(ax2-j)
        except:
            pass
        if (ax1-err > i > err) and (ax2-err > j > err):
            plot_data[src['Name of Center']]['Flux'].append(np.abs(data[j-err:j+err,i-err:i+err].max()))
            #plot_data[src['Name of Center']]['Flux'].append(np.abs(data[j-err:j+err,i-err:i+err].max()))
            ra_diff = c_ra-src['RA']
            # Correct for the difference in c_ra error
            if ra_diff > 30:
                ra_diff -= 360
            if ra_diff < -30:
                ra_diff += 360

            t = c_ra

            if c_ra-c_prev < -30:
                t = c_ra+360
            plot_data[src['Name of Center']]['RA_diff'].append(ra_diff)
            plot_data[src['Name of Center']]['time'].append(t)
            plot_data[src['Name of Center']]['Pixel_x'].append(j)
            plot_data[src['Name of Center']]['Pixel_y'].append(i)
        c_prev = c_ra
# In[ ]:
for k,v in plot_data.iteritems():
    print (len(v['Flux']))
# In[ ]:
cleaned_set = {k: v for k,v in plot_data.iteritems() if len(v['Flux']) >= 74}
len(cleaned_set)
# In[]:
plt.figure(figsize=(20,10))
for key,item in cleaned_set.items():
    LST = np.array(item['time'])*12/180
    flux = np.array(item['Flux'])
    plt.xlabel(r'Time')
    plt.ylabel('Flux')
    plt.plot(LST,flux,label=key)
    plt.title('Flux vs Time')
plt.legend()
plt.show()
