#testing.py
import rasterio
import numpy as np
from rasterio.features import shapes
from rasterio.mask import mask
from shapely.geometry import shape, mapping
import fiona
import os
from fiona.crs import from_epsg
from matplotlib import pyplot as plt
import geopandas as gpd
import pandas as pd
from rasterio.warp import reproject, Resampling


class DetectChannelBottom:
    
    def __init__(self):
        print("Initialized detectchannelbottom")

    def plot_array(self, array, title="Array Plot"):
        # Plot the data
        plt.figure(figsize=(10, 6))
        plt.imshow(array, cmap='gray')
        plt.colorbar(label='Pixel Value')
        plt.title(title)
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")
        plt.show()

    def detrend_data(self, input_raster_file, export=False):
        with rasterio.open(input_raster_file) as src:
            profile = src.profile  # Get metadata
            data = src.read(1)  # Read the first band
            #plot_array(data, "Original Data")

            width = data.shape[1]

            # Create a trend surface
            x_trend = np.linspace(0, width - 1, width) * -0.01 + 377
            trend_surface = np.tile(x_trend, (data.shape[0], 1))

            #plot_array(trend_surface, "Trend Surface")

            # Apply detrending
            detrended_data = data - trend_surface
            #plot_array(detrended_data, "Detrended Data")

            #optional export detrended data as geotiff
            if export != False:
                with rasterio.open(export, 'w', **profile) as dst:
                    dst.write(detrended_data, 1)

            return detrended_data, profile
        
    def create_mask(self, raster_data, profile, threshold, export=False):
        mask = np.where((raster_data < threshold), 1, 0).astype('uint8')

        #optional export detrended data as geotiff
        if export != False:
            with rasterio.open(export, 'w', **profile) as dst:
                dst.write(mask, 1)
    
        return mask

    def polygonize_mask(self, mask, profile):
        # Convert raster to polygons
        polygons = []
        for geom, value in shapes(mask.astype(np.uint8), transform=profile["transform"]):
            if value == 1: 
                polygons.append(shape(geom))

        # Convert to GeoDataFrame
        gdf_1 = gpd.GeoDataFrame(geometry=polygons, crs=profile["crs"])
        gdf_1["DN"] = 1  # Assign DN = 1 to masked areas

        polygons = []
        for geom, value in shapes(mask.astype(np.uint8), transform=profile["transform"]):
            if value == 0: 
                polygons.append(shape(geom))

        # Convert to GeoDataFrame
        gdf_0 = gpd.GeoDataFrame(geometry=polygons, crs=profile["crs"])
        gdf_0["DN"] = 0  # Assign DN = 0 to unmasked areas 

        # Combine both GeoDataFrames
        polygons_gdf = gpd.GeoDataFrame(pd.concat([gdf_0, gdf_1], ignore_index=True))

        #calculate area of each row
        polygons_gdf["area"] = polygons_gdf.geometry.area

        return polygons_gdf

    def filter_polygons(self, polygons_gdf, in_DN, out_DN, max_area, export = False):
        """remove holes in the channel (falsely detected floodplain)"""
        polygons_gdf.loc[(polygons_gdf["DN"] == in_DN) & (polygons_gdf["area"] < max_area), "DN"] = out_DN

        gdf_dissolved = polygons_gdf.dissolve(by="DN", as_index=False)

        gdf_exploded = gdf_dissolved.explode(index_parts=False, as_index = False).reset_index(drop=True)

        #recalculate the area of each polygon
        gdf_exploded["area"] = gdf_exploded.geometry.area

        #if true, export polygons
        if export != False:
            gdf_exploded.to_file(export, driver="ESRI Shapefile")

        return gdf_exploded

    def detect_channel_bottom(self, input_raster, max_elev, channel = False, output_file = False):
        """detrend data"""
        detrended_raster, profile = self.detrend_data(input_raster)

        """mask detrended data to isolate channel bottom"""

        mask = self.create_mask(detrended_raster, profile, max_elev)

        """polygonize the mask"""
        polygons_gdf = self.polygonize_mask(mask, profile)

        """remove small areas of "channel" within the floodplain"""
        if channel == True:
            cleaned_fp_gdf = self.filter_polygons(polygons_gdf, 1,0,5000000)

        else:
            cleaned_fp_gdf = self.filter_polygons(polygons_gdf, 1,0,10000)

        """remove small areas of "floodplain" within the channel"""
        if output_file == False:
            cleaned_fp_and_channel_gdf = self.filter_polygons(cleaned_fp_gdf, 0, 1, 5000)

        else:    
            cleaned_fp_and_channel_gdf = self.filter_polygons(cleaned_fp_gdf, 0, 1, 5000, export = output_file)

        return cleaned_fp_and_channel_gdf
    
    def split_polygons_by_ch_fp(self, wood_polygons_fn, channel_polygons_fn, out_fn = False):
        #load wood polygons
        wood_polygons = gpd.read_file(wood_polygons_fn)


        #load channel polygons
        channel_polygons = gpd.read_file(channel_polygons_fn)

        # Perform overlay to get the intersection (overlapping area)
        overlapping_gdf = gpd.overlay(wood_polygons, channel_polygons, how="intersection")

        #create a new gdf with only the infos you want
        split_wood_gdf = overlapping_gdf.loc[:, ["jam", "piece", "piece_size", "DN_2", "geometry"]].copy()

        split_wood_gdf = split_wood_gdf.rename(columns={"DN_2" : "Channel?"})

        #lets deal with the individual pieces first
        ind_pieces_gdf = split_wood_gdf[split_wood_gdf["jam"] == 0]
        # Dissolve by "piece" and "channel"
        ind_dissolved_gdf = ind_pieces_gdf.dissolve(by=["piece", "Channel?"], as_index=False)

        #now lets deal with the jams
        jams_gdf = split_wood_gdf[split_wood_gdf["jam"] != 0]
        # Dissolve by "piece" and "channel"
        jams_dissolved_gdf = jams_gdf.dissolve(by=["jam", "Channel?"], as_index=False)

        #combnine the singles and jams into one gdf
        split_wood_gdf = gpd.GeoDataFrame(pd.concat([ind_dissolved_gdf, jams_dissolved_gdf], ignore_index=True))

        print("Ind pieces")
        print(ind_dissolved_gdf)

        print("Jams")
        print(jams_dissolved_gdf)

        print("combined")
        print(split_wood_gdf)


        if out_fn != False:
            print("saving wood polygons to file")
            split_wood_gdf.to_file(out_fn)

        return split_wood_gdf

    def calculate_centroids(self, polygons_layer_fn, out_fn = False):
        #load polygons
        polygons_gdf = gpd.read_file(polygons_layer_fn)

        #first lets deal with the jams
        jams_gdf = polygons_gdf[polygons_gdf["jam"] != 0]
        # Dissolve all polygons by "jam" (merging multiple pieces into one per jam)
        jams_dissolved_gdf = jams_gdf.dissolve(by="jam", as_index=False)

        jams_dissolved_gdf["geometry"] = jams_dissolved_gdf.geometry.centroid

        print("Jams centroids: ", jams_dissolved_gdf)


        #now lets deal with the individual pieces
        ind_gdf = polygons_gdf[polygons_gdf["jam"] == 0]

        # Dissolve all polygons by "jam" (merging multiple pieces into one per jam)
        ind_dissolved_gdf = ind_gdf.dissolve(by="piece", as_index=False)

        ind_dissolved_gdf["geometry"] = ind_dissolved_gdf.geometry.centroid

        print("individual piece centroids: ", ind_dissolved_gdf)


        #combnine the singles and jams into one gdf
        all_centroids_gdf = gpd.GeoDataFrame(pd.concat([ind_dissolved_gdf, jams_dissolved_gdf], ignore_index=True))
        print("All centroids: ", all_centroids_gdf)

        if out_fn != False:
            print("saving wood polygons to file")
            all_centroids_gdf.to_file(out_fn)

        return all_centroids_gdf


class CalculateVolume:

    def __init__(self):
        print("Initialized Calculate volume")
    
    def resample_raster(self, src_raster, target_raster_meta):
        """Resample the source raster to match the resolution and extent of the target raster."""
        src_data = src_raster.read(1)
        src_transform = src_raster.transform
        
        # Define the output array shape based on the target raster metadata
        out_shape = (target_raster_meta['height'], target_raster_meta['width'])
        
        # Create an empty array for the resampled data
        resampled_data = np.empty(out_shape, dtype=src_data.dtype)
        
        # Perform the reprojection/resampling
        reproject(
            source=src_data,
            destination=resampled_data,
            src_transform=src_transform,
            src_crs=src_raster.crs,
            dst_transform=target_raster_meta['transform'],
            dst_crs=target_raster_meta['crs'],
            resampling=Resampling.bilinear  # Use bilinear interpolation for smoother results
        )
        
        return resampled_data
    
    def detect_wood(self, before_path, after_path, output_location, channel_bottom_elev, remobilization = False):
        dcb = DetectChannelBottom()

        # 1. Load rasters
        with rasterio.open(before_path) as before, rasterio.open(after_path) as after:
            before_data = before.read(1)
            after_data = after.read(1)
            before_meta = before.meta
            after_meta = after.meta
            profile = after.profile  # Use the "after" raster as the reference

            # If the rasters do not perfectly match in space, resample the "before" raster
            if before_meta['transform'] != after_meta['transform'] or before_meta['width'] != after_meta['width'] or before_meta['height'] != after_meta['height']:
                print("Resampling 'before' raster to match 'after' raster...")
                before_data = self.resample_raster(before, after_meta)

        # 2. Difference the two TIFF files (after - before)
        difference = after_data - before_data

        # 3. Mask the difference layer
        mask = np.where((difference >= 6) & (difference < 150), 1, 0).astype('uint8')

         # 4. Polygonize the mask
        polygons = []
        with rasterio.open('mask.tif', 'w', **profile) as mask_tif:
            mask_tif.write(mask, 1)

            for geom, value in shapes(mask, mask=mask > 0, transform=mask_tif.transform):
                if value == 1:  # Include only valid areas
                    polygons.append(shape(geom))

        # 5. Remove polygons with DN of 0 and 6. Area less than 1000
        filtered_polygons = [poly for poly in polygons if poly.area >= 500]

        #6. Create geopandas database of polygons
        difference_wood_gdf = gpd.GeoDataFrame(geometry=filtered_polygons, crs=32615)


        # 7. Clean up geometries to remove erroneous features in channel 
        channel_bottom = dcb.detect_channel_bottom(after_path, channel_bottom_elev)

        #Find locations that are not channel bottom (0) that are within the difference wood polygons
        not_channel_bottom = channel_bottom[channel_bottom["DN"] == 0]

        # Perform overlay to get the intersection (overlapping area)
        overlapping_gdf = gpd.overlay(difference_wood_gdf, not_channel_bottom, how="intersection")

        #explode result
        gdf_exploded = overlapping_gdf.explode(index_parts=False, as_index = False).reset_index(drop=True)

        #calculate area of each row
        gdf_exploded["area"] = gdf_exploded.geometry.area


        if remobilization == True:
            gdf_exploded.to_file(output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "_true_wood_remobilization.shp", driver="ESRI shapefile")

        else:
            gdf_exploded.to_file(output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "_true_wood.shp", driver="ESRI shapefile")

    def calculate_volume(self, before_path, after_path, polygons_file, output_location, remobilization="N"):
        
        # 1. Load rasters
        with rasterio.open(before_path) as before, rasterio.open(after_path) as after:
            before_data = before.read(1)
            after_data = after.read(1)
            before_meta = before.meta
            after_meta = after.meta
            profile = after.profile  # Use the "after" raster as the reference

            # If the rasters do not perfectly match in space, resample the "before" raster
            if before_meta['transform'] != after_meta['transform'] or before_meta['width'] != after_meta['width'] or before_meta['height'] != after_meta['height']:
                print("Resampling 'before' raster to match 'after' raster...")
                before_data = self.resample_raster(before, after_meta)

        # 2. Difference the two TIFF files (after - before)
        difference = after_data - before_data

        # Save the difference layer as a GeoTIFF
        difference_path = output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "_difference.tif"
        with rasterio.open(difference_path, 'w', **profile) as dest:
            dest.write(difference, 1)

        # Load the polygons shapefile
        polygons = gpd.read_file(polygons_file)

        with rasterio.open(difference_path) as src:
        # Reproject polygons to match raster CRS if necessary
            if polygons.crs != src.crs:
                polygons = polygons.to_crs(src.crs)

            # Initialize an empty list to store sum of cells for each polygon
            sums = []

            # Loop through each polygon
            for _, row in polygons.iterrows():
                geom = [row.geometry]

                # Clip the raster to the current polygon
                out_image, out_transform = mask(src, geom, crop=True)
                out_image = out_image[0]  # Get the first band

                # Calculate the sum of all non-NaN cells within the clipped raster
                cell_sum = np.nansum(out_image[out_image != src.nodata])
                sums.append(cell_sum)

        # Add the sum as a new column to the GeoDataFrame
        polygons['cell_sum'] = sums

        # Check the column names to ensure "jam" and "cell_sum" exist
        print(polygons.columns)

        if 'jam' in polygons.columns and 'cell_sum' in polygons.columns:

            # Group by the "jam" attribute
            grouped = polygons.groupby("jam")

            # Combine polygons into a multipolygon and sum the "cell_sum" attribute
            combined = grouped.agg({
                "geometry": lambda x: x.unary_union,  # Combine geometries into a multipolygon
                "cell_sum": "sum"                    # Sum the "cell_sum" values
            }).reset_index()

            # Create a new GeoDataFrame
            combined_gdf = gpd.GeoDataFrame(combined, geometry="geometry", crs=polygons.crs)

            # Save the updated shapefile with the new attribute
            if remobilization == "N":
                combined_gdf.to_file(output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "-wood_volumes.shp", driver="ESRI shapefile")

                print(f"output file: {output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "-wood_volumes.shp"}")

            if remobilization == "Y":
                combined_gdf.to_file(output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "-remobilized_wood_volumes.shp", driver="ESRI shapefile")

                print(f"output file: {output_location + "/" + os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1] + "-remobilized_wood_volumes.shp"}")
        else:
            print(f"Something went wrong with experiment {os.path.split(after_path)[1].split("_")[0] + "_" + os.path.split(after_path)[1].split("_")[1]}. Skipping it for now")


if __name__ == "__main__":
    # Load the two TIFF files (before and after)
    before_path = "C:/Users/josie/local_data/20241118_SICK_scans/20240529_exp2_nowood.tif"
    after_path = "C:/Users/josie/local_data/20241118_SICK_scans/20240529_exp2_wood.tif"
    output_location = "C:/Users/josie/local_data/calculating_volume"

    cv = CalculateVolume()
    cv.detect_wood(before_path, after_path, output_location)