from calculate_volume import DetectChannelBottom
from functions import FileFunctions

dcb = DetectChannelBottom()
ff = FileFunctions()

nowood_tif_fn = ff.load_fn("choose a nowood tif file", [("tif files", "*.tif")])

print(nowood_tif_fn)

