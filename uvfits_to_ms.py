from casa import importuvfits
import sys
import os

def find_uvfits_files(polarization='xx',path=None):
    """

    Finds all of the uvfits files in a given directory

    Parameters
    ----------
    polarization : str
        Polarization of the uvfits files to search for.
        Default is xx polarization
    path : str
        Folder path where the function looks for uvfits files.
        Default is the current working directory.

    Returns
    -------
    array
        An array of uvfits file names

    """

    if path == None:
        path = os.getcwd()

    folders = []

    for folder in os.listdir(path):
        if (folder[-16:]) == polarization + '.HH.uvR.uvfits':
            folders.append(os.path.join(path,folder))

    folders.sort()
    return (folders)

def convert_uvfits(folder,path=None):
    """

    Converts a single uvfits file to ms format

    Parameters
    ----------
    folder : str
        File path of the uvfits file to be converted to
        ms format
    path : str
        File path where the new ms file will be written.
        Default is the current working directory.

    """
    if path != None:
        if os.path.isdir(path):
            vis_file = os.path.join(path,folder) + '.ms'
        else:
            raise IOError("%s not found." % path)

    else:
        vis_file = folder + '.ms'

    importuvfits(fitsfile=folder,vis=vis_file)

if __name__ == '__main__':
    try:
        folders = sys.argv[3:]
        for folder in folders:
            convert_uvfits(folder)
    except IndexError:
        print ('No file specified for conversion from uvfits to ms')
