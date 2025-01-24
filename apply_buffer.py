"""Load packages and modules"""
import os
from osgeo import gdal
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from functions import FileFunctions, FindCentersFunctions

class ApplyBuffer:
    def __init__(self):
        gdal.UseExceptions()
        print("Initialized Apply Buffer")


    def apply_buffer(self, input_sick, buffer_dst, wse_file):

        """Instantiate classes"""
        fcf = FindCentersFunctions()

        """Create temporary and final filenames"""
        polygons_file = buffer_dst + "/" + os.path.basename(input_sick).split(".")[0] + "_polygons.shp"

        filtered_polygons_file = buffer_dst + "/" + os.path.basename(input_sick).split(".")[0] + "_filtered_polygons.shp"

        """Create buffer from sick file"""

        sick_info = fcf.load_raster(input_sick)

        sick_slope = fcf.calculate_slope(sick_info[0], sick_info[1])

        mask = fcf.mask_by_slope(sick_slope, 40, replace_with_one=True)

        fcf.polygonize_mask(mask, sick_info[1], sick_info[2], polygons_file)

        polygons_gdf = gpd.read_file(polygons_file)

        polygons_gdf["area"] = polygons_gdf.geometry.area

        filtered_gdf = polygons_gdf[(polygons_gdf['area'] >= 20) & (polygons_gdf['area'] <= 250000)]

        #create buffer around filtered polygons
        buffer_width = 12 #in mm

        #Apply the buffer with a width of 12 units
        filtered_gdf['buffered'] = filtered_gdf.geometry.buffer(buffer_width)

        #Dissolve the buffers to merge overlapping areas
        dissolved_geom = filtered_gdf['buffered'].union_all()

        #Convert the dissolved geometry back into a GeoDataFrame
        dissolved_gdf = gpd.GeoDataFrame(geometry=[dissolved_geom], crs=filtered_gdf.crs)

        # Save or use the resulting GeoDataFrame
        dissolved_gdf.to_file(buffer_dst + "/" + os.path.basename(input_sick).split(".")[0] + "_buffer.shp")

        """Remove the intermediate files"""
        #list basenames
        basenames = [polygons_file.split(".")[0], filtered_polygons_file.split(".")[0]]

        #list file extensions
        file_extensions = [".cpg", ".dbf", ".prj", ".shp", ".shx"]

        #iterate through lists and remove these files

        for i, ext in enumerate(file_extensions):
            file_to_remove = polygons_file.split(".")[0]+ext
            try:
                os.remove(file_to_remove)
            except:
                print(f"{file_to_remove} does not exist, so does not need to be removed.")

        """Apply buffer to WSE data"""
        # Load the points and polygons shapefiles
        points_df = gpd.read_file(wse_file) 
        polygons_gdf = gpd.read_file(buffer_dst + "/" + os.path.basename(input_sick).split(".")[0] + "_buffer.shp")  

        # Convert the DataFrame to a GeoDataFrame
        # Convert the DataFrame to a GeoDataFrame using x and y columns
        points_gdf = gpd.GeoDataFrame(
            points_df,
            geometry=gpd.points_from_xy(points_df.X, points_df.Y),  # Replace 'x' and 'y' with your column names
            crs="EPSG:32615"  # Set the CRS to UTM Zone 15N
        )

        # Ensure CRS matches between points and polygons
        if points_gdf.crs != polygons_gdf.crs:
            polygons_gdf = polygons_gdf.to_crs(points_gdf.crs)

        # Perform the spatial query: Find points NOT in polygons
        points_outside_polygons = points_gdf[~points_gdf.geometry.apply(
            lambda point: polygons_gdf.contains(point).any()
        )]

        # Save the filtered points to a new shapefile
        points_outside_polygons.to_file(buffer_dst + "/"+ os.path.basename(wse_file), driver="ESRI Shapefile")


if __name__ == "__main__":
    ff = FileFunctions()
    ab = ApplyBuffer()

    """Load sick file for buffer generation"""
    input_sick_file = ff.load_fn("Load input file to create buffer from", [("Geotiffs", "*.TIF"), ("All Files", "*.*")])
    buffer_destination = ff.load_dn("Select a directory where buffer file and output WSE scans will go")
    wse_file = ff.load_fn("Select water surface elevation file", [("CSV files", ".CSV")])

    ab.apply_buffer(input_sick_file, buffer_destination, wse_file)
