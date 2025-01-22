#output_cleaned_files.py

"""Load neccesary packages and modules"""
import pandas as pd
from functions import FileFunctions, FindCentersFunctions, FindPairsFunctions
from apply_correction_topo import ApplyTopoCorrection
from apply_buffer import ApplyBuffer

"""Instantiate classes"""
ff = FileFunctions()

"""Select files and directories containing necceary info"""
experiment_summary = ff.load_fn("Select experiment summary file", [("CSV Files", "*.csv")])
#offsets_dir = ff.load_dn("Select directory with all offsets files")
#topo_dir = ff.load_dn("Select directory with all topography tif files")
#wse_dir = ff.load_dn("Select directory with all WSE csv files")
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
l_pointfive_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "ReTopo", "NowoodWSE", "WoodWSE", "ReWSE", "PreviousOffset", "NowoodOffset", "ReOffset"])

l_one_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "ReTopo", "NowoodWSE", "WoodWSE", "ReWSE", "PreviousOffset", "NowoodOffset", "ReOffset"])

l_two_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "ReTopo", "NowoodWSE", "WoodWSE", "ReWSE", "PreviousOffset", "NowoodOffset", "ReOffset"])

l_four_df = pd.DataFrame(columns=["Experiment", "NowoodTopo", "WoodTopo", "ReTopo", "NowoodWSE", "WoodWSE", "ReWSE", "PreviousOffset", "NowoodOffset", "ReOffset"])

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

print("Autochthonous: ")
print(autoc_df)

print("High 0.5: ")
print(h_pointfive_df)

print("High 1.0: ")
print(h_one_df)

print("High 2.0: ")
print(h_two_df)

print("High 4.0: ")
print(h_four_df)

print("Low 0.5: ")
print(l_pointfive_df)

print("Low 1.0: ")
print(l_one_df)

print("Low 2.0: ")
print(l_two_df)

print("Low 4.0: ")
print(l_four_df)