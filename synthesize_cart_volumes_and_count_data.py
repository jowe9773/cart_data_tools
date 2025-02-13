import os
import pandas as pd
import geopandas as gpd
from functions import FileFunctions
from pprint import pprint

ff = FileFunctions()

count_data_df = pd.read_csv(ff.load_fn("Choose the jam count data file"))
outpath = ff.load_dn("Choose a place to store the output")


# Set your root folder
root_folder = ff.load_dn("Choose a file containing all folders with data")
experiment_folder_list = []
# Walk through all subfolders
for dirpath, _, filenames in os.walk(root_folder):
    # Collect all input files in the current subfolder

    if "2024" in dirpath and "MAS" not in dirpath:
        experiment_folder_list.append(dirpath)

pprint(experiment_folder_list)

s_volume = 11988
i_volume = 25559
l_volume = 58584

count_data_df["wood_volume (mm^3)"] = count_data_df["s_tot"]*s_volume + count_data_df["i_tot"]*i_volume + count_data_df["l_tot"]*l_volume

#add a coulmn to the count_data_df for remote_volume
count_data_df["jam_volume (mm^3)"] = None

pprint(count_data_df)

# now go through experiments and process each one
for i, exp_folder in enumerate(experiment_folder_list):

    filenames = os.listdir(exp_folder)

    #identify neccesary files for calculating volume
    nowood_fn = ff.find_files_with_string(exp_folder, "nowood", ".tif")
    wood_fn = ff.find_files_with_string(exp_folder, "_wood", ".tif")
    remobilization_fn = ff.find_files_with_string(exp_folder, "_remobilization", ".tif")
    real_wood_fn = ff.find_files_with_string(exp_folder, "_true_wood.", ".shp")
    real_wood_remobilization_fn = ff.find_files_with_string(exp_folder, "_true_wood_remobilization", ".shp")
    remote_jam_voumes_wood_fn = ff.find_files_with_string(exp_folder, "-wood_volumes", ".shp")
    remote_jam_voumes_remobilized_fn = ff.find_files_with_string(exp_folder, "-remobilized_wood_volumes", ".shp")

    print(remote_jam_voumes_wood_fn)
    print(remote_jam_voumes_remobilized_fn)


    #find wood volume after high/low flood
    if len(remote_jam_voumes_wood_fn)>0 and len(remote_jam_voumes_remobilized_fn)<=0:
        experiment = exp_folder.split("\\")[-1]
        print(experiment)
        print("This is a high flood experiment")

        ##we want volumes for wood
        remote_jams = gpd.read_file(remote_jam_voumes_wood_fn[0])
        pprint(remote_jams)

        for index, row in remote_jams.iterrows():
            jam_value = row["jam"]
            cell_sum = row['cell_sum']

            #find row in the count data df that is associated with this experiment and jam
            condition = (count_data_df['exp_name'] == experiment) & (count_data_df['jam'] == jam_value)
            match = count_data_df.loc[condition]
            print(match)

            if not count_data_df.loc[condition].empty:
                count_data_df.loc[condition, 'jam_volume (mm^3)'] = cell_sum

    #find wood volume after remobilization flood
    if len(remote_jam_voumes_remobilized_fn)>0: 
        experiment = exp_folder.split("\\")[-1]
        print(experiment)
        print("This is a low flood experiment, jams are from after remobilization")
    
        # we want volumes for remobilized wood
        remote_jams = gpd.read_file(remote_jam_voumes_remobilized_fn[0])


        for index, row in remote_jams.iterrows():
                jam_value = row["jam"]
                cell_sum = row['cell_sum']

                #find row in the count data df that is associated with this experiment and jam
                condition = (count_data_df['exp_name'] == experiment) & (count_data_df['jam'] == jam_value)
                match = count_data_df.loc[condition]
                print(match)

                if not count_data_df.loc[condition].empty:
                    count_data_df.loc[condition, 'jam_volume (mm^3)'] = cell_sum
    
print(count_data_df)
 
count_data_df.to_csv(outpath + "/jam_data_with_volumes.csv")
