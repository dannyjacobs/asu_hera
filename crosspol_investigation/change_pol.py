'''

To run in terminal:
casa -c change_pol.py <measurement sets>

'''

#Import necessary packages
import sys
import os

def find_pol_files(path=None):
    """

    Finds all of the polarization ms files in a given directory

    Parameters
    ----------
    path : str, optional
	    The path to the directory where the files you want are located. 
	    The default is the current working directory. 

    Returns
    -------
    file_names : ndarray
            An array of uvfits file names

    """
    #Check if a path was specified when called
    #If not, find the current directory path
    if path is None:
            path = os.getcwd()

    #Create a list variable to hold the file names
    file_names = []

    #Search the directory for all the ms files and save them in the list
    for current_file in os,listdir(path):
            if (current_file[-12:]) == '.uvfits.ms':
                file_names.append(os.path.join(path,current_file))

    #Sort the list
    file_names.sort()
    #Return the list of file names
    return (file_names)


def change_pol(file_name, path=None):
    """

    This function reads in a file, changes the polarization index, runs clean, 
    and returns the polarizations index to what it was originally

    Parameters
    ----------
    file_name : str
        File name of the ms file to be altered
    path : str, optional
        File path where the new ms file will be written.
        Default is the current working directory.

    """

    #Check if a path was specified
    #If it was, check that the path is a valid directory
    #Otherwise, it prints an error message
    if path is not None:
        if os.path.isdir(path):
	    #Define a variable that holds the full path for our new file
            vis_file = os.path.join(path,file_name) + '.fake_xx_pol.ms'
        else:
            raise IOError("%s not found." % path)
    #If no path was specified, then we define the variable to hold the new file name
    else:
        vis_file = file_name + '.fake_xx_pol.ms'

    #Create a variable to point to the Polarization table
    pol_cell = file_name + '/POLARIZATION'

    #Open the polarization table and save the polarization index
    tb.open(pol_cell, nomodify=False)
    origin_pol = tb.getcell('CORR_TYPE')

    #Check to see if the polarization is already xx
    if origin_pol[0] == 9:
        print 'Already xx polarized'
    else:
	#If it is not xx polarized, we tell CASA that it is
        tb.putcell('CORR_TYPE',0,[9])
        print 'Now it is xx polarized'

    #Close the table
    tb.close()

    #Create a variable to hold the clean output file name
    imgname = vis_file + '.init.img'

    #Clean the file to create images
    #niter is set to zero so that CASA does not actually clean the file
    clean(vis=file_name, imagename=imgname, niter=0, weighting='briggs',robust=-0.5, imsize=[512,512], cell=['250arcsec'],mode='mfs',nterms=1,spw='0:150~900')

    #Put the original polariazation back in the data
    if origin_pol[0] == 9:
        print 'Was already xx'
    else:
        tb.open(pol_cell, nomodify=False)
        tb.putcell('CORR_TYPE',0,[origin_pol[0]])
        print 'Polarization returned'        
        tb.close()

#Run the functions
if __name__ == '__main__':
    try:
	folders = sys.argv[3:]
        for my_file in folders:
            change_pol(my_file)
    except IndexError:
        print ('No file specified to change the polarization')
