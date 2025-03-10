import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from functions import FileFunctions

class PlottingFunctions():
    def __init__(self):
        print("Initialized plotting functions")

    def plot_jam_size_dist(self, data, boxplot_name, y_value, comparison_var_1, color_map = "hot", groupby_cols=False):
        """
        This function plots box and whisker charts across up to three comparison variables. 
        The first comparison variable will be plotted in different colors on the same subplot.
        The second comparison variable will be plotted in different subplots across the same row.
        The third comparison variable will be plotted in different subplots across different columns.
        """
        def set_colormap(data, comparison_var_1, color_map):
            unique_vals_comp_1 = sorted(data[comparison_var_1].unique())
            colormap = plt.get_cmap(color_map, len(unique_vals_comp_1))  
            norm = mcolors.Normalize(vmin=0, vmax=len(unique_vals_comp_1) - 1)
            return {value: colormap(norm(i)) for i, value in enumerate(unique_vals_comp_1)}
        
        def plot_subplot(ax, subset, boxplot_name, y_min, y_max, comparison_var_1, unique_color_map):

            print(f"subset data: {subset}")

            #lets make labels by experiment name
            labels = data[boxplot_name].unique()
            colors = []

            for i, label in enumerate(labels):
                comp_var = subset[subset[boxplot_name] == label].iloc[0][comparison_var_1]

                print(f"comp_var {comp_var}")
                
                color = unique_color_map[comp_var]
                
                print(label)
                print(color)

                colors.append(color)


            # Group by experiment name
            grouped_data = [subset[subset[boxplot_name] == label][y_value] for label in labels]
            
            #make a boxplot for each group of data
            bplot = ax.boxplot(grouped_data,patch_artist=True)
            
            #set the labels and the y axis extent
            ax.set_xticklabels(labels, rotation=45, ha="right")
            ax.set_ylim(y_min, y_max)
            
            #color the boxes according to the comparison variable 1 and the colormap
            for patch, color in zip(bplot['boxes'], colors):
                
                patch.set_facecolor(color)

        # Step 1: Choose a colormap
        unique_color_map = set_colormap(data, comparison_var_1, color_map)
        print("Unique Color Map")
        print(unique_color_map)


        global_y_min = data[y_value].min()  # Minimum considering error bars
        global_y_max = data[y_value].max()  # Maximum considering error bars

        if not groupby_cols:
            fig, axs = plt.subplots(1, 1, squeeze=False)
            plot_subplot(axs[0,0], data, boxplot_name, global_y_min, global_y_max, comparison_var_1, unique_color_map)

        

        plt.show()




if __name__ == "__main__":
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
    final_jams_df = jams_df[jams_df["flood"]!="R"]

    #now lets run the plotting function
    pf.plot_jam_size_dist(final_jams_df, "key", "est_wood_volume", "flood")