'''

To run (in terminal):
casa -c change_pol.py <measurement sets>

'''

import sys
import os

def find_pol_files(path=None):
    """

    Finds all of the polarization ms files in a given directory

    Returns
    -------
    array
            An array of uvfits file names

    """

    if path is None:
            path = os.getcwd()

    folders = []

    for folder in os,listdir(path):
            if (folder[-12:]) == '.uvfits.ms':
                folders.append(os.path.join(path,folder))

    folders.sort()
    return (folders)


def get_pol(folder, path=None):
    """

    reads in the file and gets the original polarization

    Parameters
    ----------
    folder : str
        File path of the ms file to be altered
    path : str
        File path where the new ms file will be written.
        Default is the current working directory.

    """

    # Create a variable to hold the modified file name
    if path is not None:
        if os.path.isdir(path):
            vis_file = os.path.join(path,folder) + '.fake_xx_pol.ms'
        else:
            raise IOError("%s not found." % path)
    else:
        vis_file = folder + '.fake_xx_pol.ms'

    # Create a variable to point to the Polarization table
    pol_cell = folder + '/POLARIZATION'

    # Open the polarization table and save the polarization index
    tb.open(pol_cell, nomodify=False)
    origin_pol = tb.getcell('CORR_TYPE')


    # Check to see if the polarization is already xx
    if origin_pol[0] == 9:
        print 'Already xx polarized'
    else:
        tb.putcell('CORR_TYPE',0,[9])
        print 'Now it is xx polarized'

    # Close the table
    tb.close()

    # Create a variable to hold the clean output file name
    imgname = vis_file + '.init.img'

    # Clean the file to create images
    clean(vis=folder, imagename=imgname, niter=0, weighting='briggs',robust=-0.5, imsize=[512,512], cell=['250arcsec'],mode='mfs',nterms=1,spw='0:150~900')

    #Put the original polariazation back in the data
    if origin_pol[0] == 9:
        print 'Was already xx'
    else:
        tb.open(pol_cell, nomodify=False)
        tb.putcell('CORR_TYPE',0,[origin_pol[0]])
        print 'Polarization returned'        
        tb.close()


if __name__ == '__main__':
    try:
        folders = sys.argv[3:]
        for folder in folders:
            get_pol(folder)
    except IndexError:
        print ('No file specified to change the polarization')
