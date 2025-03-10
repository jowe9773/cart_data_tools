import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

class PlottingFunctions():
    def __init__(self):
        print("Initialized plotting functions")

    def plot_jam_size_dist(self, data, boxplot_name, y_value):
        """
        This function plots box and whisker charts across up to three comparison variables. 
        The first comparison variable will be plotted in different colors on the same subplot.
        The second comparison variable will be plotted in different subplots across the same row.
        The third comparison variable will be plotted in different subplots across different columns.
        """

        #lets make labels by experiment name
        labels = data[boxplot_name].unique()
        print(labels)

        # Group by experiment name
        grouped_data = [data[data[boxplot_name] == label][y_value] for label in labels]

        # Create the boxplot
        fig, axs = plt.subplots(1, 1, figsize=(6, 6), squeeze=False)
        axs[0, 0].boxplot(grouped_data, tick_labels=labels)

        plt.show()




if __name__ == "__main__":
    #A simple dataset to practice with
    data = {
        "exp_name" : ["exp1", "exp1", "exp1", "exp1", "exp2", "exp2", "exp2", "exp2", "exp2"],
        "jam" : [1, 2, 3, 4, 1, 2, 3, 4, 5],
        "jam_vol" : [10, 100, 34, 2, 15, 200, 347, 24, 17]
        }
    
    df = pd.DataFrame(data)
    print(df)


    #instantiate class
    pf = PlottingFunctions()
    pf.plot_jam_size_dist(df, "exp_name", "jam_vol")
