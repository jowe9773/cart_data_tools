import pandas as pd
from functions import FileFunctions
from testing import PlottingFunctions

#instantiate functions
ff = FileFunctions()
pf = PlottingFunctions()

#choose files
non_low_flood_jams_fn = ff.load_fn("Choose jams file for NON low floods")
low_flood_jams_fn = ff.load_fn("Choose jams file for low floods")

#load these files into pandas databases
nlfj_df = pd.read_csv(non_low_flood_jams_fn)
lfj_df = pd.read_csv(low_flood_jams_fn)

print(nlfj_df.columns)
print(lfj_df.columns)

#lets change the flood type for "low floods" in the non low flood experiments to reflect what the data truly is: "remobilization"
condition = (nlfj_df["flood"] == "L")
matches = nlfj_df.loc[condition]
nlfj_df.loc[nlfj_df['exp_name'].isin(matches['exp_name']), 'flood'] = 'R'

#now lets add a key for each experiment that includes its name and the flood type, forest stand density, and transport regime
nlfj_df["key"] = nlfj_df["exp_name"] + "_" + nlfj_df["flood"] + "_" + nlfj_df["fsd"].astype(str) + "_" + nlfj_df["trans_reg"]
lfj_df["key"] = lfj_df["exp_name"] + "_" + lfj_df["flood"] + "_" + lfj_df["fsd"].astype(str) + "_" + lfj_df["trans_reg"]

#make one big dataframe now
jams_df = pd.concat([nlfj_df, lfj_df], ignore_index=True)

print(jams_df.columns)
print(jams_df)

#remove remobilization data from the dataframe
final_jams_df = jams_df[jams_df["flood"]!="R"]

#now lets run the plotting function
pf.plot_jam_size_dist(final_jams_df, "key", "est_wood_volume")