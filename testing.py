import os
from pprint import pprint
from calculate_volume import CalculateVolume, DetectChannelBottom
from functions import FileFunctions

#instantiate classes
dcb = DetectChannelBottom()
cv = CalculateVolume()
ff = FileFunctions()

wood_poly_fn = ff.load_fn("Choose a wood polygons layer", [("Shapefiles", "*.shp")])
#channel_poly_fn = ff.load_fn("Choose a channel polygons layer", [("Shapefiles", "*.shp")])
out_dn = ff.load_dn("Choose output location")
out_fn = out_dn + "/centroids.shp"


split_wood = dcb.calculate_centroids(wood_poly_fn, out_fn)