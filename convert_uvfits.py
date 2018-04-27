#!/usr/bin/env casapy=

from casa import importuvfits
import sys


def convert_uvfits(folder):
    importuvfits(fitsfile=folder,vis=(folder + '.ms'))

if __name__ == '__main__':
    try:
        folder = sys.argv[1]
        convert_uvfits(folder)
    except IndexError:
        print ('No file specified for conversion from uvfits to ms')
