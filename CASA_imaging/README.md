# CASA_imaging

## Installation

### Dependencies

CASA, or the Common Astronomy Software Applications package developed by the NRAO, is required to run casa_image_ms. This script has been tested on CASA version 4.6.91, but should work on later versions as well. To install CASA, follow the link below and choose a version >= 4.6.91 that works for your operating system.

Install CASA: https://casa.nrao.edu/casa_obtaining.shtml

## Usage

To use this script, there are a couple of things that need to be defined. The first is the json file that stores the parameters that will be used to calibrate a file and generate an image from a measurement set. An example of this file is *standard_run_parameters.json* in this directory. 

```casa -c casa_image_ms.py <json parameter file> <measurement set> ```
