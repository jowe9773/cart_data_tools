import pandas as pd
from functions import FileFunctions
from functions import PlottingFunctions

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


#lets add columns for abs_uncert for est_wood_vol
nlfj_df["abs_uncert_wood_volume"] = nlfj_df["est_wood_volume"]* nlfj_df["rel_uncert"]
lfj_df["abs_uncert_wood_volume"] = lfj_df["est_wood_volume"] * lfj_df["rel_uncert"]

#lets add columns for abs_uncert_fp_wood_vol
nlfj_df["abs_uncert_fp_wood_volume"] = nlfj_df["est_fp_wood_volume"]* nlfj_df["rel_uncert"]
lfj_df["abs_uncert_fp_wood_volume"] = lfj_df["est_fp_wood_volume"] * lfj_df["rel_uncert"]

#lets add columns for abs_uncert_ch_wood_vol
nlfj_df["abs_uncert_ch_wood_volume"] = nlfj_df["est_ch_wood_volume"]* nlfj_df["rel_uncert"]
lfj_df["abs_uncert_ch_wood_volume"] = lfj_df["est_ch_wood_volume"] * lfj_df["rel_uncert"]


#Lets reorganize the volume data by experiment
nlf_exp_df = nlfj_df.groupby("key", as_index = False).agg({"est_wood_volume": "sum", "abs_uncert_wood_volume": "sum", "est_fp_wood_volume": "sum", "abs_uncert_fp_wood_volume": "sum", "est_ch_wood_volume": "sum", "abs_uncert_ch_wood_volume": "sum"})
lf_exp_df = lfj_df.groupby("key", as_index = False).agg({"est_wood_volume": "sum", "abs_uncert_wood_volume": "sum", "est_fp_wood_volume": "sum", "abs_uncert_fp_wood_volume": "sum", "est_ch_wood_volume": "sum", "abs_uncert_ch_wood_volume": "sum"})

#okay now lets combine these two dataframes
all_exp_df = pd.concat([nlf_exp_df, lf_exp_df], ignore_index=True)

#and break up the key for future use
df_expanded = all_exp_df["key"].str.split("_", expand = True)
df_expanded. columns = ["exp_date", "exp_num", "flood_type", "fsd", "trans_reg"]
all_exp_df = all_exp_df.join(df_expanded)

#find the relative uncertainty of wood stayed
all_exp_df["all_wood_rel_uncert"] = all_exp_df["abs_uncert_wood_volume"] / all_exp_df["est_wood_volume"]
all_exp_df["fp_wood_rel_uncert"] = all_exp_df["abs_uncert_fp_wood_volume"] / all_exp_df["est_fp_wood_volume"]
all_exp_df["ch_wood_rel_uncert"] = all_exp_df["abs_uncert_ch_wood_volume"] / all_exp_df["est_ch_wood_volume"]

print(all_exp_df.columns)

#calculate the total volume of wood dropped
s_dropped = 462
i_dropped = 325
l_dropped = 86

s_volume = 11988
i_volume = 25559
l_volume = 58584

total_volume = s_dropped*s_volume + i_dropped*i_volume + l_dropped * l_volume

#create a column for retention capacity
all_exp_df["ret_cap"] = all_exp_df["est_wood_volume"] / total_volume

#create columns for retention capacity for floodplain and channel
all_exp_df["fp_ret_cap"] = all_exp_df["est_fp_wood_volume"] / total_volume
all_exp_df["ch_ret_cap"] = all_exp_df["est_ch_wood_volume"] / total_volume

#find abosolute uncertainty in retention capacity (for plotting purposes)
all_exp_df["abs_uncert_ret_cap"] = all_exp_df["ret_cap"] * all_exp_df["all_wood_rel_uncert"]
all_exp_df["abs_uncert_fp_ret_cap"] = all_exp_df["fp_ret_cap"] * all_exp_df["fp_wood_rel_uncert"]
all_exp_df["abs_uncert_ch_ret_cap"] = all_exp_df["ch_ret_cap"] * all_exp_df["ch_wood_rel_uncert"]

#now remove remobilization plots
#exps = all_exp_df[all_exp_df["flood_type"] != "R"]

pf.volume_bar_plots(all_exp_df, "exp_date", "ch_ret_cap", "abs_uncert_ch_ret_cap", "flood_type", color_map = "tab10", groupby_cols=["trans_reg", "fsd"])
