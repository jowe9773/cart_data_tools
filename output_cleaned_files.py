#output_cleaned_files.py

"""Load neccesary packages and modules"""
import pandas as pd
from pprint import pprint
import os
from functions import FileFunctions, FindCentersFunctions, FindPairsFunctions
from apply_correction_topo import ApplyTopoCorrection
from apply_buffer import ApplyBuffer

"""Instantiate classes"""
ff = FileFunctions()

"""Select files and directories containing necceary info"""
experiment_summary = ff.load_fn("Select experiment summary file", [("CSV Files", "*.csv")])
topo_dir = ff.load_dn("Select directory with all topography tif files")
wse_dir = ff.load_dn("Select directory with all WSE csv files")
offsets_dir = ff.load_dn("Select directory with all offsets files")
out_location = ff.load_dn("Select directory to store outputs in") 
#centroids_dir = ff.load_dn("Select directory with all centroids files")

"""Create a set of pandas dataframes (one for each flood magnitude/forest stand density) that show all of the files that each experiment has"""
#Autochthonous df
autoc_df = pd.DataFrame(columns=["Experiment", "preTopo", "postTopo", "autochthonousWSE", "prepostOffset"])


#High flood dfs
h_pointfive_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "nowoodWSE", "woodWSE", "previousOffset", "nowoodOffset"])

h_one_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "nowoodWSE", "woodWSE", "previousOffset", "nowoodOffset"])

h_two_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "nowoodWSE", "woodWSE", "previousOffset", "nowoodOffset"])

h_four_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "nowoodWSE", "woodWSE", "previousOffset", "nowoodOffset"])


#Low flood dfs
l_pointfive_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "remobilizationTopo", "nowoodWSE", "woodWSE", "remobilizationWSE", "previousOffset", "nowoodOffset", "remobilizationOffset"])

l_one_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "remobilizationTopo", "nowoodWSE", "woodWSE", "remobilizationWSE", "previousOffset", "nowoodOffset", "remobilizationOffset"])

l_two_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "remobilizationTopo", "nowoodWSE", "woodWSE", "remobilizationWSE", "previousOffset", "nowoodOffset", "remobilizationOffset"])

l_four_df = pd.DataFrame(columns=["Experiment", "nowoodTopo", "woodTopo", "remobilizationTopo", "nowoodWSE", "woodWSE", "remobilizationWSE", "previousOffset", "nowoodOffset", "remobilizationOffset"])

#list of dataframes (for use in future iterating)
dfs = [autoc_df, h_pointfive_df, h_one_df, h_two_df, h_four_df, l_pointfive_df, l_one_df, l_two_df, l_four_df]

"""Use experiment summary file to create rows for each experiment in the appropriate dataframe"""
#create dataframe for experiment summary
exp_sum_df = pd.read_csv(experiment_summary)

for i, row in exp_sum_df.iterrows():

    if row["Flood type"] == "A":
        autoc_df.loc[len(autoc_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "H" and row["Forest Stand Density"] == 0.5:
        h_pointfive_df.loc[len(h_pointfive_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "H" and row["Forest Stand Density"] == 1.0:
        h_one_df.loc[len(h_one_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "H" and row["Forest Stand Density"] == 2.0:
        h_two_df.loc[len(h_two_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "H" and row["Forest Stand Density"] == 4.0:
        h_four_df.loc[len(h_four_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "L" and row["Forest Stand Density"] == 0.5:
        l_pointfive_df.loc[len(l_pointfive_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "L" and row["Forest Stand Density"] == 1.0:
        l_one_df.loc[len(l_one_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "L" and row["Forest Stand Density"] == 2.0:
        l_two_df.loc[len(l_two_df)] = {"Experiment" : row["Experiment Name"]}

    if row["Flood type"] == "L" and row["Forest Stand Density"] == 4.0:
        l_four_df.loc[len(l_four_df)] = {"Experiment" : row["Experiment Name"]}

"""Populate the topography columns of the dataframes"""
#load topo files into a list
topo_files_list = ff.find_files_with_string(topo_dir, search_string = "2024", filetype = ".tif")

#iterate through the list and sort files into their appropriate dataframe
for i, file in enumerate(topo_files_list):
    #gather information from filename
    directory, basename, exp = ff.extract_info_from_filename(file)
    scan_type = basename.split("_")[-1].split(".")[0]

    #look for where the file should go in the dataframes above
    for j, df in enumerate(dfs):
        row_index = df[df["Experiment"] == exp].index
        if not row_index.empty:

            #determine the appropriate column
            column_name = scan_type + "Topo"

            #fill with filename
            df.loc[row_index, column_name] = file
        
#We have loaded all of the files that belong to a particular experiment (i.e. were recorded on that day) we will deal with the nowood scans for experiemnts that borrow them when we do the offsets

"""Populate the WSE columns of the dataframes"""
#load WSE files into a list
wse_files_list = ff.find_files_with_string(wse_dir, search_string = "MAS", filetype = ".CSV")

for i, file in enumerate(wse_files_list):
    directory, basename, exp = ff.extract_info_from_filename(file)
    scan_type = basename.split("_")[-1].split("(")[0]

    #look for where the file should go in the dataframes above
    for j, df in enumerate(dfs):
        row_index = df[df["Experiment"] == exp].index
        if not row_index.empty:

            #determine the appropriate column
            column_name = scan_type + "WSE"

            #fill with filename
            df.loc[row_index, column_name] = file

"""Populate the offset columns of the dataframes and fill in missing nowood scans"""
offset_files = []
for i, name in enumerate(["autochthonous", "high_pointfive", "high_one", "high_two", "high_four", "low_pointfive", "low_one", "low_two", "low_four"]):
    offset_file = ff.find_files_with_string(offsets_dir, name, ".csv")
    offset_files.append(offset_file[0])

for i, file in enumerate(offset_files):

    #load csv into pandas df
    offset_df = pd.read_csv(file)

    #fill in autochthonous, previous, and remobilization offset columns(if present)
    if "Pre-Post" in offset_df.columns:

        #iterate through the rows of the related dataframe from above
        for j, row in offset_df.iterrows():
            experiment_name = row["Experiment"]
            prepost_offset = row["Pre-Post"]

            dfs[i].loc[dfs[i]['Experiment'] == experiment_name, 'prepostOffset'] = prepost_offset

    if "Previous" in offset_df.columns:

        #iterate through the rows of the related dataframe from above
        for j, row in offset_df.iterrows():
            experiment_name = row["Experiment"]
            previous_offset = row["Previous"]

            dfs[i].loc[dfs[i]['Experiment'] == experiment_name, 'previousOffset'] = previous_offset

    if "Remobilization" in offset_df.columns:

        #iterate through the rows of the related dataframe from above
        for j, row in offset_df.iterrows():
            experiment_name = row["Experiment"]
            remobilization_offset = row["Remobilization"]

            dfs[i].loc[dfs[i]['Experiment'] == experiment_name, 'remobilizationOffset'] = remobilization_offset

    #now let fill in any nowood files that were not recorded
    for j, row in dfs[i].iterrows():
            #if the dataframe does not contain the prepostOffset column (i.e. is not an autochthonous run), and the nowoodTopo column is empty:
        if "prepostOffset" not in dfs[i].columns and pd.isna(row["nowoodTopo"]):

            #identify the nowood column with the lowest offset
            to_compare = offset_df.loc[offset_df['Experiment'] == row["Experiment"], offset_df.filter(like='2024').columns]
            min_nowood_column = to_compare.idxmin(axis=1).iloc[0]

            #get the nowood topo filepath related to this column
            search_string = min_nowood_column + "_nowood"
            nowood_topo_filepath = ff.find_files_with_string(topo_dir, search_string, ".tif")[0]

            #put this nowood topo filepath into the dataframe
            dfs[i].loc[j, "nowoodTopo"] = nowood_topo_filepath

    #now lets fill in the nowood offset
    for j, row in dfs[i].iterrows():
        if "prepostOffset" not in dfs[i].columns:
            directory, filename = os.path.split(row["nowoodTopo"])
            nowood_scan_exp = filename.split("_no")[0]
            experiment = row["Experiment"]

            offset = offset_df.loc[offset_df['Experiment'] == experiment, nowood_scan_exp].iloc[0]
 
            #put this nowood topo offset into the dataframe
            dfs[i].loc[j, "nowoodOffset"] = offset

outnames = ["autoc_df", "h_pointfive_df", "h_one_df", "h_two_df", "h_four_df", "l_pointfive_df", "l_one_df", "l_two_df", "l_four_df"]

for i, df in enumerate(dfs):
    outpath = out_location + "/" + outnames[i] + ".csv"
    df.to_csv(outpath, index= False)
