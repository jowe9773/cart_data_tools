import pandas as pd
from functions import FileFunctions, PlottingFunctions

#instantiate functions
ff = FileFunctions()
pf = PlottingFunctions()

#choose files
non_low_flood_jams_fn = ff.load_fn("Choose jams file for NON low floods")
low_flood_jams_fn = ff.load_fn("Choose jams file for low floods")

#load these files into pandas databases
nlfj_df = pd.read_csv(non_low_flood_jams_fn)
lfj_df = pd.read_csv(low_flood_jams_fn)

#lets change the flood type for "low floods" in the non low flood experiments to reflect what the data truly is: "remobilization"
condition = (nlfj_df["flood"] == "L")
matches = nlfj_df.loc[condition]
nlfj_df.loc[nlfj_df['exp_name'].isin(matches['exp_name']), 'flood'] = 'R'

#now lets add a key for each experiment that includes its name and the flood type, forest stand density, and transport regime
nlfj_df["key"] = nlfj_df["exp_name"] + "_" + nlfj_df["flood"] + "_" + nlfj_df["fsd"].astype(str) + "_" + nlfj_df["trans_reg"]
lfj_df["key"] = lfj_df["exp_name"] + "_" + lfj_df["flood"] + "_" + lfj_df["fsd"].astype(str) + "_" + lfj_df["trans_reg"]

#make one big dataframe now
jams_df = pd.concat([nlfj_df, lfj_df], ignore_index=True)

#remove remobilization data from the dataframe
#final_jams_df = jams_df[jams_df["flood"]!="R"]

#print(final_jams_df.columns)

#now lets run the plotting function
pf.plot_jam_size_dist(jams_df, "key", "est_wood_volume", "flood", color_map="tab10", groupby_cols = ["trans_reg", "fsd"])