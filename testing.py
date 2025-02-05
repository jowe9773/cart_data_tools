import cv2
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
from pprint import pprint
import matplotlib.pyplot as plt
import pandas as pd
from functions import FileFunctions

ff = FileFunctions()

def plot_array(array, title="Array Plot"):
    # Plot the data
    plt.figure(figsize=(10, 6))
    plt.imshow(array, cmap='gray')
    plt.colorbar(label='Pixel Value')
    plt.title(title)
    plt.xlabel("X-axis")
    plt.ylabel("Y-axis")
    plt.show()



"""choose input file"""
input_tif = ff.load_fn("Choose a tif file", [("tif files", "*.tif")])

"""detrend data"""
with rasterio.open(input_tif) as src:
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


""" Mask values below threshold and convert to polygons """
mask = np.where((detrended_data < -15), 1, 0).astype('uint8')
#plot_array(mask.astype(int), "Masked Data")

# Convert raster to polygons
polygons = []
for geom, value in shapes(mask.astype(np.uint8), transform=profile["transform"]):
    if value == 1: 
        polygons.append(shape(geom))

# Convert to GeoDataFrame
gdf_1 = gpd.GeoDataFrame(geometry=polygons, crs=profile["crs"])
gdf_1["DN"] = 1  # Assign DN = 1 to masked areas
print(gdf_1)

polygons = []
for geom, value in shapes(mask.astype(np.uint8), transform=profile["transform"]):
    if value == 0: 
        polygons.append(shape(geom))

# Convert to GeoDataFrame
gdf_0 = gpd.GeoDataFrame(geometry=polygons, crs=profile["crs"])
gdf_0["DN"] = 0  # Assign DN = 0 to unmasked areas
print(gdf_0)

# Combine both GeoDataFrames
polygons_gdf = gpd.GeoDataFrame(pd.concat([gdf_0, gdf_1], ignore_index=True))

print(polygons_gdf)

#calculate area of each row
polygons_gdf["area"] = polygons_gdf.geometry.area

"""remove holes in the channel (falsely detected floodplain)"""
polygons_gdf.loc[(polygons_gdf["DN"] == 0) & (polygons_gdf["area"] < 10000), "DN"] = 1

dn_count1 = (polygons_gdf["DN"] == 1).sum()
dn_count0 = (polygons_gdf["DN"] == 0).sum()

print(f"there are {dn_count1} polygons with a dn of 1 and {dn_count0} polygons with a dn count of 0")

gdf_dissolved1 = polygons_gdf.dissolve(by="DN", as_index=False)
print(gdf_dissolved1)


gdf_exploded1 = gdf_dissolved1.explode(index_parts=False, as_index = False).reset_index(drop=True)
print(gdf_exploded1)

#recalculate the area of each polygon
gdf_exploded1["area"] = gdf_exploded1.geometry.area

print("Exploded1")
print(gdf_exploded1)

"""remove holes from floodplain (falsely identified as channel)"""
gdf_exploded1.loc[(gdf_exploded1["DN"] == 1) & (gdf_exploded1["area"] < 10000), "DN"] = 0

gdf_dissolved2 = gdf_exploded1.dissolve(by="DN", as_index=False)
print(gdf_dissolved2)

gdf_exploded2 = gdf_dissolved2.explode(index_parts=False, as_index = False).reset_index(drop=True)
print(gdf_exploded2)

#recalculate the area of each polygon
gdf_exploded2["area"] = gdf_exploded2.geometry.area

# Save final polygons to Shapefile
gdf_exploded2.to_file("dissolvedandexploded_shapefile.shp", driver="ESRI Shapefile")
print(f"Final dissolved layer saved")

