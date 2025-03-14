#bulk_calculate_volume.py

#import packages and modules
import os
from pprint import pprint
from calculate_volume import CalculateVolume, DetectChannelBottom
from functions import FileFunctions

#instantiate classes
dcv = DetectChannelBottom()
cv = CalculateVolume()
ff = FileFunctions()

# Set your root folder
root_folder = ff.load_dn("Choose a file containing all folders with data")
#channel_thresh =  -15

experiment_folder_list = []

# Walk through all subfolders
for dirpath, _, filenames in os.walk(root_folder):
    # Collect all input files in the current subfolder

    if "2024" in dirpath and "MAS" not in dirpath:
        experiment_folder_list.append(dirpath)

pprint(experiment_folder_list)

#now go through experiments and process each one
for i, exp_folder in enumerate(experiment_folder_list):
    filenames = os.listdir(exp_folder)

    #identify neccesary files for calculating volume
    nowood_fn = ff.find_files_with_string(exp_folder, "nowood", ".tif")
    wood_fn = ff.find_files_with_string(exp_folder, "_wood", ".tif")
    remobilization_fn = ff.find_files_with_string(exp_folder, "_remobilization", ".tif")
    real_wood_fn = ff.find_files_with_string(exp_folder, "_split_wood.", ".shp")
    real_wood_remobilization_fn = ff.find_files_with_string(exp_folder, "_split_remobilized", ".shp")
    channel_fn = ff.find_files_with_string(exp_folder, "_channel", "*.shp")


    print(" ")
    print(" ")

    print(exp_folder)
    print("nowood tif: ", nowood_fn)
    print("wood tif: ", wood_fn)
    print("remobilization tif: ", remobilization_fn)
    print("wood polygons fn: ", real_wood_fn)
    print("remobilization polygons fn: ", real_wood_remobilization_fn)
    print("chanel: ", channel_fn)
 
    print(" ")

    #find wood volume after high/low flood
    if len(nowood_fn)>0 and len(wood_fn)>0 and "20240714" not in exp_folder:
        print(f"calculating volume for {exp_folder} wood")
        cv.calculate_volume(nowood_fn[0], wood_fn[0], real_wood_fn[0], exp_folder)
        

    #find wood volume after remobilization flood
    if len(nowood_fn)>0 and len(remobilization_fn)>0 and "20240714" not in exp_folder:
        print(f"calculating volume for {exp_folder} remobilization")
        cv.calculate_volume(nowood_fn[0], remobilization_fn[0], real_wood_remobilization_fn[0], exp_folder, remobilization = "Y")
 