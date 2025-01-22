#combine_massa_scans.py
#This is how we will combine the wWSE data from the two scans into one for each set (e.g. wood scan, or no wood scan, or remobilization scan)

"""Load packages and modules"""
from pprint import pprint
import pandas as pd
from functions import FileFunctions

"""Instantiate classes"""
ff = FileFunctions()

"""Select directories"""
input_data_dir = ff.load_dn("Select a directory containing all of the raw massa files")
output_dir = ff.load_dn("Select a directory where we will put the output combined files")

#load WSE files into a list
wse_files_list = ff.find_files_with_string(input_data_dir, search_string = "MAS", filetype = ".CSV")
wse_files_by_scanset = {}
scansets = []

#create list of scansets (i.e. floodplain and channel scans from the same time)
for i, file in enumerate(wse_files_list):
    directory, basename, exp = ff.extract_info_from_filename(file)

    scanset = basename.split("_")[0] + "_" + basename.split("_")[1] + "_" + basename.split("_")[2]
     
    scansets.append(scanset)
print(scansets)

#iterate through the list of scansets and append the related files to a list (item) related to the scanset(key) in a dictionary
for i, scanset in enumerate(scansets):
    wse_files_by_scanset[f"{scanset}"] = []

    for i, file in enumerate(wse_files_list):
        if scanset in file:
            wse_files_by_scanset[f"{scanset}"].append(file)

#iterate through the dictionary and combine the data, creating an additional swath for the channel scan and appending it to the floodplain scans
for key, scanset in wse_files_by_scanset.items():
    fp_scan_df = None
    ch_scan_df = None
    for i, file in enumerate(scanset):
        scan_data = pd.read_csv(file, header=26, skip_blank_lines=True, usecols=["Pass",  "X", "Y", "Massa Target"])
        if len(scan_data) < 1000:
           scan_data["Pass"] = 6
           ch_scan_df = scan_data

        else:
           fp_scan_df = scan_data

    output_scanset = pd.concat([fp_scan_df, ch_scan_df], ignore_index=True)
    output_filename = output_dir + "/" + key + ".CSV"
    output_scanset.to_csv(output_filename, index= False)