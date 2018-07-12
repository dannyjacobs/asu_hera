'''

 The purpose of this code is to read an entire night of uvfits files into 
 a single file.

 To run from terminal: 
 ipython run_all_uvfits.py

'''

#Import needed packages
from pyuvdata import UVData
import numpy as np
import glob

#Create uv objects
uvaccum = UVData()

#Create a list of all the xy files
files_xy=glob.glob('/data6/HERA/data/IDR2.1/uvOCRSL_crosspol_time_split/xy_time_split_data/*.uvfits')
files_xy.sort()

#Read in the first file
uvaccum.read_uvfits(files_xy[0])

#Create an array of zeros
zeros = np.zeros([uvaccum.Nbls,uvaccum.Nspws,uvaccum.Nfreqs,uvaccum.Npols])

#Replace the data array and the nsample array with zeros
uvaccum.data_array = zeros.astype('complex')
uvaccum.nsample_array = np.zeros([uvaccum.Nbls,uvaccum.Nspws,uvaccum.Nfreqs,uvaccum.Npols])
uvaccum.flag_array = zeros.astype('bool')

#Change the number of times and correct all params that use time
uvaccum.Ntimes = 1
uvaccum.Nblts = uvaccum.Nbls * uvaccum.Ntimes
uvaccum.ant_1_array = uvaccum.ant_1_array[:uvaccum.Nbls]
uvaccum.ant_2_array = uvaccum.ant_2_array[:uvaccum.Nbls]
uvaccum.baseline_array = uvaccum.baseline_array[:uvaccum.Nbls]
uvaccum.lst_array = uvaccum.lst_array[:uvaccum.Nbls]
uvaccum.nsample_array = uvaccum.nsample_array[:uvaccum.Nbls]
uvaccum.time_array = uvaccum.time_array[:uvaccum.Nbls]
uvaccum.uvw_array = uvaccum.uvw_array[:uvaccum.Nbls]
#uvaccum.flag_array = uvaccum.flag_array[:uvaccum.Nbls] 

print uvaccum.data_array.shape
print uvaccum.nsample_array.shape
print uvaccum.flag_array.shape

#Run a check that arrays have correct length
uvaccum.check(check_extra=True)

#ntimes = 0
nitems = 0

#Start iterating over all of the files
for my_file in files_xy:
   
    #Create a uv object to read in the given files
    uvin = UVData()
    uvin.read_uvfits(my_file)

    print('Accessing'+my_file)
    
    #Unphase the data
    uvin.unphase_to_drift()

    #Reshape the data to have time in a separate dimension
    uvin.data_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)
    uvin.nsample_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)
    uvin.flag_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)


    if np.all(uvin.flag_array):
        print 'Completely flagged'
        continue

    flags = np.logical_not(uvin.flag_array)
    print np.mean(flags)

    #ntimes += np.sum(uvin.Ntimes)
    nitems += np.sum(flags,axis=0)
    
    print np.mean(nitems)

    #Add in the data to the accumulated object
    uvaccum.data_array += np.sum(uvin.data_array*flags, axis=0)
    uvaccum.nsample_array += np.sum(uvin.nsample_array, axis=0)
    uvaccum.flag_array += np.sum(np.logical_not(uvin.flag_array), axis=0,dtype='bool')
#    print uvaccum.data_array

#print uvaccum.data_array
#print uvaccum.nsample_array
#print uvaccum.flag_array
uvaccum.flag_array = np.logical_not(uvaccum.flag_array)
print uvaccum.flag_array
#print nitems
#Average the data
#time_avg = uvaccum.data_array / ntimes
time_avg = np.true_divide(uvaccum.data_array,nitems,where=nitems!=0)
#print time_avg

#Put the average into the data array
uvaccum.data_array = time_avg

#Write out the file
print('Writing out file')
uvaccum.write_uvfits('/data6/HERA/data/IDR2.1/uvOCRSL_crosspol_time_split/xy_time_split_data/combined_files/zen.grp1.of1.xy.LST.run_5.uvOCRSL.uvfits')

