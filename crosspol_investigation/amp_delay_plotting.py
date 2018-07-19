'''
This file contains the functions used to find the maximum amplitude of delay 
transform plots, the corresponding delay times, as well as the functions to 
plot this information.

'''
#Import packages
from pyuvdata import UVData
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
import os
import sys

#Define constants
diagonals = np.linspace(0,130)
zero_line = np.linspace(0,0)
cable = np.linspace(150,150) 

#Create an array of antennas we want to flag
flagged_antennas = np.array([0,2,26,50,98,136])


def check_antnum(antnum,ants):
    '''
    This function checks to see if the entered antenna number matches with a 
    known antenna number

    Parameters
    ----------
    antnum : int
         The number entered that needs to be checked
    ants : ndarray
         The array of antenna numbers to be checked against 

    Returns
    -------
    antnum : int
         The original number entered by the user if it was valid
    OR
    new_ant : int
         A valid antenna number entered by the user after the first entry was 
         rejected

    '''

    #Check if the number entered matches with a flagged antenna
    if np.any(antnum==flagged_antennas):
	#If the antenna entered is flagged, an error message will be printed
	print 'The antenna entered has been flagged.'
	#Prompt the user to enter a new number
	new_ant = input('Which antenna would you like to look at? Enter here: ')
	new_ant = int(new_ant)
	#Run the check on the new entry
	new_ant = check_antnum(new_ant,ants)
	#Return the valid antenna number
	return int(new_ant)
    #Check if the number entered matches with an unflagged antenna
    elif np.any(antnum==ants):
        #If the number matched an unflagged antenna, it is printed and returned
        print(antnum)
        return antnum
    else:
        #If the number did not match any antenna, an error message is printed
        print 'The number entered does not correspond to a known antenna.'
        #Prompt the user to enter a new number
        new_ant = input("Which antenna would you like to look at? Enter here: ")
        new_ant = int(new_ant)
        #Run the check on the new entry
        new_ant = check_antnum(new_ant,ants)
        #Return the valid antenna number
        return int(new_ant)



def find_blin_length(index,antpos,ants):
    '''
    The purpose of this function is to read in the selected antenna and
    calculate the length of each baseline
    
    Parameters
    ----------
    index : int
        The index points to which antenna has been selected by the user
    antpos : ndarray
        The array of positions for each antenna
    ants : ndarray
        The array of antenna numbers
        
    Returns
    -------
    blin_length : ndarray
        This array holds the corresponding distance between each antenna pair
    
    '''
    
    #Create an array which holds the physical distance between each antenna in 
    #meters 
    #Initialize it to the desired length and fill with zeros. 
    blin_length = np.zeros((52,1))
    
    #Step through each antenna pair with the entered antenna
    for aa,ant in enumerate(ants):
        #Find the horizontal distance between the two antennas
        x = antpos[index,0] - antpos[aa,0]
        #Find the vertical distance between the two antennas
        y = antpos[index,1] - antpos[aa,1]
        #Find the hypotenus of the triangle, which is the total distance between
        #the two antennas
        diag = np.sqrt(x**2 + y**2)
        #Place this value into the array
        blin_length[aa] = diag
    
    #Return the array of baselines
    return(blin_length)



def make_max_arrays(uv,keep_flags=False):
    '''
    The purpose of this function is to read in all antenna pairs and produce an
    array of the maximum amplitudes of the delay transform and an array of the 
    corresponding delay times. 

    Parameters 
    ----------
    uv : uv data object
        Name of the uv object being used
    keep_flags : bool, optional
        If this is set to True, a zero will be inserted into the amplitude array
        when a flagged antenna is encountered. This acts as a placeholder so 
        that when the antenna array positions are plotted, all of the antenna 
        are present, including the flagged antenna. 
        If the default value is passed, then the function will skip flagged 
        antenna and no entry will be placed in the array element.
    
    Returns
    -------
    max_amp, delays : ndarrays
        The first array holds the maximum amplitudes. If keep_flags is True, the
        array will have empty elements to correct the shape and size of the 
        array. 
        The second array holds the corresponding delay times. If keep_flags is
	True, the array will have empty elements to correct the shape and size 
	of the array. 
    '''
    
    #Create the arrays to be returned
    max_amp=[]
    delays=[]
    
    #Loop through each antenna pair
    for i,ant1 in enumerate(uv.ant_1_array):
        #Get the second antenna number using the index number
        ant2 = uv.ant_2_array[i]
        
        #Flag out dead antennas
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #If keep_flags is set to False, the function continues
        if np.any(ant1==flagged_antennas) and keep_flags:
            max_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant1==flagged_antennas):
            continue

        if np.any(ant2==flagged_antennas) and keep_flags:
            max_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant2==flagged_antennas):
            continue
            
        # Check if the antenna numbers are equal
        #If they are, the function will continue
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #'''
        if ant1==ant2 and keep_flags:
            max_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif ant1==ant2:
            continue
        #'''
        
        # Create an array to hold the data for the given antenna pair
        spectrum=uv.data_array[i,0,:,0]
        # Take a Fourier transform along the time axis
        vis_avg_delay = np.fft.fftshift(np.fft.fft(spectrum))
        #Find the frequency width of a channel in GHz
        freq_width = np.diff(uv.freq_array[0,:])[0]
        #Convert frequencies to delays and convert to ns
        con_delays = np.fft.fftshift(np.fft.fftfreq(uv.Nfreqs,freq_width))*1e9
        # Find the maximum amplitude and put into a variable
        #This is the absolute maximum of the graph, no matter how many peaks are
	#present
        max_peak = np.max(np.abs(vis_avg_delay))
        #If the max peak is zero, meaning there is no peak, the corresponding 
	#delay is set to zero. This helps to avoid errors and correct the color
        if max_peak==0:
            corr_delay = 0
        #If there is an peak present, the corresponding delay time is found
        else: 
            #Find the corresponding delay
            corr_delay = con_delays[np.argwhere(np.abs(vis_avg_delay)==max_peak)]
        # Append the maximum amplitude array with a list of the antenna pair 
	#and the peak
        max_amp.append([ant1,ant2,max_peak])
        #Append the delay array with a list of the antenna pair and the delay
        delays.append([ant1,ant2,corr_delay])

    #Convert to numpy arrays
    max_amp = np.array(max_amp)
    delays = np.array(delays)
    
    #Return the created arrays
    return max_amp, delays;



def make_matrix_array(amp_array,delay_array,antnum=None,index=False):
    '''
    The purpose of this function is to correctly fill the arrays that will be 
    used to plot the matrices. 
    
    Parameters
    ----------
    amp_array : ndarray
        The array holding the amplitudes
    delay_array : ndarray
        The array holding the delay times
    antnum : int, optional
        The antenna number of a specific antenna to check for. 
        Default is none. 
    index : bool, optional
        If this is set to True, the index number for the entered antenna number 
	will be returned as well. 
        
    Returns
    -------
    amp_matrix,delay_matrix : ndarrays
        The first array holds the amplitudes correctly shaped to produce the 
	matrix. 
        The second array hold the delays correctly shaped to produce the matrix
    OR
    amp_matrix,delay_matrix,indexnum,dindexnum : ndarrays, ints
        The first array holds the amplitudes correctly shaped to produce the 
	matrix. 
        The second array hold the delays correctly shaped to produce the matrix
        indexnum is the integer index number of the amplitude matrix for the 
	entered antenna. This is only returned if index is set to True.
        dindexnum is the integer index number of the delay matrix for the 
	entered antenna. This is only returned if index is set to True.
    
    '''
    
    #Get a list of all of the antennas used and sort them
    antennas = list(set(amp_array[:,0]))
    antennas.sort()
    
    #Find the number of antennas
    nants_peak = len(antennas)
    
    #Create arrays to hold the formatted matrices
    amp_matrix = np.zeros((nants_peak,nants_peak))
    delay_matrix = np.zeros((nants_peak,nants_peak))
    
    #Fill the amplitude matrix array by stepping through the array
    for ant1,ant2,peak in amp_array:
        #Get the coordinates for the current antenna pair
        i,j = np.argwhere(antennas==ant1),np.argwhere(antennas==ant2)
        #Check if index was set to True
        if index:
            #If one of the current antennas is the antenna entered by the user,
	    #then the amplitude value is placed into the correct element
            #The index of the selected antenna is also placed in the specified
	    #variable
            if ant1==antnum:
                amp_matrix[i,j] = peak
                indexnum = np.argwhere(antennas==ant1)
            elif ant2==antnum:
                amp_matrix[j,i] = peak
                indexnum = np.argwhere(antennas==ant2)
            #If neither of the antennas match the entered antenna, a zero is 
	    #placed into the corresponding array element
            else:
                amp_matrix[i,j] = 0
        #If index was not set to true, we check the coordinates and format so 
	#that the larger coordinate is entered second. 
	#This makes the matrix look nicer
        elif j<i:
            amp_matrix[j,i] = peak
        else:
            amp_matrix[i,j] = peak
    
    #Now we fill the delay matrix array
    for ant1,ant2,delay in delay_array:
        #Get the coordinate
        i,j = np.argwhere(antennas==ant1),np.argwhere(antennas==ant2)
        #Check if index was set to True
        if index:
            #If one of the current antennas is the antenna entered by the user,
	    #then the delay time is placed into the correct element. The index 
	    #of the selected antenna is also placed in the specified variable
            if ant1==antnum:
                delay_matrix[i,j] = delay
                dindexnum = np.argwhere(antennas==ant1)
            elif ant2==antnum:
                delay_matrix[j,i] = delay
                dindexnum = np.argwhere(antennas==ant2)
            #If neither of the antennas match the entered antenna, a zero is 
	    #placed into the corresponding array element
            else:
                delay_matrix[i,j] = 0
        #If index was not set to true, we check the coordinates and format so 
	#that the larger coordinate is entered second.
        #This makes the matrix look nicer
        elif j<i:
            delay_matrix[j,i] = delay
        else:
            delay_matrix[i,j] = delay
    
    #If index was set to True, return the two arrays and the two index values
    if index:
        return amp_matrix, delay_matrix, indexnum, dindexnum;
    #If index was set to False, only return the two arrays
    else:
        return amp_matrix, delay_matrix;



def plot_matrix_array(amp_array,amp_matrix,delay_matrix,vmin=0,vmax=1000,title=None):
    '''
    The purpose of this function is to plot the matrix arrays for both amplitude
    and delay
    
    Parameters
    ----------
    amp_array : ndarray
        The amplitude array that is used to get the antenna numbers to be used 
	for tick marks on the graphs
    amp_matrix : ndarray
        The array of amplitudes which will be plotted as a matrix
    delay_matrix : ndarray
        The array of delays which will be plotted as a matrix
    vmin : int, optional
        The minimum value for the delay color scale. Default is 0.
    vmin : int, optional
        The maximum value for the delay color scale. Default is 1000.
    title : str, optional
        The name of the plot. Default is None. 
    
    '''
    
    #Get a list of the antennas to use for tick marks
    antennas = list(set(amp_array[:,0]))
    antennas.sort()

    #Open a figure
    fig = plt.figure(figsize=(12,5))

    #Plot the amplitudes
    #vmin and vmax have been set manually to a range that is usually readable
    ax = fig.add_subplot(121)
    cax = ax.matshow(amp_matrix,norm=SymLogNorm(vmin=200,vmax=10000,linthresh=.1))
    fig.colorbar(cax,label='Amplitude',fraction=0.046, pad=0.04)
    plt.xticks(np.arange(45), antennas, rotation='vertical', fontsize=8)
    plt.yticks(np.arange(45), antennas, fontsize=8)
    #Print the title with the entered name
    plt.title(title,pad=20)
    #plt.grid()

    #Plot the delays
    #vmin and vmax are entered by the user
    ax2 = fig.add_subplot(122)
    cax2 = ax2.matshow(np.abs(delay_matrix),norm=SymLogNorm(vmin=vmin,vmax=vmax,linthresh=.1))
    fig.colorbar(cax2,label='Delay (ns)',fraction=0.046, pad=0.04)
    plt.xticks(np.arange(45), antennas, rotation='vertical', fontsize=8)
    plt.yticks(np.arange(45), antennas, fontsize=8)
    plt.title('Delay (ns)',pad=20)
    #plt.grid()

    plt.tight_layout()
    plt.show()



def plot_position_array(amp_array,delay_array,index,dindex,uv,antnum=None,vmin=0,vmax=1000,title1=None,title2=None):
    '''
    The purpose of this function is to plot the antenna array in their physical
    locations, with one plot using the amplitude as the color scale and the 
    other plot using the delay times as the color scale. 
    
    Parameters
    ----------
    amp_array : ndarray
        The amplitude array that is used as color scale for the first plot
    delay_array : ndarray
        The delay array that is used as color scale for the first plot
    index : int
        The index number for the amplitude array
    dindex : int
        The index number for the delay array
    uv : uv object
	The uv object to be used to find the antenna and antenna positions.
    antnum : int, optional
	The user entered antenna number. Default is none.
    vmin : int, optional
        The minimum value for the delay color scale. Default is 0
    vmin : int, optional
        The maximum value for the delay color scale. Default is 1000
    title1 : str, optional
        The name of the first plot. Default is blank
    title2 : str, optional
        The name of the second plot. Default is blank
    
    '''

    #Get the antenna positions and antenna numbers
    antpos, ants = uv.get_ENU_antpos()
    
    #Open the figure
    plt.figure(figsize=(12,5))
    
    #Create a subplot
    #The first array of antennas plotted with amplitude as color
    plt.subplot(121)

    #This line of code isn't necessary, but it helps to better format the plot
    plt.scatter(antpos[:,0],antpos[:,1],marker='.',s=3000,color='w')

    #Now we step through each antenna and plot it with the amplitude acting as
    #the color scale
    for aa in range(52):
        #Get the amplitude value for the current antenna pair
        color = amp_array[index,aa]
        #Convert into integer
        color = int(color)
        #Plot the antennas with the corresponding colors
        #vmin and vmax are set manually to a range that is usually readable
        im=plt.scatter(antpos[aa,0],antpos[aa,1],marker='.',s=3000,c=color,norm=SymLogNorm(vmin=1,vmax=2000,linthresh=.1))
    #Print the antetnna numbers
    for aa,ant in enumerate(ants):
        if ant==antnum: plt.scatter(antpos[aa,0],antpos[aa,1],marker='.',color='black',s=3000)
        plt.text(antpos[aa,0],antpos[aa,1],ants[aa],color='w',va='center',ha='center')
    #Print the labels and color bar
    plt.xlabel('X-position (m)')
    plt.ylabel('Y-position (m)')
    plt.title(title1)
    plt.axis('equal')
    plt.colorbar(im, label='Amplitude')

    #Plot the array of antennas with color representing delay time
    plt.subplot(122)

    #Again, this line isn't strictly necessary, but it helps to better format 
    #the graph
    plt.scatter(antpos[:,0],antpos[:,1],marker='.',color='w',s=3000)

    #Now we step through each antenna and plot it with delay as color
    for aa in range(52):
        #Get the delay value for the current antenna pair
        dcolor = delay_array[dindex,aa]
        #Convert into integer
        dcolor = int(dcolor)
        #To help with readability, we take the absolute value of the delay time
        dcolor = np.abs(dcolor)
        #Plot the antennas with the corresponding colors
        #vmin and vmax are set by the user
        dim=plt.scatter(antpos[aa,0],antpos[aa,1],marker='.',s=3000,c=dcolor,norm=SymLogNorm(vmin=vmin,vmax=vmax,linthresh=.1))
    #Print the antenna numbers
    for aa,ant in enumerate(ants):
        if ant==antnum: plt.scatter(antpos[aa,0],antpos[aa,1],marker='.',color='black',s=3000)
        plt.text(antpos[aa,0],antpos[aa,1],ants[aa],color='w',va='center',ha='center')

    #Print the labels and colorbar
    plt.xlabel('X-position (m)')
    plt.ylabel('Y-position (m)')
    plt.title(title2)
    plt.axis('equal')
    plt.colorbar(dim, label='Amplitude')

    plt.tight_layout()
    plt.show()



def plot_delay_position(amp_1,delay_dis_1,amp_2,delay_dis_2,index1,index2,uv,antnum=None,title1=None,title2=None):
    '''
    The purpose of this function is to plot the antenna array based on the 
    distance given by the delay time
    
    Parameters
    ----------
    amp_1 : ndarray
        The array of amplitudes for the first plot
    delay_dis_1 : ndarray
        The array of delays in meters corresponding to the first amplitude array
    amp_2 : ndarray
        The array of amplitudes for the second plot
    delay_dis_2 : ndarray
        The array of delays in meters which correspond to the second amplitude 
        array
    uv : uv object
	The uv object used to find the antenna positions and antenna numbers.
    index1 : int
        The index for the first plot
    index2 : int
        The index for the second plot
    antnum : int, optional
	The entered antenna number. Default is None. 
    title1 : str, optional
        The name of the first plot. Default is blank
    title2 : str, optional
        The name of the second plot. Default is blank
    
    '''
    
    #Get the antenna positions and list of antenna numbers
    antpos, ants = uv.get_ENU_antpos()

    #Call the function to find the distance between antennas
    blin_length = find_blin_length(index1,antpos,ants)

    #Open the figure
    plt.figure(figsize=(12,5))

    #Plot the array of antennas in the first plot with the amplitude acting as
    #the color scale
    plt.subplot(121)
    for aa,ant in enumerate(ants):
        #Get the amplitude value for the current antenna pair
        color = amp_1[index1,aa]
        #If the current antenna is the entered antenna we are focusing on, print
	#in black and center at 0,0
        if ant==antnum: plt.scatter(0,0,marker='.',color='black',s=2000)
        #Skip flagged antennas
        elif np.any(ant==flagged_antennas): continue
        #Now we plot the remaining antennas
        #The x coordinate corresponds to the physical distance separating the 
	#antenna from the focus antenna
        #The y coordinate corresponds to the delay distance found
        #vmin and vmax are set manually to a range that is usually readable
        else: im=plt.scatter(blin_length[aa,0],delay_dis_1[index1,aa],marker='.',s=2000,c=color,norm=SymLogNorm(vmin=10,vmax=5000,linthresh=.1))
    
    #Print the antetnna numbers
    for aa,ant in enumerate(ants):
        #If the current antenna is the focus antenna, manually print number at 
	#0,0
        if ant==antnum: 
            plt.text(0,0,ants[aa],color='w',va='center',ha='center')
        #Skip flagged antennas
        elif np.any(ant==flagged_antennas): continue
        #Print the remaining antenna numbers
        else: plt.text(blin_length[aa,0],delay_dis_1[index1,aa],ants[aa],color='w',va='center',ha='center')
    #Plot lines on the diagonals and at zero
    plt.plot(diagonals,-diagonals)
    plt.plot(diagonals,diagonals)
    plt.plot(diagonals,zero_line)
    #Print labels and color bar
    plt.xlabel('Physical Distance (m)')
    plt.ylabel('Delay distance (m)')
    plt.title(title1)
    plt.colorbar(im, label='Amplitude')

    plt.subplot(122)
    #Plot the array of antennas for the second plot
    for aa,ant in enumerate(ants):
        #Get the amplitude value for the current antenna pair
        color = amp_2[index2,aa]
        #If the current antenna is the entered antenna we are focusing on, print
	#in black and center at 0,0
        if ant==antnum: plt.scatter(0,0,marker='.',color='black',s=2000)
        #Skip flagged antennas
        elif np.any(ant==flagged_antennas): continue
        #Now we plot the remaining antennas with the color representing the
	#amplitude
        #The x coordinate corresponds to the physical distance separating the 
	#antenna from the focus antenna
        #The y coordinate corresponds to the delay distance found
        #vmin and vmax are set manually to a rangle that is usually readable
        else: indim=plt.scatter(blin_length[aa,0],delay_dis_2[index2,aa],marker='.',s=2000,c=color,norm=SymLogNorm(vmin=10,vmax=5000,linthresh=.1))
   
    #Print the antetnna numbers
    for aa,ant in enumerate(ants):
        #If the current antenna is the focus antenna, manually print number at
	#0,0
        if ant==antnum: plt.text(0,0,ants[aa],color='w',va='center',ha='center')
        #Skip flagged antennas
        elif np.any(ant==flagged_antennas): continue
        #Print the remaining antenna numbers
        else: plt.text(blin_length[aa,0],delay_dis_2[index2,aa],ants[aa],color='w',va='center',ha='center')
    #Plot lines on the diagonal and at zero
    plt.plot(diagonals,-diagonals)
    plt.plot(diagonals,diagonals)
    plt.plot(diagonals,zero_line)
    #Print labels
    plt.xlabel('Physical Distance (m)')
    plt.ylabel('Delay distance (m)')
    plt.title(title2)
    plt.colorbar(indim, label='Amplitude')

    plt.tight_layout()
    plt.show()



def make_blin_depd_arrays(uv,keep_flags=False):
    '''
    The purpose of this function is to read in all antenna pairs and produce an
    array of the maximum amplitudes and an array of the corresponding delay. 

    Parameters 
    ----------
    uv : uv data object
        Name of the uv object being used
    keep_flags : bool, optional
        If this is set to True, a zero will be inserted into the amplitude array
        If the default value is passed, then the function will continue and 
	nothing will be placed into the array.
    
    Returns
    -------
    max_amp, delays : ndarrays
        The first array holds the maximum amplitudes. If keep_flags is True, the
	array will have empty elements to correct the shape and size of the
	array. 
        The second array holds the corresponding delay times. If keep_flags is 
        True, the array will have empty elements to correct the shape and size 
	of the array. 
    '''
    
    #Create the arrays to be returned
    blin_amp=[]
    delays=[]
    
    #Define constants for the beginning element that is within baseline 
    #depenedence and the end element
    blin_start = 471
    blin_end = 554
    
    for i,ant1 in enumerate(uv.ant_1_array):
        #Get the second antenna number using the index number
        ant2 = uv.ant_2_array[i]
        
        #Flag out dead antennas
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #If keep_flags is set to False, the function continues
        if np.any(ant1==flagged_antennas) and keep_flags:
            blin_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant1==flagged_antennas):
            continue

        if np.any(ant2==flagged_antennas) and keep_flags:
            blin_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant2==flagged_antennas):
            continue
            
        # Check if the antenna numbers are equal
        #If they are, the function will continue
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #'''
        if ant1==ant2 and keep_flags:
            blin_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif ant1==ant2:
            continue
        #'''
        
        # Create an array to hold the night's data
        spectrum=uv.data_array[i,0,:,0]
        # Fourier transform along the time axis
        vis_avg_delay = np.fft.fftshift(np.fft.fft(spectrum))
        #Find the frequency width of a channel in GHz
        freq_width = np.diff(uv.freq_array[0,:])[0]
        #Convert frequencies to delays and convert to ns
        con_delays = np.fft.fftshift(np.fft.fftfreq(uv.Nfreqs,freq_width))*1e9
        # Find the maximum amplitude and put into a variable
        blin_peak = np.max(np.abs(vis_avg_delay[blin_start:blin_end]))
	#If the peak is zero, meaning there is no peak, the delay is set to zero
        if blin_peak==0:
            blin_delay = 0
        else: 
            #Find the corresponding delay
            blin_delay = con_delays[np.argwhere(np.abs(vis_avg_delay)==blin_peak)]
        # Append the maximum amplitude array with a list of the antenna pair and
	#the peak
        blin_amp.append([ant1,ant2,blin_peak])
        #Append the delay array with a list of the antenna pair and the delay
        delays.append([ant1,ant2,blin_delay])

    #Convert to numpy arrays
    blin_amp = np.array(blin_amp)
    delays = np.array(delays)
    
    #Return the created arrays
    return blin_amp, delays;



def make_blin_ind_arrays(uv,keep_flags=False):
    '''
    The purpose of this function is to read in all antenna pairs and produce an
    array of the maximum amplitudes and an array of the corresponding delays. 

    Parameters 
    ----------
    uv : uv data object
        Name of the uv object being used
    keep_flags : bool, optional
        If this is set to True, a zero will be inserted into the amplitude array
        If the default value is passed, then the function will continue and 
	nothing will be placed into the array.
    
    Returns
    -------
    max_amp, delays : ndarrays
        The first array holds the maximum amplitudes. If keep_flags is True, the
	array will have empty elements to correct the shape and size. 
        The second array holds the corresponding delay times. If keep_flags is 
        True, the array will have empty elements to correct the shape and size. 
    '''
    
    #Create the arrays to be returned
    ind_amp=[]
    delays=[]
    
    #Define constants for the beginning element that is within baseline 
    #depenedence and the end element
    blin_start = 471
    blin_end = 554
    
    for i,ant1 in enumerate(uv.ant_1_array):
        #Get the second antenna number using the index number
        ant2 = uv.ant_2_array[i]
        
        #Flag out dead antennas
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #If keep_flags is set to False, the function continues
        if np.any(ant1==flagged_antennas) and keep_flags:
            ind_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant1==flagged_antennas):
            continue

        if np.any(ant2==flagged_antennas) and keep_flags:
            ind_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif np.any(ant2==flagged_antennas):
            continue
            
        # Check if the antenna numbers are equal
        #If they are, the function will continue
        #If keep_flags is set to True, a zero entry will be added to the arrays
        #'''
        if ant1==ant2 and keep_flags:
            ind_amp.append([ant1,ant2,0])
            delays.append([ant1,ant2,0])
            continue
        elif ant1==ant2:
            continue
        #'''
        
        # Create an array to hold the night's data
        spectrum=uv.data_array[i,0,:,0]
        # Fourier transform along the time axis
        vis_avg_delay = np.fft.fftshift(np.fft.fft(spectrum))
        #Find the frequency width of a channel in GHz
        freq_width = np.diff(uv.freq_array[0,:])[0]
        #Convert frequencies to delays and convert to ns
        con_delays = np.fft.fftshift(np.fft.fftfreq(uv.Nfreqs,freq_width))*1e9
        #Find the maximum peaks below the baseline dependance and above
        below_blin = np.max(np.abs(vis_avg_delay[:blin_start]))
        above_blin = np.max(np.abs(vis_avg_delay[blin_end:]))
	#Find which value is larger and set the peak element equal to it
        if below_blin >= above_blin:
            ind_peak = below_blin
        else: ind_peak = above_blin

	#If the peak is zero, meaning there is no peak, the delay is set to zero
        if ind_peak==0:
            ind_delay = 0
        else: 
            #Find the corresponding delay
            ind_delay = con_delays[np.argwhere(np.abs(vis_avg_delay)==ind_peak)]
        # Append the maximum amplitude array with a list of the antenna pair and
	#the peak
        ind_amp.append([ant1,ant2,ind_peak])
        #Append the delay array with a list of the antenna pair and the time
        delays.append([ant1,ant2,ind_delay])

    #Convert to numpy arrays
    ind_amp = np.array(ind_amp)
    delays = np.array(delays)
    
    #Return the created arrays
    return ind_amp, delays;


