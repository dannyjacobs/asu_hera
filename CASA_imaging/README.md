# CASA_imaging

## Installation

### Dependencies

CASA, or the Common Astronomy Software Applications package developed by the NRAO, is required to run casa_image_ms. This script has been tested on CASA version 4.6.91, but should work on later versions as well. To install CASA, follow the link below and choose a version >= 4.6.91 that works for your operating system.

Install CASA: https://casa.nrao.edu/casa_obtaining.shtml

## Usage

### Reformatting Data

The purpose of this package was to relatively easily image full nights of HERA
data. HERA's data products come in the form of miriad files that have a file
extension beginning with uv (common variants include uvR, uvOR, etc.). CASA,
on the other hand, reduces data from from measurement set (.ms) files. This
package includes two separate modules to convert from HERA miriad file outputs
to CASA-usable measurement set input files.

The conversion between miriad files to measurement sets cannot be done directly
(that I know of), so the miriad files must first be converted into uvfits files.
This can be done with `miriad_to_uvfits.py` as shown in the command below. Either
a single miriad file can be selected to be converted to uvfits or the input can
be a glob as shown below. By default, the output files are stored in the same
directory as the miriad files.

```
python miriad_to_uvfits.py /path/to/data/*.uv
```

Once the uvfits files have been produced, measurement sets can be generated using
`uvfits_to_ms.py`. The usage of this script is shown below:

```
casa -c uvfits_to_ms.py /path/to/data/*.uvfits
```

CASA comes built in with a function to read in uvfits files and convert to
measurement sets. Like `miriad_to_uvfits.py` the input can either be a single file or glob. Once this script is run, the data should be in a usable format for CASA.

### Configuring the Run

The CLEAN process used in this pipeline is based on HERA
[Memo 22](http://reionization.org/wp-content/uploads/2013/03/HERAmemo22-GC_imaging_cal.pdf)
and [Memo 23](http://reionization.org/wp-content/uploads/2013/03/HERA19.Comm2_.pdf).
In these memos, HERA data is calibrated using a self-calibration model of the galactic
center. The default parameters match what is used in this memo. However, to allow
users to configure imaging to their desired parameters, a json configure file
is included in this module to set imaging parameters. It should be noted that
all parameters below, with the exception of the self-calibration cycle are
applied to all measurement sets. There currently is no support for setting
parameters that vary over the course of a run within the configuration file.

As an example, we can walk through the `imgaing_runs/2458042/run_3/run.json`
configuration file to show how you would go about setting up your own
configuration file. At the top of this file, we have the dictionary that is used
to set the path where CASA generated images will be stored. The `run_folder`
key stores the file path of the directory where `image_folder` will be created.
Fits files made by CASA will be sent to the `image_folder` within `run_folder`.
Other files such as calibration files will be stored in the `run_folder`.
It is important to note that the key names in this dictionaries
should not be changed. Only the values attached to the keys should be changed for
your personal run.

```
"data_path" : {
  "run_folder": "/data6/HERA/HERA_imaging/2458042/run_3",
  "image_folder": "imgs"
}
```

Once the location of your run is set, we can move on to setting the calibration
parameters. The `new_calibration` key gives you the option to generate new
calibration files based on the self-calibration routine defined in Memo 22 or
to use calibration files generated from a previous run. If `new_calibration` is
set to `True`, the self-calibration routine will be run using the parameters in
`new_cal_params`. Parameters that you will most commonly be change are
`file_to_calibrate` and `cal_sources`. The `file_to_calibrate` sets the
measurement on which the self-calibration routine will be run. This file should
most likely be a file within your particular set of measurement sets. The
`cal_sources` key stores dictionaries that containing information on which
sources will be used to run the self-calibration. One or more calibration sources
can be used and given any name such as with `some_other_name`. Once these are set
the rest of the parameters in the `new_cal_params` dictionary can be changed.

If `new_calibration` is set to `False`, the self-calibration routine will be
skipped and calibration will be applied to the data by the `.cal` files whose
location can be defined by the user in the `calibration_files` key. The
calibration files in this example were generated using the self-calibration
routine from Memo 22. In cases where the data is already pre-calibrated, you
can simply set `new_calibration` to `False` and `calibration_files` to `[]`. This
will prevent calibration from being added to the data.

```
"new_calibration": "False",

"new_cal_params": {
  "file_to_calibrate": "/data6/HERA/data/2458042/KM_uvR_files/zen.2458042.12552.xx.HH.uvR.uvfits.ms",
  "model_name": "GC.cl",
  "cal_sources" : {
    "galactic_center": {
      "shape": "point",
      "fluxunit": "Jy",
      "flux": 1,
      "dir": "J2000 17h45m40.0409s -29d0m28.118s"
    },
    "some_other_name": {
      "shape": "point",
      "fluxunit": "Jy",
      "flux": 1000,
      "dir": "J2000 12h00m00.000s -10d40m00.000s"
    }
  },

  ....
}
"calibration_files" : ["/data6/HERA/HERA_imaging/2458042/run_3/zen.2458042.12552.xx.HH.uvR.uvfits.msG.cal",
                       "/data6/HERA/HERA_imaging/2458042/run_3/zen.2458042.12552.xx.HH.uvR.uvfits.msK.cal",
                       "/data6/HERA/HERA_imaging/2458042/run_3/zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msB.cal",
                       "/data6/HERA/HERA_imaging/2458042/run_3/zen.2458042.12552.xx.HH.uvR.uvfits.mssplit.msc2.msB.cal"]
```

CLEAN masks can also be applied to the data. The file below contains all sources
within 10 degrees of HERA's zenith declination for all right ascensions brighter
than ~1 Jy.

```
"clean_mask_sources" : {
  "file_name" : "imaging_runs/2458042/run_15/mask_sources.json"
}
```

In the block below, the parameters for the flag function are entered.
Any function parameters used in the flag function can be entered into this
dictionary.

```
"flag": {
  "autocorr": "False",
  "mode": "tfcrop"
}
```

Finally, CLEAN can be configured using the dictionary below. This is the block
that sets the parameters for the final CLEAN that produces an image from the
data. Any CLEAN parameter input can be added to this dictionary and will be
passed on to the final CLEAN function. The values in the dictionary below are
simply the base arguments passed into CLEAN for this particular run.

```
"clean" : {
  "niter" : 6000,
  "weighting" : "briggs",
  "robust" :   -0.5,
  "imsize" :   [512,512],
  "cell" :   ["250arcsec"],
  "mode" :   "mfs",
  "nterms" :   1,
  "spw" : "0:100~800"
}
```
### Running the Pipeline

Once the desired settings have been selected and set in your `run.json` file,
you can run this pipeline using the command below.

```casa -c casa_image_ms.py /path/to/parameter_file/run.json /path/to/data/*ms ```
