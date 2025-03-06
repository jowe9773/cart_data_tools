import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functions import FileFunctions

#instantiate classes
ff = FileFunctions()

exp_type = "low"
#load jam info for all jams from all experiments
wood_poly_fn = ff.load_fn("Choose jam info layer", [("csv files", "*.csv")])
jams = pd.read_csv(wood_poly_fn)

#load porosity estimates
porosity_estimates_fn = ff.load_fn("Choose porosity estimates file", [("csv files", "*.csv")])
porosity_estimates = pd.read_csv(porosity_estimates_fn)


print(jams)
print(porosity_estimates)

for i, row in jams.iterrows():
    #assign a porosity value and relative error based on the size of the jam
    jam_vol = row["jam_vol"]

    condition = (porosity_estimates["min_vol"] <= jam_vol) & (porosity_estimates["max_vol"] >= jam_vol)
    condition_match = porosity_estimates.loc[condition]
    print("Condition Matches: ", condition_match)

    jams.loc[i, "porosity"] = condition_match.iloc[0]["mean"]
    jams.loc[i, "rel_uncert"] = condition_match.iloc[0]["Rel_Uncertainty"]


print(jams)

#now lets find volumes 
jams["est_wood_volume"] = jams["jam_vol"]* (1- jams["porosity"])

print(jams)

#now lets save this information to a csv
#now lets save the bin stats to a csv to use later
outpath = ff.load_dn("choose an output path")
jams.to_csv(outpath + "/" + exp_type + "_jam_wood_vol_estimates.csv")