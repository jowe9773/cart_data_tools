#functions.py

"""Import packages and modules"""
import tkinter as tk
from tkinter import filedialog
from matplotlib import pyplot as plt
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
    