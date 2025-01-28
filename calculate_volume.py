#testing.py
import rasterio
import numpy as np
from rasterio.features import shapes
from shapely.geometry import shape, mapping
import fiona
import os
from fiona.crs import from_epsg



class CalculateVolume:
    
    def calculate_volume(self, before_path, after_path, output_location):
        
        # 1.Load rasters
        with rasterio.open(before_path) as before, rasterio.open(after_path) as after:
            before_data = before.read(1)
            after_data = after.read(1)
            profile = before.profile

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
        filtered_polygons = [poly for poly in polygons if poly.area >= 1000]

        # 7. Clip the difference layer using each remaining polygon
        results = []
        for poly in filtered_polygons:
            # Create a mask for the polygon
            poly_mask = rasterio.features.geometry_mask(
                [mapping(poly)],
                transform=profile["transform"],
                invert=True,
                out_shape=difference.shape
            )
            
            # Clip the difference layer
            clipped_data = np.where(poly_mask, difference, 0)
            
            # 8. Calculate the sum of all cells in the raster
            cell_sum = clipped_data.sum()
            
            # Store the sum as an attribute to the polygon
            results.append({"geometry": mapping(poly), "properties": {"sum": float(cell_sum)}})

        # 9. Export the polygons as a shapefile
        schema = {
            'geometry': 'Polygon',
            'properties': {'sum': 'float'},
        }

        out_fn = os.path.split(before_path)[1].split("_")[0] + "_" + os.path.split(before_path)[1].split("_")[1] + "_wood_polygons.shp"
        out_path = output_location + "/" + out_fn

        with fiona.open(out_path, "w", driver="ESRI Shapefile", crs=from_epsg(32615), schema=schema) as shp:
            for result in results:
                shp.write(result)

        print("Workflow complete. Polygons exported as output_shapefile.shp")


if __name__ == "__main__":
    #Load the two TIFF files (before and after)
    before_path = "C:/Users/josie/local_data/20241118_SICK_scans/20240529_exp2_nowood.tif"
    after_path = "C:/Users/josie/local_data/20241118_SICK_scans/20240529_exp2_wood.tif"
    output_location = "C:/Users/josie/local_data/calcualting volume"

    cv = CalculateVolume()
    cv.calculate_volume(before_path, after_path, output_location)