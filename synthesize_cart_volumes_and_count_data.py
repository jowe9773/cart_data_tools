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

#lets find the wood volume of each jam
s_volume = 11988
i_volume = 25559
l_volume = 58584

count_data_df["wood_volume (mm^3)"] = count_data_df["s_tot"]*s_volume + count_data_df["i_tot"]*i_volume + count_data_df["l_tot"]*l_volume


#lets get the output_jam file setup
jam_data_df = gpd.GeoDataFrame(columns = ["exp_name", "flood", "trans_reg", "fsd", "jam", 
                                    "centroid_x", "centroid_y",
                                    "s_tot", "i_tot", "l_tot", "all", "wood_volume", 
                                    "ch_jam_area", "fp_jam_area", "frac_area_in_ch", "jam_area","ch_jam_vol", "fp_jam_vol", "frac_vol_in_ch", "jam_vol"])


for i, row in count_data_df.iterrows():
    
    #get info from count data df
    exp_name = row["exp_name"]
    flood = row["flood"]
    trans_reg = row["trans_reg"]
    fsd = row["fsd"]
    jam = row["jam"]
    s_tot = row["s_tot"]
    i_tot = row["i_tot"]
    l_tot = row["l_tot"]
    full_count = row["all"]
    wood_volume = row["wood_volume (mm^3)"]

    #lets load the files associated with this row
    exp_folder = root_folder + "/" + exp_name
    remote_jam_volumes_wood_fn = ff.find_files_with_string(exp_folder, "-wood_volumes", ".shp")
    remote_jam_volumes_remobilized_fn = ff.find_files_with_string(exp_folder, "-remobilized_wood_volumes", ".shp")
    wood_centroids = ff.find_files_with_string(exp_folder, "wood_centroids", ".shp")
    remobilized_centroids = ff.find_files_with_string(exp_folder, "remobilized_centroids", ".shp")

    if "20240805" not in exp_name and "20240807" not in exp_name and "20240714" not in exp_name:

        if len(remote_jam_volumes_remobilized_fn) <= 0 and len(remote_jam_volumes_wood_fn) >= 1:
            #load wood jam volumes and centroids
            jam_volumes = gpd.read_file(remote_jam_volumes_wood_fn[0])
            jam_centroids = gpd.read_file(wood_centroids[0])

            #now lets extract the information we want from the centroids file
            condition = (jam_centroids['jam'] == jam)
            match = jam_centroids.loc[condition]

            centroid_x = match.geometry.x.values[0]
            centroid_y = match.geometry.y.values[0]

            #now lets get the info we want from the jam volumes file
            floodplain = (jam_volumes['jam'] == jam) & (jam_volumes["Channel?"] == 0)
            floodplain_match = jam_volumes.loc[floodplain]
            
            channel = (jam_volumes['jam'] == jam) & (jam_volumes["Channel?"] == 1)
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
                                    "s_tot": [s_tot], "i_tot": [i_tot], "l_tot": [l_tot], "all" : [full_count], "wood_volume": [wood_volume], 
                                    "ch_jam_area":[ch_jam_area], "fp_jam_area": [fp_jam_area], "frac_area_in_ch": [frac_area_in_ch], "jam_area": [jam_area],"ch_jam_vol": [ch_jam_vol], "fp_jam_vol": [fp_jam_vol], "frac_vol_in_ch": [frac_vol_in_ch], "jam_vol": jam_vol})

            jam_data_df = pd.concat([jam_data_df, new_row], ignore_index=True)

        if len(remote_jam_volumes_remobilized_fn) >= 1:
            #load remobilized jam volumes and centroids
            jam_volumes = gpd.read_file(remote_jam_volumes_remobilized_fn[0])
            jam_centroids = gpd.read_file(remobilized_centroids[0])

            #now lets extract the information we want from the centroids file
            condition = (jam_centroids['jam'] == jam)
            match = jam_centroids.loc[condition]

            centroid_x = match.geometry.x.values[0]
            centroid_y = match.geometry.y.values[0]


            #now lets get the info we want from the jam volumes file
            floodplain = (jam_volumes['jam'] == jam) & (jam_volumes["Channel?"] == 0)
            floodplain_match = jam_volumes.loc[floodplain]
            
            channel = (jam_volumes['jam'] == jam) & (jam_volumes["Channel?"] == 1)
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
                                    "s_tot": [s_tot], "i_tot": [i_tot], "l_tot": [l_tot], "all" : [full_count], "wood_volume": [wood_volume], 
                                    "ch_jam_area":[ch_jam_area], "fp_jam_area": [fp_jam_area], "frac_area_in_ch": [frac_area_in_ch], "jam_area": [jam_area],"ch_jam_vol": [ch_jam_vol], "fp_jam_vol": [fp_jam_vol], "frac_vol_in_ch": [frac_vol_in_ch], "jam_vol": jam_vol})

            jam_data_df = pd.concat([jam_data_df, new_row], ignore_index=True)


#export dataframe
out_fn = outpath + "/jams_with_volumes.csv"

jam_data_df.to_csv(out_fn)
