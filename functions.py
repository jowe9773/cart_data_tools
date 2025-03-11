#functions.py

"""Import packages and modules"""
import tkinter as tk
from tkinter import filedialog
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from osgeo import gdal, ogr, osr
import geopandas as gpd
from shapely.geometry import Point
from scipy.spatial.distance import cdist
import os

"""Now for the classes"""
class FileFunctions:
    """Class contains methods for managing files"""

    def __init__(self):
        print("Initialized file managers")

    def load_dn(self, purpose):
        """this function opens a tkinter GUI for selecting a 
        directory and returns the full path to the directory 
        once selected
        
        'purpose' -- provides expanatory text in the GUI
        that tells the user what directory to select"""

        root = tk.Tk()
        root.withdraw()
        directory_name = filedialog.askdirectory(title = purpose)

        return directory_name

    def load_fn(self, purpose, types = [("All files", "*.*")]):
        """this function opens a tkinter GUI for selecting a 
        file and returns the full path to the file 
        once selected
        
        'purpose' -- provides expanatory text in the GUI
        that tells the user what file to select
        
        'filetypes' -- allows you to select particular file types to look for"""

        root = tk.Tk()
        root.withdraw()
        filename = filedialog.askopenfilename(title = purpose, filetypes = types)

        return filename
    
    def extract_info_from_filename(self, filepath):
        directory, filename = os.path.split(filepath)
        basename = filename.split("_centroids")[0]
        exp = basename.split("_")[0] + "_" + basename.split("_")[1]

        #print(directory)
        #print("Basename: ", basename)
        #print("Experiment: ", exp)

        return directory, basename, exp
    
    def find_files_with_string(self, root_dir, search_string, filetype):
        files = []
        for dirpath, _, filenames in os.walk(root_dir):
            for file in filenames:
                if search_string in file and file.endswith(filetype):
                    files.append(os.path.join(dirpath, file))
        return files
    
    def sort_scans_chronologically(self, file_list):
        # Predefined order of scan types
        scan_order = ["nowood", "wood", "remobilization", "pre", "post"]

        # Function to extract sorting keys
        def extract_sort_key(filepath):
            # Get the filename without the path or extension
            filename = os.path.basename(filepath)
            filename = os.path.splitext(filename)[0]  # Remove the extension
            
            # Split the filename to extract parts
            parts = filename.split('_')
            date = parts[0]  # First part is the date
            experiment = parts[1]  # Second part is the experiment (e.g., exp1)
            scan_type = parts[2]  # Third part is the scan type
            
            # Extract date as an integer (for chronological ordering)
            date_key = int(date)
            
            # Extract experiment number (e.g., exp1 -> 1)
            exp_num = int(experiment.replace("exp", ""))
            
            # Extract scan type position from predefined order
            scan_type_key = scan_order.index(scan_type)
            
            return (date_key, exp_num, scan_type_key)

        # Sort the file list using the sorting key
        sorted_file_list = sorted(file_list, key=extract_sort_key)

        return sorted_file_list
    
    def csv_to_shp_WSE(self, wse_file, output_location):
        #load points into a dataframe
        points_df = gpd.read_file(wse_file) 

        #convert to a geoddataframe
        points_gdf = gpd.GeoDataFrame(
            points_df,
            geometry=gpd.points_from_xy(points_df.X, points_df.Y),  # Replace 'x' and 'y' with your column names
            crs="EPSG:32615"  # Set the CRS to UTM Zone 15N
        )

        #save geodataframe as shapefile
        points_gdf.to_file(output_location + "/"+ os.path.basename(wse_file), driver="ESRI Shapefile")

class PlottingFunctions:
    def __innit__(self):
        print("Initialized Plotting Functions")

    def volume_bar_plots(self, data, bar_name, y_value, y_error, comparison_var_1, color_map='hot', groupby_cols=None):
        """
        This function plots bar charts across up to three comparison variables. 
        The first comparison variable will be plotted in different colors on the same subplot.
        The second comparison variable will be plotted in different subplots across the same row.
        The third comparison variable will be plotted in different subplots across different columns.
        """

        def set_colormap(data, comparison_var_1, color_map):
            unique_vals_comp_1 = sorted(data[comparison_var_1].unique())
            colormap = plt.get_cmap(color_map, len(unique_vals_comp_1))  
            norm = mcolors.Normalize(vmin=0, vmax=len(unique_vals_comp_1) - 1)
            return {value: colormap(norm(i)) for i, value in enumerate(unique_vals_comp_1)}

        def plot_subplot(ax, subset, bar_name, y_value, y_error, comparison_var_1, unique_color_map, y_min, y_max):
            bar_width = 0.3
            bar_positions = range(len(subset))

            for k, (b_n, y_val, y_err, comp_val_1) in enumerate(zip(subset[bar_name], subset[y_value], subset[y_error], subset[comparison_var_1])):
                ax.bar(bar_positions[k], y_val, width=bar_width, color=unique_color_map[comp_val_1], yerr=y_err, capsize=5)

            ax.set_xticks(bar_positions)
            ax.set_xticklabels(subset[bar_name], rotation=45, ha="right")

            ax.set_ylim(y_min, y_max)

        # Step 1: Choose a colormap
        unique_color_map = set_colormap(data, comparison_var_1, color_map)

        global_y_min = (data[y_value] - data[y_error]).min()  # Minimum considering error bars
        global_y_max = (data[y_value] + data[y_error]).max()  # Maximum considering error bars

        if not groupby_cols:
            fig, ax = plt.subplots(1, 1, squeeze=False)
            plot_subplot(ax[0, 0], data, bar_name, y_value, y_error, comparison_var_1, unique_color_map, global_y_min, global_y_max)

        elif len(groupby_cols) == 1:
            width = len(data[groupby_cols[0]].unique())  # Number of unique categories

            fig, axs = plt.subplots(1, width, squeeze=False, figsize=(width*5, 5))

            grouped = data.groupby(groupby_cols[0])
            unique_cats = sorted(data[groupby_cols[0]].unique(), key=str)

            for column, category in enumerate(unique_cats):
                subset = grouped.get_group(category)
                print(f"Plotting: {category} at column {column}")
                plot_subplot(axs[0, column], subset, bar_name, y_value, y_error, comparison_var_1, unique_color_map, global_y_min, global_y_max)
                axs[0, column].set_title(f"{groupby_cols[0]}: {category}", fontsize=14, fontweight="bold")
            
        else:
            unique_cats = sorted(data[groupby_cols[0]].unique())  
            unique_subcats = sorted(data[groupby_cols[1]].unique())  

            height, width = len(unique_cats), len(unique_subcats)
            fig, axs = plt.subplots(height, width, squeeze=False, figsize=(width * 5, height * 5))

            grouped = data.groupby(groupby_cols)

            for (category, subcategory), subset in grouped:
                row, col = unique_cats.index(category), unique_subcats.index(subcategory)
                plot_subplot(axs[row, col], subset, bar_name, y_value, y_error, comparison_var_1, unique_color_map, global_y_min, global_y_max)

            # Add column titles
            for col, subcategory in enumerate(unique_subcats):
                axs[0, col].set_title(f"{groupby_cols[1]}: {subcategory}", fontsize=14, fontweight="bold")

            # Add row labels
            for row, category in enumerate(unique_cats):
                axs[row, 0].annotate(f"{groupby_cols[0]}: {category}", xy=(-0.4, 0.5), xycoords='axes fraction',
                                     fontsize=14, fontweight="bold", ha="right", va="center", rotation=90)

        handles = [plt.Line2D([0], [0], color=unique_color_map[value], lw=6, label=value) for value in unique_color_map]
        fig.legend(handles=handles, loc='upper right')

        #plt.tight_layout()
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.1, top=0.9, wspace=0.3, hspace=0.4)
        plt.show()

    def plot_jam_size_dist(self, data, boxplot_name, y_value, comparison_var_1, color_map = "tab10", groupby_cols=False):
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
            labels = subset[boxplot_name].unique()
            colors = []

            for i, label in enumerate(labels):
                subset_rows = subset[subset[boxplot_name] == label]
                if subset_rows.empty:
                    print(f"Warning: No data found for label {label} in subset.")
                    continue

                comp_var = subset_rows.iloc[0][comparison_var_1]
                
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

        elif len(groupby_cols) == 1:
            width = len(data[groupby_cols[0]].unique())  # Number of unique categories

            fig, axs = plt.subplots(1, width, squeeze=False, figsize=(width*5, 5))

            grouped = data.groupby(groupby_cols[0])
            unique_cats = sorted(data[groupby_cols[0]].unique(), key=str)

            for column, category in enumerate(unique_cats):
                subset = grouped.get_group(category)
                print(f"Plotting: {category} at column {column}")
                plot_subplot(axs[0, column], subset, boxplot_name, global_y_min, global_y_max, comparison_var_1, unique_color_map)
                axs[0, column].set_title(f"{groupby_cols[0]}: {category}", fontsize=14, fontweight="bold")
            
        else:
            unique_cats = sorted(data[groupby_cols[0]].unique())  
            unique_subcats = sorted(data[groupby_cols[1]].unique())  

            height, width = len(unique_cats), len(unique_subcats)
            fig, axs = plt.subplots(height, width, squeeze=False, figsize=(width * 5, height * 5))

            grouped = data.groupby(groupby_cols)

            for (category, subcategory), subset in grouped:
                row, col = unique_cats.index(category), unique_subcats.index(subcategory)
                plot_subplot(axs[row, col], subset, boxplot_name, global_y_min, global_y_max, comparison_var_1, unique_color_map)

            # Add column titles
            for col, subcategory in enumerate(unique_subcats):
                axs[0, col].set_title(f"{groupby_cols[1]}: {subcategory}", fontsize=14, fontweight="bold")

            # Add row labels
            for row, category in enumerate(unique_cats):
                axs[row, 0].annotate(f"{groupby_cols[0]}: {category}", xy=(-0.4, 0.5), xycoords='axes fraction',
                                     fontsize=14, fontweight="bold", ha="right", va="center", rotation=90)

        handles = [plt.Line2D([0], [0], color=unique_color_map[value], lw=6, label=value) for value in unique_color_map]
        fig.legend(handles=handles, loc='upper right')

        #plt.tight_layout()
        plt.subplots_adjust(left=0.15, right=0.9, bottom=0.1, top=0.9, wspace=0.3, hspace=0.4)
        plt.show()

class FindCentersFunctions:
    def __init__(self):
        print("Initialized Find Centers Functions")

    def load_raster(self, input_raster):
        with rasterio.open(input_raster) as src:
            elevation = src.read(1, resampling=Resampling.bilinear)
            transform = src.transform
            epsg_code = src.crs.to_epsg()
            raster_info = [elevation, transform, epsg_code]
        
        return raster_info

    def calculate_slope(self, elevation_array, transform):
        x, y = np.gradient(elevation_array, transform[0], transform[4])
        slope = np.sqrt(x**2 + y**2)
        slope_degrees = np.arctan(slope) * (180 / np.pi)
        return slope_degrees

    def mask_by_slope(self, slope_data, threshold, replace_with_one=False):
        if replace_with_one:
            return np.where(slope_data > threshold, 1, np.nan)
        else:
            return np.where(slope_data > threshold, slope_data, np.nan)

    def polygonize_mask(self, mask_array, transform, epsg_code, output_shapefile):
        driver = gdal.GetDriverByName("GTiff")
        temp_raster = "temp_mask.tif"
        
        with driver.Create(temp_raster, mask_array.shape[1], mask_array.shape[0], 1, gdal.GDT_Byte) as dst:
            dst.SetGeoTransform(transform.to_gdal())
            dst.SetProjection(f"EPSG:{epsg_code}")
            dst.GetRasterBand(1).WriteArray(mask_array)
            dst.GetRasterBand(1).SetNoDataValue(0)
            
            src_band = dst.GetRasterBand(1)
            srs = osr.SpatialReference()
            srs.ImportFromEPSG(epsg_code)
            
            driver = ogr.GetDriverByName("ESRI Shapefile")
            vector_dst = driver.CreateDataSource(output_shapefile)
            layer = vector_dst.CreateLayer("polygons", srs=srs, geom_type=ogr.wkbPolygon)
            field_defn = ogr.FieldDefn("value", ogr.OFTInteger)
            layer.CreateField(field_defn)
            
            gdal.Polygonize(src_band, src_band, layer, 0, [], callback=None)
            
            vector_dst.Destroy()

    def filter_by_area(self, geodataframe, min_area, max_area, output_shapefile):
        filtered_gdf = geodataframe[(geodataframe['area'] >= min_area) & (geodataframe['area'] <= max_area)]
        filtered_gdf.to_file(output_shapefile)
        return filtered_gdf

    def create_bounding_circles(self, geodataframe, output_shapefile):

        def minimum_bounding_circle(polygon):
            centroid = polygon.centroid
            radius = max(centroid.distance(Point(coords)) for coords in polygon.exterior.coords)
            return centroid.buffer(radius)

        geodataframe['min_bounding_circle'] = geodataframe.geometry.apply(minimum_bounding_circle)
        circle_gdf = gpd.GeoDataFrame(geodataframe[['min_bounding_circle']], geometry='min_bounding_circle', crs=geodataframe.crs)
        circle_gdf.to_file(output_shapefile)
        print("Minimum bounding circle shapefile created:", output_shapefile)

    def calculate_centroids(self, geodataframe, output_shapefile):
        geodataframe['centroid'] = geodataframe.geometry.centroid
        centroid_gdf = gpd.GeoDataFrame(geodataframe[['centroid']], geometry='centroid', crs=geodataframe.crs)
        centroid_gdf.to_file(output_shapefile)
        print("Centroid shapefile created:", output_shapefile)

    def find_centers(self, sick_filename, out_directory):
        scan = self.load_raster(sick_filename)
        out_filename_no_suffix = out_directory + "/" + sick_filename.split(".")[0].split("/")[-1]

        #process to find center of holes on floodplain
        #find slope
        slope = self.calculate_slope(scan[0], scan[1])

        #mask slope so only areas of slopes greater than 50 are saved
        high_slope_mask = self.mask_by_slope(slope, 50, False)

        #find the slope of the mask to find the edges of the high slope areas
        slope_of_high_slope_mask = self.calculate_slope(np.nan_to_num(high_slope_mask, nan=0), scan[1])

        #mask to only find areas of high slope change
        final_mask = self.mask_by_slope(slope_of_high_slope_mask, 20, True).astype(np.uint8)

        #convert to polygons
        polygons_file = out_filename_no_suffix + "_polygons.shp"
        self.polygonize_mask(final_mask, scan[1], scan[2], polygons_file)

        #filter polygons to a particular size
        gdf = gpd.read_file(polygons_file)
        gdf['area'] = gdf.geometry.area
        filtered_gdf = self.filter_by_area(gdf, 100, 400, polygons_file)

        #find bounding circles of the filtered polygons
        bounding_circles_file = out_filename_no_suffix + "_bounding_circles.shp"
        self.create_bounding_circles(filtered_gdf, bounding_circles_file)

        #filter bounding circles to a particular size (same range as polygons)
        gdf = gpd.read_file(bounding_circles_file)
        print(gdf)
        gdf['area'] = gdf.geometry.area
        filtered_gdf = self.filter_by_area(gdf, 100, 400, bounding_circles_file)

        #find centroids of bounding circles
        centroids_file = out_filename_no_suffix + "_centroids.shp"
        self.calculate_centroids(filtered_gdf, centroids_file)


class FindPairsFunctions:

    def __init__(self):
        print("Initialized FindPairFunctions")

    def find_closest_pairs(self, scan1, scan2):
        shapefile_1 = gpd.read_file(scan1)
        shapefile_2 = gpd.read_file(scan2)

        # Ensure both shapefiles use the same CRS
        if shapefile_1.crs != shapefile_2.crs:
            print("CRS does not match")
            shapefile_2 = shapefile_2.to_crs(shapefile_1.crs)

        # Extract the points (coordinates) from both shapefiles
        points_1 = shapefile_1.geometry.apply(lambda x: (x.x, x.y)).tolist()
        points_2 = shapefile_2.geometry.apply(lambda x: (x.x, x.y)).tolist()

        # Step 3: Calculate pairwise distances between points
        distances = cdist(points_1, points_2)

        # Find the closest point pairs
        closest_pairs = []
        for i in range(len(points_1)):
            closest_index = distances[i].argmin()
            closest_pairs.append((points_1[i], points_2[closest_index]))

        return closest_pairs
    
    def calculate_offsets(self, closest_pairs):
        # Prepare lists to store the x and y offsets
        x_offsets = []
        y_offsets = []


        # Calculate the offsets (x_offset and y_offset) for each pair and store them
        for pair in closest_pairs:
            point1 = pair[0]
            point2 = pair[1]

            # Calculate the offset (difference) in x and y coordinates
            x_offset = point2[0] - point1[0]
            y_offset = point2[1] - point1[1]

            x_offsets.append(x_offset)
            y_offsets.append(y_offset)

        # Combine the offsets into a 2D array
        offsets = np.array(list(zip(x_offsets, y_offsets)))

        return offsets

    def select_true_offsets(self, offsets, low_threshold = 0, high_threshold = 30):
        
        # Use boolean indexing to filter pairs
        filtered_offsets = offsets[(np.abs(offsets[:, 0]) <= high_threshold) & (np.abs(offsets[:, 1]) <= high_threshold) & (np.abs(offsets[:, 0]) >= low_threshold) & (np.abs(offsets[:, 1]) >= low_threshold)]

        return filtered_offsets

    def compute_median_direction_and_distance(self, offsets):
        x_values = offsets[:, 0].tolist()  # First column (x values)
        y_values = offsets[:, 1].tolist()  # Second column (y values)

        # Step 1: Calculate the Euclidean distances for each (x, y) pair
        distances = np.sqrt(np.array(x_values)**2 + np.array(y_values)**2)
        
        # Step 2: Calculate the angles (in radians) for each (x, y) pair
        angles = np.arctan2(y_values, x_values)
        
        # Step 3: Convert angles to degrees
        angles_degrees = np.degrees(angles)
        
        # Step 4: Compute the median angle (direction) in degrees
        median_angle = np.median(angles_degrees)
        
        # Step 5: Compute the median distance
        median_distance = np.median(distances)

        new_median_direction = float(median_angle)
        new_median_distance = float(median_distance)
        
        return new_median_direction, new_median_distance
    
    def find_median_offset_from_scans(self, scan1, scan2):
        print("Scan1: ", scan1)
        print("Scan2: ", scan2)

        if scan1 == None or scan2 == None:
            print("One or more scans are messed up. If you thiknk this is wrong check over your files. ")
            median_direction = np.nan
            median_distance = np.nan
        
        else:

            pairs = self.find_closest_pairs(scan1, scan2)
            offsets = self.calculate_offsets(pairs)
            true_offsets = self.select_true_offsets(offsets)
            median_direction, median_distance = self.compute_median_direction_and_distance(true_offsets)

        return median_direction, median_distance
    