import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from functions import FileFunctions


bin_number = 10
x_variable = "jam_vol"

#instantiate classes
ff = FileFunctions()


#load jam info for all jams from all experiments
wood_poly_fn = ff.load_fn("Choose jam info layer", [("csv files", "*.csv")])
jams = pd.read_csv(wood_poly_fn)


#add porosity values for each jam
jams["porosity"] = 1 - (jams["wood_volume"]/jams["jam_vol"])
print(jams)

# Create 10 quantile-based bins for 'jam_vol' (each bin has ~equal number of points)
jams['jam_vol_bin'] = pd.qcut(jams[f'{x_variable}'], q=bin_number, labels=False)  # Labels 0 to 9

# Compute mean and standard deviation of 'porosity' for each 'jam_vol' bin
bin_stats = jams.groupby('jam_vol_bin')['porosity'].agg(['mean', 'std', "sem"]).reset_index()

bin_stats["CI_95"] = 1.95*bin_stats["sem"]
bin_stats["Rel_Uncertainty"] = bin_stats["CI_95"]/bin_stats["mean"]

print("Bin Stats: ", bin_stats)


#find minimum and maximum bound for each bin (i.e. find the boundaires of the bins)
min_max_values = jams.groupby('jam_vol_bin')[f"{x_variable}"].agg(['min', 'max']).reset_index()

# Get bin centers for plotting
min_max_values["center"] = (min_max_values["max"] + min_max_values["min"]) / 2

# Print the min and max values for each bin
print(min_max_values)


for i, row in bin_stats.iterrows():
    final_row = len(bin_stats) - 1
    if i == 0:
        min_vol = 0
        max_vol = min_max_values.iloc[i+1]["min"]

    elif i == final_row:
        min_vol = min_max_values.iloc[i]["min"]
        max_vol = 1000000000000000

    else:
        min_vol = min_max_values.iloc[i]["min"]
        max_vol = min_max_values.iloc[i+1]["min"]

    bin_stats.loc[i, "min_vol"] = min_vol
    bin_stats.loc[i, "max_vol"] = max_vol



print(bin_stats)

# Plot scatter plot of all data points
plt.figure(figsize=(8, 6))
plt.scatter(jams[f"{x_variable}"], jams['porosity'], alpha=0.5, label="Jams", color='gray')

# Plot mean porosity with error bars at bin centers
plt.errorbar(min_max_values["center"], bin_stats['mean'], yerr=bin_stats['sem']*1.96, fmt='o', capsize=5, color='red', label="Local Mean ± 95% CI")

# Add vertical lines at bin edges
for i, row in min_max_values.iterrows():
    plt.axvline(row["min"], color='blue', linestyle='--', linewidth=1, label="Min Bin Edge")


# Labels and title
plt.xscale("log")
plt.xlabel(f"{x_variable}")
plt.ylabel('Porosity')
plt.title(f'Porosity vs {x_variable} with Binned Statistics')
plt.legend()
plt.grid(True)

# Show plot
plt.show()

#now lets save the bin stats to a csv to use later
outpath = ff.load_dn("choose an output path")
bin_stats.to_csv(outpath + "/porosity_estimates.csv")