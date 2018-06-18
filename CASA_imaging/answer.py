import argparse
import glob
import json

parser = argparse.ArgumentParser(description='Get some files according to a pattern')
parser.add_argument("-p", "--params",type=str,help="name of the parameter file")
parser.add_argument('-f','--files', required=True,type=str, action='store', nargs='+')
args = parser.parse_args()
print args.run_files
config = args.params

print config

with open(config) as f:
    config_data = json.load(f)

if config_data['new_calibration']:
    cal_params = config_data['new_cal_params']
    infile = cal_params['file_to_calibrate']
    model_name = cal_params['model_name']
    cal_sources = cal_params['cal_sources']
    clean_1_params = cal_params['clean_1']
    clean_2_params = cal_params['clean_2']
    clean_final_params = cal_params['clean_final']
    band_pass_1 = cal_params['band_pass_1']
    band_pass_2 = cal_params['band_pass_2']
    kc,gc,bc,bc1 = make_initial()

print config_data
