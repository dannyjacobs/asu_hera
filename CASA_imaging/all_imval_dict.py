#!/usr/bin/env python

import os
import sys
import numpy as np

def find_image_files(path=None):
	if path is  None:
		path = os.getcwd()

	folders = []

	for folder in os.listdir(path):
	    if folder.endswith("img.image"):
			folders.append(os.path.join(path,folder))

	folders.sort()
	return (folders)


def create_dict(folder):
	xval = imval(folder, box='0,0,511,511')
	np.savez(folder,coords=xval['coords'],vals=xval['data'])


if __name__ == '__main__':
	try:
		arg = sys.argv[-1:]
		print 'YOUR DIRECTORY BEING USED AS AN ARGUMENT IS:'+arg[0]
		folders = find_image_files(arg[0])
		for folder in folders:
			create_dict(folder)
	except IndexError:
		print('No file specified for data extraction')
