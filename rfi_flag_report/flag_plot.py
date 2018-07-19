#!/usr/bin/env python

'''

This is a script intended to automatically generate a .npz containing arrays for the flag data in a given night's observations.

It works in conjunction with a .sh file and with a template Jupyter Notebook, as well as with a librarian service running on HERA servers. It is based on the HERA_Plots concept and infrastructure.

Coder: David Lewis 2018

'''

import glob
from hera_qm import xrfi as xrfi
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
import numpy as np
import numpy.ma as ma
import os
from pyuvdata import UVData
import sys

#define functions to make plots for a given observation, return the relevant variables
def create_flag_arrays(Data_Path):
    #This will take in a data path and output the four arrays needed to plot the flags.
    #init variables
    file_flag_xx=[]
    file_flag_yy=[]
    time_mean_xx=[]
    time_mean_yy=[]
    flag_times_xx=[]
    flag_times_yy=[]
    chan_mean_xx=[]
    chan_mean_yy=[]
    flag_waterfall_xx=[]
    flag_waterfall_yy=[]
    #Gather flags
    #xx
    file_flag_xx=glob.glob(Data_Path + '/*.xx.*.uvO.flags.npz')
    file_flag_xx.sort()
    #yy
    file_flag_yy=glob.glob(Data_Path + '/*.yy.*.uvO.flags.npz')
    file_flag_yy.sort()
    
    for i,flagfile in enumerate(file_flag_xx):
        flag_data=np.load(flagfile)
        timelen=len(flag_data['waterfall'])
        time_mean_xx.append(np.mean(flag_data['flag_array'],axis=(0,1,3)))
        chan_mean_temp=np.mean(flag_data['flag_array'], axis=(1,2,3))
        numbaseline=len(chan_mean_temp)/timelen
        chantemp=np.reshape(chan_mean_temp,(timelen, numbaseline))
        chan_mean_xx.extend(np.mean(chantemp, axis=1))
    
    for i,flagfile in enumerate(file_flag_yy):
        flag_data=np.load(flagfile)
        timelen=len(flag_data['waterfall'])
        time_mean_yy.append(np.mean(flag_data['flag_array'],axis=(0,1,3)))
        chan_mean_temp=np.mean(flag_data['flag_array'], axis=(1,2,3))
        numbaseline=len(chan_mean_temp)/timelen
        chantemp=np.reshape(chan_mean_temp,(timelen, numbaseline))
        chan_mean_yy.extend(np.mean(chantemp, axis=1))
    
    time_mean_xx=np.mean(time_mean_xx, axis=0)
    time_mean_yy=np.mean(time_mean_yy, axis=0)
    return(chan_mean_xx, chan_mean_yy, time_mean_xx, time_mean_yy);


def create_flag_sum_arrays(Data_Path):
    #This will take in flag summary files and output the arrays needed to create plots and waterfalls of the flags.
    #This is no longer used in the main file, but the function remains here for posterity.
    #init variables
    file_flag_summary_xx=[]
    file_flag_summary_yy=[]
    file_flags=[]
    sum_chan_mean_xx=[]
    sum_chan_mean_yy=[]
    sum_flag_times_xx=[]
    sum_flag_times_yy=[]
    sum_time_mean_xx=[]
    sum_time_mean_yy=[]
    sum_flag_waterfall_xx=[]
    sum_flag_waterfall_yy=[]
    
    #Gather flag summaries
    #start with xx
    file_flag_summary_xx=glob.glob(Data_Path + '/*.xx.*.flag_summary.npz')
    file_flag_summary_xx.sort()
    #Continue with yy
    file_flag_summary_yy=glob.glob(Data_Path + '/*.yy.*.flag_summary.npz')
    file_flag_summary_yy.sort()
    
    for i, sumfile in enumerate(file_flag_summary_xx):
        flag_sum_data=np.load(sumfile)
        sum_chan_mean_xx.extend(flag_sum_data['fmean'].squeeze())
        sum_flag_times_xx.extend(flag_sum_data['times'])
        sum_time_mean_xx.append(flag_sum_data['tmean'].squeeze())

    for i, sumfile in enumerate(file_flag_summary_yy):
        flag_sum_data=np.load(sumfile)
        sum_chan_mean_yy.extend(flag_sum_data['fmean'].squeeze())
        sum_flag_times_yy.extend(flag_sum_data['times'])
        sum_time_mean_yy.append(flag_sum_data['tmean'].squeeze())

    sum_time_mean_xx=np.average(sum_time_mean_xx,axis=0)
    sum_time_mean_yy=np.average(sum_time_mean_yy,axis=0)

    return(sum_chan_mean_xx, sum_chan_mean_yy, sum_time_mean_xx, sum_time_mean_yy, sum_flag_times_xx, sum_flag_times_yy);

def save_plots(arr_xx1, arr_yy1, arr_xx2, arr_yy2, directory, Save_Path):
    plotfile=Save_Path + directory + '_plot_arrays.npz'
    #np.savez(plotfile,chan_mean_xx=arr_xx1, chan_mean_yy=arr_yy1, time_mean_xx=arr_xx2, time_mean_yy=arr_yy2, sum_chan_mean_xx=arr_xx3, sum_chan_mean_yy=arr_yy3, sum_time_mean_xx=arr_xx4, sum_time_mean_yy=arr_yy4, sum_flag_times_xx=arr_xx5, sum_flag_times_yy=arr_yy5)
    #Change to only make file based on flag array, not summaries
    np.savez(plotfile,chan_mean_xx=arr_xx1, chan_mean_yy=arr_yy1, time_mean_xx=arr_xx2, time_mean_yy=arr_yy2)
    return();

def main():
    Data_Path='/lustre/aoc/projects/hera/djacobs/IDR2_flags'
    Save_Path='/lustre/aoc/projects/hera/dlewis/flagreports_full/'
    #Data_Path='/data6/HERA/data/2458042'
    #Save_Path='/data6/HERA/HERA_imaging/rfi_flag_report/'
    
    #Get list of directories to run on within Data Path
    directoryList=glob.glob(Data_Path +'/2*')
    directoryList.sort()
    
    for filedir in directoryList[-30:]:
        directory=os.path.split(filedir)[1]
        print('Accessing ' + directory)
	chan_mean_xx, chan_mean_yy, time_mean_xx,time_mean_yy=create_flag_arrays(filedir)
        #sum_chan_mean_xx, sum_chan_mean_yy, sum_time_mean_xx, sum_time_mean_yy, sum_flag_times_xx, sum_flag_times_yy=create_flag_sum_arrays(filedir)
        save_plots(chan_mean_xx, chan_mean_yy, time_mean_xx, time_mean_yy, directory, Save_Path)

    return;


if __name__=="__main__":
    main()
