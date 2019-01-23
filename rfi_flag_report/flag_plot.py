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
import json
import itertools as it

#define functions to make plots for a given observation, return the relevant variables
def create_flag_arrays(Data_Path):
    #This will take in a data path and output the arrays needed to plot the flags.
    #init variables
    file_flag_xx=[]
    file_flag_yy=[]
    time_mean_xx=[]
    time_mean_yy=[]
    time_mean_xx_old=[]
    time_mean_yy_old=[]
    flag_times_xx=[]
    flag_times_yy=[]
    chan_mean_xx=[]
    chan_mean_yy=[]
    chan_mean_xx_old=[]
    chan_mean_yy_old=[]
    flag_waterfall_xx=[]
    flag_waterfall_yy=[]
    xants_xx=[]
    xants_yy=[]
    SUMMARY_PATH='/lustre/aoc/projects/hera/dlewis/FullSeason_flag_summaries'
    JSON_PATH='/lustre/aoc/projects/hera/dlewis/ant_metrics_fullseason'

    #Gather flags
    #xx
    file_flag_xx=glob.glob(Data_Path + '/*.xx.*.uvO.flags.npz')
    file_flag_xx.sort()
    #yy
    file_flag_yy=glob.glob(Data_Path + '/*.yy.*.uvO.flags.npz')
    file_flag_yy.sort()

    for i,flagfile in enumerate(file_flag_xx):
        directory=os.path.split(Data_Path)[1]
        JD=flagfile[-33:-20]
        print ('Accessing: '+ JD)
        #load JSON for given JD
        jsontemp=JSON_PATH + '/' + directory +'/zen.' + JD + '.HH.uv.ant_metrics.json'
        with open(jsontemp,'r') as antjson:
            antmetrics=json.load(antjson)
        #copy into better format
        exec('ants='+antmetrics['xants']) 
        #get xants for polarization
        xants_xx_temp=np.asarray([xant for i, (xant,pol) in enumerate(ants) if pol=='x'])
        xants_xx.extend(xants_xx_temp)
#         print ('xants_xx_temp='+str(xants_xx_temp))
        numxant=len(xants_xx_temp)
#         print ('numxant='+str(numxant))
        #load summary data
        sum_data=np.load(SUMMARY_PATH + '/' + directory +'/zen.' + JD + '.xx.HH.uvO.flag_summary.npz')
        flag_times_xx.extend(sum_data['times'])
        #load flag data
        flag_data=np.load(flagfile)

        timelen=len(flag_data['waterfall'])
#         print ('timelen='+str(timelen))

        numbaseline=len(flag_data['flag_array'])/timelen
#         print ('numbaseline 1='+str(numbaseline))

        numant=(np.sqrt((8*numbaseline) +1) -1)/2
#         print ('numant='+str(numant))

        antcomb=it.combinations_with_replacement(np.linspace(1, numant,numant, endpoint=True), 2)
        noxantcomb=it.combinations_with_replacement(np.linspace(1, numant-numxant,numant-numxant, endpoint=True), 2)
        baselines=list(antcomb) #list of baselines
        goodbase=list(noxantcomb) #list of baselines not including xants
        numbase=len(baselines) #Nbls
        numgoodbase=len(goodbase) #Nbls not including xants
        numxantbase=numbase-numgoodbase #Nbls of xant baselines
#         print ('numbaseline 2='+str(numbase))
#         print ('numgoodbaselines='+str(numgoodbase))
#         print ('numxantbaselines='+str(numxantbase))

        #current shape of flag_array: (Nblts, Nspw, Nchans, Npols)

        #compute base sums first
        basearr=np.reshape(flag_data['flag_array'],(timelen, numbaseline, 1, 1024, 1)) #convert shape to (Ntimes, Nbls, Nspws, Nfreqs, Npols)
#         print basearr.shape
        basesum=np.sum(basearr, axis=1)  #sum over Nbls
#         print basesum.shape
        baseavg=(basesum-numxantbase)/(numbaseline-numxantbase) #average over Nbls minus xant baselines
#         print baseavg.shape #shape is now (Ntimes, Nspws, Nfreqs, Npols)


        #time averaging
        time_mean_temp=np.mean(baseavg,axis=(0,1,3)) #average  over Ntimes, Nspw, Npols
    #     time_temp=np.reshape(time_mean_temp,(timelen, numbaseline, 1024))
    #     timesums=np.sum(time_temp, axis=1)
    #     timeavgxant=(timesums-numxantbase)/(numbaseline-numxantbase)
#         print time_mean_temp.shape
    #     print timeavgxant.shape
        time_mean_xx.append(time_mean_temp)

        #channel averaging
        chan_mean_temp=np.mean(baseavg, axis=(1,2,3))
    #     chantemp=np.reshape(chan_mean_temp,(timelen, numbaseline))#reshape to a more flexible shape
    #     chansums=np.sum(chantemp, axis=1)
    #     chanavgxant=(chansums-numxantbase)/(numbaseline-numxantbase) #subtract flagged antennas from sum over baseline averaging
        chan_mean_xx.extend(chan_mean_temp)

        #Old version, without subtracting flagged antennas
        time_mean_xx_old.append(np.mean(flag_data['flag_array'], axis=(0,1,3)))
        chan_mean_temp_old=np.mean(flag_data['flag_array'], axis=(1,2,3))
        chantemp_old=np.reshape(chan_mean_temp_old,(timelen, numbaseline))
        chan_mean_xx_old.extend(np.mean(chantemp_old, axis=1))

    for i,flagfile in enumerate(file_flag_yy):
        directory=os.path.split(Data_Path)[1]
        JD=flagfile[-33:-20]
        print ('Accessing: '+ JD)
        #load JSON for given JD
        jsontemp=JSON_PATH + '/' + directory +'/zen.' + JD + '.HH.uv.ant_metrics.json'
        with open(jsontemp,'r') as antjson:
            antmetrics=json.load(antjson)
        #copy into better format
        exec('ants='+antmetrics['xants']) 
        #get xants for polarization
        xants_yy_temp=np.asarray([xant for i, (xant,pol) in enumerate(ants) if pol=='y'])
        xants_yy.extend(xants_yy_temp)
#         print ('xants_yy_temp'+str(xants_yy_temp))
        numxant=len(xants_yy_temp)
#         print 'numxant=' +str(numxant)
        #load summary data
        sum_data=np.load(SUMMARY_PATH + '/' + directory +'/zen.' + JD + '.yy.HH.uvO.flag_summary.npz')
        flag_times_yy.extend(sum_data['times'])
        #load flag data
        flag_data=np.load(flagfile)

        timelen=len(flag_data['waterfall'])
#         print 'timelen='+str(timelen)

        numbaseline=len(flag_data['flag_array'])/timelen
#         print 'numbaseline='+str(numbaseline)

        numant=(np.sqrt((8*numbaseline) +1) -1)/2
#         print 'numant='+str(numant)
        antcomb=it.combinations_with_replacement(np.linspace(1, numant,numant, endpoint=True), 2)
        noxantcomb=it.combinations_with_replacement(np.linspace(1, numant-numxant,numant-numxant, endpoint=True), 2)
        baselines=list(antcomb) #list of baselines
        goodbase=list(noxantcomb) #list of baselines not including xants
        numbase=len(baselines) #Nbls
        numgoodbase=len(goodbase) #Nbls not including xants
        numxantbase=numbase-numgoodbase #Nbls of xant baselines
#         print ('numbaseline 2='+str(numbase))
#         print ('numgoodbaselines='+str(numgoodbase))
#         print ('numxantbaselines='+str(numxantbase))
        #current shape of flag_array: (Nblts, Nspw, Nchans, Npols)
        #compute base sums first
        basearr=np.reshape(flag_data['flag_array'],(timelen, numbaseline, 1, 1024, 1)) #convert shape to (Ntimes, Nbls, Nspws, Nfreqs, Npols)
#         print basearr.shape
        basesum=np.sum(basearr, axis=1)  #sum over Nbls
#         print basesum.shape
        baseavg=(basesum-numxantbase)/(numbaseline-numxantbase) #average over Nbls minus xant baselines
#         print baseavg.shape #shape is now (Ntimes, Nspws, Nfreqs, Npols)
        #time averaging
        time_mean_temp=np.mean(baseavg,axis=(0,1,3)) #average  over Ntimes, Nspw, Npols
    #     time_temp=np.reshape(time_mean_temp,(timelen, numbaseline, 1024))
    #     timesums=np.sum(time_temp, axis=1)
    #     timeavgxant=(timesums-xantbaselines)/(numbaseline-xantbaselines)

#         print time_mean_temp.shape
        time_mean_yy.append(time_mean_temp)
        #channel averaging
        chan_mean_temp=np.mean(baseavg, axis=(1,2,3))
    #     chantemp=np.reshape(chan_mean_temp,(timelen, numbaseline))#reshape to a more flexible shape
    #     chansums=np.sum(chantemp, axis=1)
    #     chanavgxant=(chansums-xantbaselines)/(numbaseline-xantbaselines) #subtract flagged antennas from sum over baseline averaging
        chan_mean_yy.extend(chan_mean_temp)
        #Old version, without subtracting flagged antennas
        time_mean_yy_old.append(np.mean(flag_data['flag_array'], axis=(0,1,3)))
        chan_mean_temp_old=np.mean(flag_data['flag_array'], axis=(1,2,3))
        chantemp_old=np.reshape(chan_mean_temp_old,(timelen, numbaseline))
        chan_mean_yy_old.extend(np.mean(chantemp_old, axis=1))    
    xants_xx=np.unique(xants_xx)
    xants_yy=np.unique(xants_yy)
    timeshape=np.asarray(time_mean_xx)
#     print timeshape.shape
    time_mean_xx_old=np.mean(time_mean_xx_old, axis=0)
    time_mean_xx=np.mean(time_mean_xx, axis=0)
    time_mean_yy_old=np.mean(time_mean_yy_old, axis=0)
    time_mean_yy=np.mean(time_mean_yy, axis=0)
    return(chan_mean_xx, chan_mean_yy, time_mean_xx, time_mean_yy,flag_times_xx,flag_times_yy,xants_xx, xants_yy, chan_mean_xx_old, chan_mean_yy_old, time_mean_xx_old, time_mean_yy_old);


def save_plots(arr_xx1, arr_yy1, arr_xx2, arr_yy2, arr_xx3, arr_yy3, arr_xx4, arr_yy4,arr_xx5, arr_yy5, arr_xx6, arr_yy6, directory, Save_Path):
    plotfile=Save_Path + directory + '_plot_arrays.npz'
    #save summary arrays
    np.savez(plotfile,chan_mean_xx=arr_xx1, chan_mean_yy=arr_yy1, time_mean_xx=arr_xx2, time_mean_yy=arr_yy2, flag_times_xx=arr_xx3, flag_times_yy=arr_yy3, xants_xx=arr_xx4, xants_yy=arr_yy4, chan_mean_xx_old=arr_xx5, chan_mean_yy_old=arr_yy5, time_mean_xx_old=arr_xx6, time_mean_yy_old=arr_yy6)
    return();

def main():
    Data_Path='/lustre/aoc/projects/hera/djacobs/IDR2_flags'
    Save_Path='/lustre/aoc/projects/hera/dlewis/flagreports_xant_test/'
    #Data_Path='/data6/HERA/data/2458042'
    #Save_Path='/data6/HERA/HERA_imaging/rfi_flag_report/'
    
    #Get list of directories to run on within Data Path
    directoryList=glob.glob(Data_Path +'/2*')
    directoryList.sort()
    
    for filedir in directoryList[45:]:
        directory=os.path.split(filedir)[1]
        print('Accessing ' + directory)
        chan_mean_xx, chan_mean_yy, time_mean_xx,time_mean_yy,flag_times_xx,flag_times_yy, xants_xx, xants_yy, chan_mean_xx_old, chan_mean_yy_old, time_mean_xx_old, time_mean_yy_old=create_flag_arrays(filedir)
        #sum_chan_mean_xx, sum_chan_mean_yy, sum_time_mean_xx, sum_time_mean_yy, sum_flag_times_xx, sum_flag_times_yy=create_flag_sum_arrays(filedir)
        save_plots(chan_mean_xx, chan_mean_yy, time_mean_xx, time_mean_yy,flag_times_xx, flag_times_yy, xants_xx, xants_yy,chan_mean_xx_old, chan_mean_yy_old, time_mean_xx_old, time_mean_yy_old, directory, Save_Path)

    return;


if __name__=="__main__":
    main()
