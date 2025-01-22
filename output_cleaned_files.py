#output_cleaned_files.py

"""Load neccesary packages and modules"""
import pandas as pd
from pprint import pprint
from functions import FileFunctions, FindCentersFunctions, FindPairsFunctions
from apply_correction_topo import ApplyTopoCorrection
from apply_buffer import ApplyBuffer

"""Instantiate classes"""
ff = FileFunctions()

"""Select files and directories containing necceary info"""
experiment_summary = ff.load_fn("Select experiment summary file", [("CSV Files", "*.csv")])
topo_dir = ff.load_dn("Select directory with all topography tif files")
#offsets_dir = ff.load_dn("Select directory with all offsets files")
wse_dir = ff.load_dn("Select directory with all WSE csv files")
#centroids_dir = ff.load_dn("Select directory with all centroids files")

"""Create a set of pandas dataframes (one for each flood magnitude/forest stand density) that show all of the files that each experiment has"""
#Autochthonous df
autoc_df = pd.DataFrame(columns=["Experiment", "PreTopo", "PostTopo", "AutocWSE", "PrePostOffset"])


#High flood dfs
h_pointfive_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "NowoodWSE", "WoodWSE", "PreviousOffset", "NowoodOffset"])

h_one_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "NowoodWSE", "WoodWSE", "PreviousOffset", "NowoodOffset"])

h_two_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "NowoodWSE", "WoodWSE", "PreviousOffset", "NowoodOffset"])

h_four_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "NowoodWSE", "WoodWSE", "PreviousOffset", "NowoodOffset"])


#Low flood dfs
l_pointfive_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "RemobilizationTopo", "NowoodWSE", "WoodWSE", "RemobilizationWSE", "PreviousOffset", "NowoodOffset", "ReOffset"])

l_one_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "RemobilizationTopo", "NowoodWSE", "WoodWSE", "RemobilizationWSE", "PreviousOffset", "NowoodOffset", "RemobilizationOffset"])

l_two_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "RemobilizationTopo", "NowoodWSE", "WoodWSE", "RemobilizationWSE", "PreviousOffset", "NowoodOffset", "RemobilizationOffset"])

l_four_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "RemobilizationTopo", "NowoodWSE", "WoodWSE", "RemobilizationWSE", "PreviousOffset", "NowoodOffset", "RemobilizationOffset"])

#list of dataframes (for use in future iterating)
dfs = [autoc_df, h_pointfive_df, h_one_df, h_two_df, h_four_df, l_pointfive_df, l_one_df, l_two_df, l_four_df]

"""Use experiment summary file to create rows for each experiment in the appropriate dataframe"""
#create dataframe for experiment summary
exp_sum_df = pd.read_csv(experiment_summary)
print(exp_sum_df)

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
    for i, df in enumerate(dfs):
        row_index = df[df["Experiment"] == exp].index
        if not row_index.empty:

            #determine the appropriate column
            column_name = scan_type + "Topo"
            matching_columns = [col for col in df.columns if col.lower() == column_name.lower()]

            if matching_columns:
                target_column = matching_columns[0]

                #fill with filename
                df.loc[row_index, target_column] = file
        
#We have loaded all of the files that belong to a particular experiment (i.e. were recorded on that day) we will deal with the nowood scans for experiemnts that borrow them when we do the offsets


"""Populate the WSE columns of the dataframes"""
#load WSE files into a list
wse_files_list = ff.find_files_with_string(wse_dir, search_string = "MAS", filetype = ".CSV")

for i, file in enumerate(wse_files_list):
    directory, basename, exp = ff.extract_info_from_filename(file)
    print(basename)
    print(exp)

"""Populate the Offset columns of the dataframes"""
