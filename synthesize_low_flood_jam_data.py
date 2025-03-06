import os
import numpy as np
import pandas as pd
import geopandas as gpd
from functions import FileFunctions
from pprint import pprint

ff = FileFunctions()

count_data_df = pd.read_csv(ff.load_fn("Choose the jam count data file"))
outpath = ff.load_dn("Choose a place to store the output")


# Set your root folder
root_folder = ff.load_dn("Choose a file containing all folders with data")

#lets get the output_jam file setup
jam_data_df = gpd.GeoDataFrame(columns = ["exp_name", "flood", "trans_reg", "fsd", "jam", 
                                    "centroid_x", "centroid_y", 
                                    "ch_jam_area", "fp_jam_area", "frac_area_in_ch", "jam_area","ch_jam_vol", "fp_jam_vol", "frac_vol_in_ch", "jam_vol"])


for i, row in count_data_df.iterrows():
    
    #get info from count data df
    exp_name = row["Experiment Name"]
    flood = row["Flood type"]
    trans_reg = row["Congestion"]
    fsd = row["Forest Stand Density"]

    if isinstance(exp_name, str):
        #lets load the files associated with this row
        exp_folder = root_folder + "/" + exp_name
        remote_jam_volumes_wood_fn = ff.find_files_with_string(exp_folder, "-wood_volumes", ".shp")
        remote_jam_volumes_remobilized_fn = ff.find_files_with_string(exp_folder, "-remobilized_wood_volumes", ".shp")
        wood_centroids = ff.find_files_with_string(exp_folder, "wood_centroids", ".shp")
        remobilized_centroids = ff.find_files_with_string(exp_folder, "remobilized_centroids", ".shp")

        print("centroids file: ", wood_centroids)
        print("Jams shapefile:", remote_jam_volumes_wood_fn)

        if "20240805" not in exp_name and "20240807" not in exp_name and "20240714" not in exp_name:
            if len(remote_jam_volumes_remobilized_fn) >= 1 and len(remote_jam_volumes_wood_fn) >= 1:
                #load wood jam volumes and centroids
                jam_volumes = gpd.read_file(remote_jam_volumes_wood_fn[0])
                jam_centroids = gpd.read_file(wood_centroids[0])

                print("Jam volumes: ", jam_volumes)
                print("Centroids: ", jam_centroids)

                #now lets extract the information we want from the centroids file
                for i, row in jam_centroids.iterrows():
                    if row["jam"] > 0:

                        jam = row["jam"]

                        centroid_x = row.geometry.x
                        centroid_y = row.geometry.y

                        #now lets get the info we want from the jam volumes file
                        floodplain = (jam_volumes['jam'] == row["jam"]) & (jam_volumes["Channel?"] == 0)
                        floodplain_match = jam_volumes.loc[floodplain]
                        
                        channel = (jam_volumes['jam'] == row["jam"]) & (jam_volumes["Channel?"] == 1)
                        channel_match = jam_volumes.loc[channel]

                        ch_jam_vol = 0
                        fp_jam_vol = 0
                        ch_jam_area = 0
                        fp_jam_area = 0

                        if channel_match.empty is not True:
                            ch_jam_vol = channel_match["cell_sum"].values[0]
                            ch_jam_area = channel_match.geometry.area.iloc[0]


                        if floodplain_match.empty is not True:
                            fp_jam_vol = floodplain_match["cell_sum"].values[0]
                            fp_jam_area = floodplain_match.geometry.area.iloc[0]

                        jam_vol = ch_jam_vol + fp_jam_vol
                        jam_area = ch_jam_area + fp_jam_area

                        frac_vol_in_ch = ch_jam_vol/jam_vol
                        frac_area_in_ch = ch_jam_area/jam_area

                        #now lets create a row for this jam and add it to the output df
                        new_row = pd.DataFrame({"exp_name" : [exp_name], "flood" : [flood], "trans_reg" : [trans_reg], "fsd": [fsd], "jam": [jam], 
                                                "centroid_x": [centroid_x], "centroid_y": [centroid_y],
                                                "ch_jam_area":[ch_jam_area], "fp_jam_area": [fp_jam_area], "frac_area_in_ch": [frac_area_in_ch], "jam_area": [jam_area],"ch_jam_vol": [ch_jam_vol], "fp_jam_vol": [fp_jam_vol], "frac_vol_in_ch": [frac_vol_in_ch], "jam_vol": jam_vol})

                        jam_data_df = pd.concat([jam_data_df, new_row], ignore_index=True)

#export dataframe
out_fn = outpath + "/low_flood_jams_with_volumes.csv"

jam_data_df.to_csv(out_fn)