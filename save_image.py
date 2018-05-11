from casa import *
import viewertool

def save_image(imname,out,ext='png'):
    """

    Creates a single image with a default format '.png' from an image file

    Parameters
    ----------
    imname : str
        Folder path where the function looks for the image file
    out : str
        Name of the output image
    ext : str
        File format of the image. Acceptable options are jpg, pdf, eps, ps, png,
        xbm, xpm, or ppm.
            Default: 'png'

    """
    img = viewertool.viewertool()
    img.load(imname)
    img.output(device=out,format=ext)
    img.close()
