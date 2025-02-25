import os
from pprint import pprint
from calculate_volume import CalculateVolume, DetectChannelBottom
from functions import FileFunctions

#instantiate classes
dcb = DetectChannelBottom()
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
    real_wood_fn = ff.find_files_with_string(exp_folder, "_true_wood.", ".shp")
    real_wood_remobilization_fn = ff.find_files_with_string(exp_folder, "_true_wood_remobilization", ".shp")
    

    print(exp_folder)
    print("nowood tif: ", nowood_fn)
    print("wood tif: ", wood_fn)
    print("remobilization tif: ", remobilization_fn)
    print("wood polygons fn: ", real_wood_fn)
    print("remobilization polygons fn: ", real_wood_remobilization_fn)
 
    print(" ")

    #find wood volume after high/low flood
    if len(nowood_fn)>0 and len(wood_fn)>0:
        output_file = (exp_folder + "/" + os.path.split(wood_fn[0])[1].split("_")[0] + "_" + os.path.split(wood_fn[0])[1].split("_")[1] + "_channel.shp")
        print("output file: ", output_file)
        print(f"finding channel for {exp_folder.split("\\")[1]}")
        dcb.detect_channel_bottom(nowood_fn[0],-10, channel=True, output_file=output_file)