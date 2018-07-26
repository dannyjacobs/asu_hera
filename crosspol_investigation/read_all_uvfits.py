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
globbed_files = glob.glob('/data6/HERA/data/IDR2.1/uvOCRSL_crosspol_time_split/xy_time_split_data/*.uvfits')
globed_files.sort()

#Read in the first file
uvaccum.read_uvfits(globbed_files[0])

#Create an array of zeros
zeros = np.zeros([uvaccum.Nbls,uvaccum.Nspws,uvaccum.Nfreqs,uvaccum.Npols])

#Replace the data array and the nsample array with zeros
#Careful to use correct array type
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

print uvaccum.data_array.shape
print uvaccum.nsample_array.shape
print uvaccum.flag_array.shape

#Run a check that arrays have correct length
uvaccum.check(check_extra = True)

#Initialize variable to track the number times
#This will be used to take the average at the end
ntimes = 0

#Start iterating over all of the files
for my_file in globbed_files:
   
    #Create a uv object to read in the given files
    uvin = UVData()
    uvin.read_uvfits(my_file, run_check=False, run_check_acceptability=False)

    print('Accessing' + my_file)
    
    #Unphase the data
    uvin.unphase_to_drift()

    #Reshape the data to have time in a separate dimension
    uvin.data_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)
    uvin.nsample_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)
    uvin.flag_array.shape = (uvin.Ntimes,uvin.Nbls,uvin.Nspws,uvin.Nfreqs,uvin.Npols)

    #Check if the file is completely flagged
    #If it is, move onto next file
    if np.all(uvin.flag_array):
        print('Completely flagged')
        continue

    #Keep track of the number of times as a way of tracking the data objects
    #being counted in each element
    ntimes += np.sum(uvin.Ntimes)
    
    #Create a masked array for our data array, with the flags acting as the mask
    data_array = np.ma.array(uvin.data_array,mask = uvin.flag_array)

    #Sum the data array over the time axis and add into the accum data array
    uvaccum.data_array += np.ma.sum(data_array, axis = 0)

    #Sum the nsamples array over the time axis and add into the accum object
    uvaccum.nsample_array += np.sum(uvin.nsample_array, axis = 0)

#Fill the accumulated flag array
#If 90% or more of the files contained data, keep unflagged
#If less than 90% of the files contained data, flag the element
uvaccum.flag_array = np.where(uvaccum.nsample_array/ntimes> = .9, False, True)
print uvaccum.flag_array
#Average the data using the nsamples array
time_avg = np.true_divide(uvaccum.data_array,uvaccum.nsample_array, where = uvaccum.nsample_array!=0)

#Put the average into the data array
uvaccum.data_array = time_avg

#Write out the file
print('Writing out file')
uvaccum.write_uvfits('/data6/HERA/data/IDR2.1/uvOCRSL_crosspol_time_split/xy_time_split_data/combined_files/zen.grp1.of1.xy.LST.run_7.uvOCRSL.uvfits', run_check = False, run_check_acceptability = False)

